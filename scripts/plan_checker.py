"""
Plan-Checker — prüft EINEN fertigen Plan (model_dump()-Dict) gegen fachliche Regeln.

Deterministisch, ohne Claude/DB. Erweiterbares Gerüst: jede Regel ist ein Prüfer
`_regelN_*(plan, EXMAP) -> list[Verstoss]`, registriert in REGELN. Ein Verstoß ist
eine lesbare, lokalisierte Meldung (welche Regel, welcher Plan, welche Übung, warum).

Stand (MVP-11, erste Naht): NUR Regel 6 (Verletzungs-Sicherheit). Regeln 1-5 folgen
je als eigene Naht — einfach einen weiteren Prüfer in REGELN ergänzen.

  python3 scripts/plan_checker.py                 # 12 Profil-Cases (Stub), Exit 0/1
  python3 scripts/plan_checker.py --kreuzprodukt  # ganzer Eingaberaum (Stub)
  python3 scripts/plan_checker.py --run-dir DIR   # externe Plan-JSONs (echter Claude-Output)
"""

from __future__ import annotations

import json
import pathlib
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from itertools import product

# Schwere-Kategorie für ERZWUNGENE Repeats (pool_size < demand): kein Plan-Defekt, sondern
# Bibliotheks-Bedarfssignal (β). Greppbar + von der regelkonform-Zählung ausgenommen.
_SCHWERE_BETA = "β-Pool-Lücke"

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

# Single source of truth: Map + Gating aus dem Filter IMPORTIEREN, nicht duplizieren.
# Regel 6 ist die exakte Negation von equipment_filter Stufe 1/2 — bleibt so bei
# Filter-Änderungen automatisch konsistent.
from logic.equipment_filter import _VERLETZUNG_MAP, _HIGH_IMPACT_GATED, _FALLBACK_PATTERN, verletzungs_rpe_cap

_EXERCISES_PATH = pathlib.Path(__file__).parent.parent / "data" / "exercises.json"


def lade_exmap() -> dict[str, dict]:
    """{exercise_id: eintrag} aus data/exercises.json. unit immer via .get(…, 'reps')."""
    exercises = json.loads(_EXERCISES_PATH.read_text(encoding="utf-8"))["exercises"]
    return {e["id"]: e for e in exercises}


@dataclass
class Verstoss:
    regel: str          # z.B. "Regel 6 — Verletzungs-Sicherheit"
    schwere: str        # "fehler"
    plan_kontext: str   # Profil/Ziel/Level
    detail: str         # welche Übung, welches Gelenk, welcher Grund

    def __str__(self) -> str:
        return f"[{self.schwere}] {self.regel} · {self.plan_kontext} · {self.detail}"


# ── Helfer: alle exercise_ids eines Plans (Kraft + Metcon + Conditioning-Block 2) ──

def _alle_uebungen(plan: dict):
    """Yield (exercise_id, name, herkunft) über alle Wochen/Sessions/Blöcke."""
    for w in plan.get("wochen", []):
        wn = w.get("woche_nummer", "?")
        for s in w.get("sessions", []):
            herkunft = f"W{wn}/{s.get('session_id', '?')}"
            for u in s.get("haupt_uebungen", []):
                yield u.get("exercise_id"), u.get("name", "?"), herkunft
            for feld in ("metcon_block", "conditioning_block_2"):
                blk = s.get(feld)
                if blk:
                    for u in blk.get("uebungen", []):
                        yield u.get("exercise_id"), u.get("name", "?"), f"{herkunft}/{feld}"


def _plan_kontext(plan: dict) -> str:
    snap = plan.get("klient_snapshot", {})
    verl = [getattr(v, "value", v) for v in snap.get("verletzungen", [])]
    return (f"{snap.get('equipment', '?')}/L{snap.get('level', '?')}/{snap.get('ziel', '?')}"
            f" · Verletzungen: {', '.join(verl) if verl else 'keine'}")


# ── Regel 6: Verletzungs-Sicherheit (Negation des Filters) ────────────────────────

def _regel6_verletzung(plan: dict, EXMAP: dict[str, dict], soll: dict | None = None) -> list[Verstoss]:
    REGEL = "Regel 6 — Verletzungs-Sicherheit"
    kontext = _plan_kontext(plan)
    snap = plan.get("klient_snapshot", {})
    verl_keys = {
        _VERLETZUNG_MAP[getattr(v, "value", v)]
        for v in snap.get("verletzungen", [])
        if getattr(v, "value", v) in _VERLETZUNG_MAP
    }

    verstoesse: list[Verstoss] = []
    seen: set[str] = set()
    for ex_id, name, herkunft in _alle_uebungen(plan):
        if ex_id in seen:
            continue
        seen.add(ex_id)

        ex = EXMAP.get(ex_id)
        if ex is None:
            verstoesse.append(Verstoss(
                REGEL, "fehler", kontext,
                f"unbekannte exercise_id '{ex_id}' ({name}, {herkunft}) — nicht in exercises.json",
            ))
            continue

        if not verl_keys:
            continue

        # Stufe 1: joint_stress ∩ Verletzung
        treffer = verl_keys & set(ex.get("joint_stress", []))
        if treffer:
            verstoesse.append(Verstoss(
                REGEL, "fehler", kontext,
                f"'{name}' ({ex_id}, {herkunft}) lädt verletzte Region(en) {sorted(treffer)} "
                f"(joint_stress={ex.get('joint_stress', [])})",
            ))

        # Stufe 2: High-Impact bei Bein-/Achs-/Hals-Verletzung
        if ex.get("impact_level") == "high" and (verl_keys & _HIGH_IMPACT_GATED):
            verstoesse.append(Verstoss(
                REGEL, "fehler", kontext,
                f"'{name}' ({ex_id}, {herkunft}) ist impact_level=high bei "
                f"Bein-/Achs-/Hals-Verletzung {sorted(verl_keys & _HIGH_IMPACT_GATED)}",
            ))

    return verstoesse


# ── Regel 2: Slot-Pattern-Treue (γ — eingesetztes pattern == Slot-pattern) ─────────

def _slot_key(session_id: str) -> str:
    """Wochenübergreifender Schlüssel: 'w3_s2' → 's2' (Split nutzt 'w1_sN', Plan 'w{N}_sN')."""
    return session_id.split("_", 1)[1] if "_" in session_id else session_id


def _regel2_slot_pattern(plan: dict, EXMAP: dict[str, dict], soll: dict | None = None) -> list[Verstoss]:
    REGEL = "Regel 2 — Slot-Pattern-Treue"
    patterns_soll = (soll or {}).get("patterns")
    if not patterns_soll:   # ohne Soll (z.B. Direktaufruf ohne Split) nicht prüfbar → still überspringen
        return []
    kontext = _plan_kontext(plan)
    verstoesse: list[Verstoss] = []

    for w in plan.get("wochen", []):
        wn = w.get("woche_nummer", "?")
        for s in w.get("sessions", []):
            if s.get("session_typ") != "kraft":
                continue   # Conditioning/Athletik/Zone-2: keine festen Kraft-Slots → skip
            patterns = patterns_soll.get(_slot_key(s.get("session_id", "")))
            if not patterns:
                continue
            for u in s.get("haupt_uebungen", []):
                idx = u.get("reihenfolge", 0) - 1
                if idx < 0 or idx >= len(patterns):
                    continue   # Ausrichtungs-Sicherheit (sollte nicht auftreten)
                soll = patterns[idx]
                ex = EXMAP.get(u.get("exercise_id"))
                if ex is None:
                    continue   # unbekannte ID → Regel 6
                ist = ex.get("pattern")
                if ist == soll or ist == _FALLBACK_PATTERN.get(soll):
                    continue
                verstoesse.append(Verstoss(
                    REGEL, "fehler", kontext,
                    f"'{u.get('name', '?')}' ({u.get('exercise_id')}, W{wn}/{s.get('session_id')} "
                    f"#{u.get('reihenfolge')}): pattern '{ist}' ≠ Slot-Soll '{soll}' "
                    f"(auch kein Fallback {_FALLBACK_PATTERN.get(soll, '–')})",
                ))
    return verstoesse


# ── Regel 5: Einheit-Konsistenz (rir-Gate global + wdh-Format kraft-scoped) ────────

def _regel5_einheit(plan: dict, EXMAP: dict[str, dict], soll: dict | None = None) -> list[Verstoss]:
    REGEL_A = "Regel 5 — Einheit (RIR-Gate)"
    REGEL_B = "Regel 5 — Einheit (wdh-Format)"
    kontext = _plan_kontext(plan)
    verstoesse: list[Verstoss] = []

    for w in plan.get("wochen", []):
        wn = w.get("woche_nummer", "?")
        for s in w.get("sessions", []):
            sid = s.get("session_id", "?")
            is_kraft = s.get("session_typ") == "kraft"
            # (src, uebungen, wdh-prüfen?) — Teil B nur Kraft-haupt_uebungen; Blöcke nie wdh-geprüft.
            gruppen = [("haupt", s.get("haupt_uebungen", []), is_kraft)]
            for f in ("metcon_block", "conditioning_block_2"):
                blk = s.get(f)
                if blk:
                    gruppen.append((f, blk.get("uebungen", []), False))

            for src, lst, wdh_pruefen in gruppen:
                for u in lst:
                    ex = EXMAP.get(u.get("exercise_id"))
                    if ex is None:
                        continue   # unbekannte ID → Regel 6
                    unit = ex.get("unit", "reps")

                    # TEIL A — rir-Gate (GLOBAL): RIR nur bei unit=reps
                    if u.get("rir") is not None and unit != "reps":
                        verstoesse.append(Verstoss(
                            REGEL_A, "fehler", kontext,
                            f"'{u.get('name', '?')}' ({u.get('exercise_id')}, W{wn}/{sid}/{src}): "
                            f"rir={u.get('rir')} bei unit='{unit}' — RIR nur bei unit=reps zulässig",
                        ))

                    # TEIL B — Einheit-Treue (NUR Kraft-haupt_uebungen; Conditioning-Format-Override legitim).
                    # Strukturiertes einheit-Feld (Blocker 2a) statt wdh-String-Parsing → robuster.
                    if wdh_pruefen:
                        erwartet = {"reps": "wiederholungen", "zeit": "sekunden", "distanz": "meter"}.get(unit)
                        einheit = u.get("einheit")
                        if erwartet and einheit != erwartet:
                            verstoesse.append(Verstoss(
                                REGEL_B, "fehler", kontext,
                                f"'{u.get('name', '?')}' ({u.get('exercise_id')}, W{wn}/{sid} "
                                f"#{u.get('reihenfolge')}): unit='{unit}' erwartet einheit='{erwartet}', hat '{einheit}'",
                            ))
    return verstoesse


# ── Regel 4: RIR-Welle (Soll via berechne_volumen-Orakel, kein Hardcode) ──────────

def _regel4_rir(plan: dict, EXMAP: dict[str, dict], soll: dict | None = None) -> list[Verstoss]:
    REGEL = "Regel 4 — RIR-Welle"
    tiers_soll = (soll or {}).get("tiers")
    rir_soll = (soll or {}).get("rir")
    if not tiers_soll or not rir_soll:
        return []
    kontext = _plan_kontext(plan)
    verstoesse: list[Verstoss] = []
    # Single Source: derselbe Verletzungs-Deckel wie der Assembler — Soll-RIR ebenso deckeln,
    # sonst flaggt Regel 4 die (gewollte) Safety-Absenkung als Abweichung (PRIO 2).
    verletzungen = plan.get("klient_snapshot", {}).get("verletzungen", [])

    for w in plan.get("wochen", []):
        wn = w.get("woche_nummer", "?")
        block = w.get("block_typ")
        soll_block = rir_soll.get(block, {})

        # Session-Sanity: Wochen-ziel_rir == compound-RIR der Welle
        comp = soll_block.get("compound")
        if comp is not None and w.get("ziel_rir") != comp:
            verstoesse.append(Verstoss(
                REGEL, "fehler", kontext,
                f"W{wn}/{block}: ziel_rir={w.get('ziel_rir')} ≠ compound-Soll {comp}",
            ))

        for s in w.get("sessions", []):
            if s.get("session_typ") != "kraft":
                continue
            session_tiers = tiers_soll.get(_slot_key(s.get("session_id", "")))
            if not session_tiers:
                continue
            for u in s.get("haupt_uebungen", []):
                if u.get("rir") is None:
                    continue   # Nicht-reps → Einheit-Gate (Regel 5)
                idx = u.get("reihenfolge", 0) - 1
                if idx < 0 or idx >= len(session_tiers):
                    continue
                tier = session_tiers[idx]
                erwartet = soll_block.get(tier)
                if erwartet is None:
                    continue
                # Verletzungs-Deckel auf die Soll-Erwartung (pattern der eingesetzten Übung):
                # RIR→RPE→cap→RIR, gleicher Helper + Transform wie der Assembler.
                pattern = EXMAP.get(u.get("exercise_id"), {}).get("pattern")
                erwartet_rpe = verletzungs_rpe_cap(verletzungen, pattern, 10 - erwartet)
                erwartet = round((10 - erwartet_rpe) * 2) / 2
                if u["rir"] != erwartet:
                    verstoesse.append(Verstoss(
                        REGEL, "fehler", kontext,
                        f"'{u.get('name', '?')}' ({u.get('exercise_id')}, W{wn}/{s.get('session_id')} "
                        f"#{u.get('reihenfolge')}, tier={tier}, {block}): rir={u['rir']} ≠ erwartet {erwartet}",
                    ))
    return verstoesse


# ── Regel 3: Keine Primär-Dedup (δ — gleicher compound-Lift nicht 2×/Woche) ────────

@lru_cache(maxsize=None)
def _pool_groessen(equipment: str, level: int, verletzungen: tuple) -> dict[str, int]:
    """{pattern: Anzahl distinkter Übungen} für (equipment, level, verletzungen) — gecacht
    (Sweep ruft das 1536×; ohne Cache je Aufruf ein exercises.json-Read). klient-Rekonstruktion
    aus den Snapshot-Feldern wie pruefe_externen_plan (Pool ist verletzungs-eng, da filtere_uebungen
    Verletzungen mitfiltert). Post-Fallback-Zahl = was der Picker real zur Verfügung hat."""
    from models import KlientenInput
    from logic.equipment_filter import filtere_uebungen
    klient = KlientenInput(
        client_id="pool", vorname="pool", alter=30, trainingsjahre="ein_bis_zwei",
        kniebeugen_wdh=0, pushups_wdh=0, situps_wdh=0, burpees_wdh=0, plank_sek=0,
        stress_level=4, schlaf_stunden=7.0,
        hauptziel="muskelaufbau", equipment=equipment,
        tage_pro_woche=4, session_dauer_min=60, verletzungen=list(verletzungen),
    )
    return {pat: len(uebs) for pat, uebs in filtere_uebungen(klient, level).items()}


def _compound_demand(soll: dict) -> dict[str, int]:
    """Compound-Slots pro Pattern über alle Sessions der Woche (plan-spezifisch aus soll —
    6T-hinge=3, 4T=2 …). Denominator des pool-aware-Tests (passt zur compound-only-Dedup)."""
    demand: Counter = Counter()
    patterns = soll.get("patterns") or {}
    tiers = soll.get("tiers") or {}
    for sk, pats in patterns.items():
        for pat, ti in zip(pats, tiers.get(sk, [])):
            if ti == "compound":
                demand[pat] += 1
    return demand


def _regel3_dedup(plan: dict, EXMAP: dict[str, dict], soll: dict | None = None) -> list[Verstoss]:
    REGEL = "Regel 3 — Keine Primär-Dedup"
    tiers_soll = (soll or {}).get("tiers")
    if not tiers_soll:
        return []
    kontext = _plan_kontext(plan)
    verstoesse: list[Verstoss] = []

    # Pool-aware-Kontext (PRIO 6) — einmal pro Plan: demand aus soll, pool aus dem Snapshot.
    demand = _compound_demand(soll)
    snap = plan.get("klient_snapshot", {})
    equip = getattr(snap.get("equipment"), "value", snap.get("equipment"))
    level = snap.get("level")
    verl_tuple = tuple(sorted(getattr(v, "value", v) for v in snap.get("verletzungen", [])))
    pool = _pool_groessen(equip, level, verl_tuple) if equip and level else {}

    for w in plan.get("wochen", []):
        wn = w.get("woche_nummer", "?")
        primaer: list[tuple] = []   # (exercise_id, name, session_id, reihenfolge)
        for s in w.get("sessions", []):
            if s.get("session_typ") != "kraft":
                continue   # nur Kraft trägt compound-Primär
            st = tiers_soll.get(_slot_key(s.get("session_id", "")))
            if not st:
                continue
            for u in s.get("haupt_uebungen", []):
                idx = u.get("reihenfolge", 0) - 1
                if 0 <= idx < len(st) and st[idx] == "compound":
                    primaer.append((u.get("exercise_id"), u.get("name", "?"),
                                    s.get("session_id"), u.get("reihenfolge")))

        for ex_id, n in Counter(p[0] for p in primaer).items():
            if n < 2:
                continue
            vork = [f"W{wn}/{sid}#{r}" for (eid, _nm, sid, r) in primaer if eid == ex_id]
            name = next((nm for (eid, nm, _s, _r) in primaer if eid == ex_id), "?")
            pat = EXMAP.get(ex_id, {}).get("pattern")
            d = demand.get(pat, 0)
            p_size = pool.get(pat, 0)
            if pool and p_size < d:
                # ERZWUNGEN: zu wenige distinkte Übungen für die compound-Slots → β-Lücke, kein Defekt.
                verstoesse.append(Verstoss(
                    REGEL, _SCHWERE_BETA, kontext,
                    f"'{name}' ({ex_id}) {n}× in Woche {wn}: {vork} — erzwungen "
                    f"(Pool {p_size} < {d} compound-Slots, β-Lücke {equip}/L{level}/{pat})",
                ))
            else:
                verstoesse.append(Verstoss(
                    REGEL, "fehler", kontext,
                    f"'{name}' ({ex_id}) {n}× als Primär in Woche {wn}: {vork} — "
                    f"vermeidbar (Pool {p_size} ≥ {d} {pat}), Variation möglich gewesen",
                ))
    return verstoesse


# ── Regel-Registry ─────────────────────────────────────────────────────────────

REGELN = [
    _regel6_verletzung,
    _regel2_slot_pattern,
    _regel5_einheit,
    _regel4_rir,
    _regel3_dedup,
]


def pruefe_plan(plan: dict, profil_label: str = "", EXMAP: dict[str, dict] | None = None,
                soll: dict | None = None) -> list[Verstoss]:
    """Prüft EINEN Plan gegen alle registrierten Regeln; sammelt alle Verstöße.
    soll = Werkzeugkiste aus dem Split/Orakel:
      {"patterns": {slot_key:[pattern]}, "tiers": {slot_key:[tier]},
       "rir": {woche_typ:{tier:rir}}} — von Regel 2 (patterns) / Regel 4 (tiers+rir) genutzt."""
    EXMAP = EXMAP if EXMAP is not None else lade_exmap()
    verstoesse: list[Verstoss] = []
    for regel in REGELN:
        verstoesse.extend(regel(plan, EXMAP, soll))
    return verstoesse


# ── Runner: über die 12 Profil-Cases ──────────────────────────────────────────────

# PST + trainingsjahre, sodass berechne_level EXAKT das Ziel-Level liefert (Cap ≥ level).
# Anker equipment-unabhängig; raw-Band 5-8/9-13/14-17/18-20 → L1-L4.
_PST_FUER_LEVEL = {
    1: dict(kniebeugen=10, pushups=5,  situps=10, burpees=5,  plank_sek=30,  trainingsjahre="keine"),
    2: dict(kniebeugen=40, pushups=20, situps=40, burpees=20, plank_sek=90,  trainingsjahre="ein_bis_zwei"),
    3: dict(kniebeugen=60, pushups=40, situps=60, burpees=30, plank_sek=150, trainingsjahre="drei_bis_fuenf"),
    4: dict(kniebeugen=80, pushups=60, situps=75, burpees=40, plank_sek=200, trainingsjahre="fuenf_plus"),
}


def pst_fuer_level(level: int) -> dict:
    return dict(_PST_FUER_LEVEL[level])


def _make_case(ziel: str, equipment: str, tage: int, dauer: int, level: int, verletzungen: list[str]) -> dict:
    """Achsen-Kombination → vollständiges case-Dict für baue_payload (PST aus pst_fuer_level)."""
    c = pst_fuer_level(level)
    c.update(vorname="sweep", alter=30, hauptziel=ziel, equipment=equipment,
             tage_pro_woche=tage, session_dauer_min=dauer, verletzungen=verletzungen)
    return c


def _baue_soll(split: dict, klient, level: int) -> dict:
    """Werkzeugkiste fürs Prüfen — aus demselben deterministischen Split + dem RIR-Orakel:
      patterns/tiers pro Session-Slot · rir pro woche_typ×tier via berechne_volumen (kein Hardcode)."""
    from logic.volume_calculator import berechne_volumen

    patterns = {_slot_key(s["session_id"]): [sl["pattern"] for sl in s.get("slots", [])] for s in split["sessions"]}
    tiers    = {_slot_key(s["session_id"]): [sl["tier"]    for sl in s.get("slots", [])] for s in split["sessions"]}

    def _rir(rpe: float) -> float:
        return round((10 - rpe) * 2) / 2   # gleiche Transform wie im Assembler

    rir = {}
    for wt in ("akkumulation", "progression", "intensivierung", "deload"):
        v = berechne_volumen(klient, level, wt)
        rir[wt] = {
            "compound":  _rir(v["compound_rpe"]),
            "accessory": _rir(v["accessory_rpe"]),
            "isolation": _rir(v["isolation_rpe"]),
            "core":      _rir(v["ziel_rpe"]),   # kein core_rpe-Key → ziel_rpe
        }
    return {"patterns": patterns, "tiers": tiers, "rir": rir}


def _baue_plan(case: dict) -> tuple[dict, dict]:
    """Plan-Dict + Soll-Werkzeugkiste (aus demselben deterministischen Split + Orakel)."""
    from scripts.run_test_matrix import baue_payload
    from scripts.generate_test_plans import _auto_claude_output
    from parsers import parse_typeform_payload
    from logic.level_calculator import berechne_level
    from logic.split_selector import waehle_split
    from logic.equipment_filter import filtere_uebungen
    from logic.plan_assembler import assemble_plan

    klient = parse_typeform_payload(baue_payload(case))
    level, _ = berechne_level(klient)
    split = waehle_split(klient, level)
    uebungen = filtere_uebungen(klient, level)
    plan = assemble_plan(klient=klient, level=level, split=split,
                         claude_output=_auto_claude_output(split, uebungen), block_nummer=1)
    return plan.model_dump(), _baue_soll(split, klient, level)


def pruefe_externen_plan(plan_json_path, EXMAP: dict[str, dict] | None = None) -> list[Verstoss]:
    """Prüft eine EXTERNE Plan-JSON (echter Claude-Output aus test_runs/) gegen Regel 2-6.

    `soll` wird aus dem self-contained `klient_snapshot` des Plans rekonstruiert — kein Case nötig:
    der Snapshot trägt level/ziel/equipment/tage/dauer/verletzungen, exakt die waehle_split- +
    berechne_volumen-Eingaben. Das ist `_baue_plan` MINUS dem Stub-Schritt: der Plan kommt von
    Platte statt aus `_auto_claude_output`; `soll` entsteht deterministisch aus demselben Split.
    PST/trainingsjahre/alter sind Dummies — `level` ist gegeben, wird NICHT via berechne_level neu gerechnet."""
    from models import KlientenInput
    from logic.split_selector import waehle_split

    plan = json.loads(pathlib.Path(plan_json_path).read_text(encoding="utf-8"))
    snap = plan["klient_snapshot"]
    level = snap["level"]
    klient = KlientenInput(
        client_id="ext", vorname="ext", alter=30, trainingsjahre="ein_bis_zwei",
        kniebeugen_wdh=0, pushups_wdh=0, situps_wdh=0, burpees_wdh=0, plank_sek=0,  # PST irrelevant: level fix
        stress_level=4, schlaf_stunden=7.0,   # Defaults: nicht mehr im Snapshot (Blocker 4), für die Prüfung irrelevant
        hauptziel=snap["ziel"], equipment=snap["equipment"],
        tage_pro_woche=snap["tage_pro_woche"], session_dauer_min=snap["session_dauer_min"],
        verletzungen=snap["verletzungen"],
    )
    split = waehle_split(klient, level)
    soll = _baue_soll(split, klient, level)
    return pruefe_plan(plan, EXMAP=EXMAP if EXMAP is not None else lade_exmap(), soll=soll)


def main() -> int:
    from scripts.run_test_matrix import CASES

    EXMAP = lade_exmap()
    print("=" * 70)
    print("PLAN-CHECKER — Regel 6+2+5+4+3 über 12 Profile")
    print("=" * 70)

    sauber = 0
    for c in CASES:
        label = f"{c['nr']}_{c['kurzname']}"
        plan, soll = _baue_plan(c)
        verstoesse = pruefe_plan(plan, label, EXMAP, soll)
        fehler = [v for v in verstoesse if v.schwere != _SCHWERE_BETA]
        beta = [v for v in verstoesse if v.schwere == _SCHWERE_BETA]
        if not fehler:
            print(f"  ✅ {label}" + (f"  ({len(beta)} β-Pool-Lücke)" if beta else ""))
            sauber += 1
        else:
            print(f"  ❌ {label} — {len(fehler)} Verstoß/Verstöße:")
            for v in fehler:
                print(f"       {v.detail}")
        for v in beta:
            print(f"       [β] {v.detail}")

    print()
    print(f"  {sauber}/{len(CASES)} Pläne regelkonform (Regel 6+2+5+4+3; β-Pool-Lücken kein Defekt)")
    return 0 if sauber == len(CASES) else 1


# ── Kreuzprodukt-Sprung: alle Regeln über den ganzen Eingaberaum ──────────────────

_ZIELE = ["muskelaufbau", "fettabbau", "recomp", "longevity"]
_EQUIP = ["gym", "home_gym", "kettlebell", "bodyweight", "travel", "hybrid"]
_TAGE = [3, 4, 5, 6]
_DAUER = [20, 30, 45, 60]
_LEVELS = [1, 2, 3, 4]
_VERLETZUNGEN = [
    ["knie"], ["schulter"], ["wirbelsäule"], ["hüfte"], ["ellenbogen"],
    ["handgelenk"], ["hals"], ["knöchel"], ["wirbelsäule", "knie"],
]


def main_kreuzprodukt() -> int:
    EXMAP = lade_exmap()
    print("=" * 70)
    print("PLAN-CHECKER — KREUZPRODUKT-SPRUNG")
    print("=" * 70)

    # ── Struktur-Sweep: Ziel × Equip × Tage × Dauer × Level (ohne Verletzung), alle 5 Regeln ──
    verst = defaultdict(list)
    beta_funde = defaultdict(list)   # β-Pool-Lücken: kein Defekt, separat ausgewiesen
    mism = []
    total = sauber = 0
    for ziel, eq, tg, da, lv in product(_ZIELE, _EQUIP, _TAGE, _DAUER, _LEVELS):
        total += 1
        kombi = f"{ziel}/{eq}/{tg}T/{da}min/L{lv}"
        plan, soll = _baue_plan(_make_case(ziel, eq, tg, da, lv, []))
        erreicht = plan["klient_snapshot"]["level"]
        if erreicht != lv:
            mism.append(f"{kombi}: erreicht L{erreicht} (Generator-Bug)")
            continue
        vs = pruefe_plan(plan, kombi, EXMAP, soll)
        fehler = [v for v in vs if v.schwere != _SCHWERE_BETA]
        for v in vs:
            (beta_funde if v.schwere == _SCHWERE_BETA else verst)[v.regel].append(f"{kombi} · {v.detail}")
        if not fehler:
            sauber += 1
    n_verst = sum(len(x) for x in verst.values())
    n_beta = sum(len(x) for x in beta_funde.values())
    print(f"\nStruktur-Sweep: {sauber}/{total} regelkonform, {n_verst} Verstöße, "
          f"{n_beta} β-Pool-Lücken (kein Defekt), {len(mism)} Level-Mismatches")

    # ── Verletzungs-Sweep: nur Regel 6, repräsentative Achsen (ziel/dauer/tage fix) ──
    iv_verst = []
    iv_mism = []
    iv_total = iv_sauber = 0
    for verl in _VERLETZUNGEN:
        for eq in _EQUIP:
            for lv in _LEVELS:
                iv_total += 1
                kombi = f"muskelaufbau/{eq}/4T/60min/L{lv}/{'+'.join(verl)}"
                plan, soll = _baue_plan(_make_case("muskelaufbau", eq, 4, 60, lv, verl))
                if plan["klient_snapshot"]["level"] != lv:
                    iv_mism.append(f"{kombi}: erreicht L{plan['klient_snapshot']['level']}")
                    continue
                vs = _regel6_verletzung(plan, EXMAP, soll)
                if vs:
                    iv_verst += [f"{kombi} · {v.detail}" for v in vs]
                else:
                    iv_sauber += 1
    print(f"Verletzungs-Sweep (Regel 6): {iv_sauber}/{iv_total} regelkonform, {len(iv_verst)} Verstöße, {len(iv_mism)} Level-Mismatches")

    # ── Detail nur bei Funden ──
    if mism or iv_mism:
        print("\n--- LEVEL-MISMATCHES (Generator, kein Regel-Fund) ---")
        for m in mism + iv_mism:
            print(f"  {m}")
    if n_verst:
        print("\n--- VERSTÖSSE (Struktur-Sweep), gruppiert nach Regel ---")
        for regel in sorted(verst):
            print(f"  [{regel}] {len(verst[regel])}:")
            for d in verst[regel][:25]:
                print(f"     {d}")
            if len(verst[regel]) > 25:
                print(f"     … (+{len(verst[regel]) - 25} weitere)")
    if iv_verst:
        print("\n--- VERSTÖSSE (Verletzungs-Sweep, Regel 6) ---")
        for d in iv_verst[:50]:
            print(f"  {d}")
        if len(iv_verst) > 50:
            print(f"  … (+{len(iv_verst) - 50} weitere)")
    if n_beta:
        print("\n--- β-POOL-LÜCKEN (Struktur-Sweep, kein Defekt — Bibliotheks-Bedarfssignal) ---")
        for regel in sorted(beta_funde):
            print(f"  [{regel}] {len(beta_funde[regel])}:")
            for d in beta_funde[regel][:25]:
                print(f"     {d}")
            if len(beta_funde[regel]) > 25:
                print(f"     … (+{len(beta_funde[regel]) - 25} weitere)")

    # β-Pool-Lücken sind KEIN Defekt → blocken GRÜN nicht.
    ok = (n_verst == 0 and not mism and len(iv_verst) == 0 and not iv_mism)
    status = "ALLES GRÜN" if ok else "FUNDE — siehe oben"
    if ok and n_beta:
        status += f" (+ {n_beta} β-Pool-Lücken, kein Defekt)"
    print(f"\n{status}")
    return 0 if ok else 1


# ── Externe Pläne: echten Claude-Output (test_runs/) gegen Regel 2-6 prüfen ───────

def main_run_dir(ordner: str) -> int:
    EXMAP = lade_exmap()
    d = pathlib.Path(ordner)
    print("=" * 70)
    print(f"PLAN-CHECKER — EXTERNE PLÄNE aus {d}")
    print("=" * 70)

    dateien = sorted(d.glob("*.json"))
    if not dateien:
        print(f"Keine *.json in {d} gefunden.")
        return 1

    sauber = 0
    for f in dateien:
        verstoesse = pruefe_externen_plan(f, EXMAP)
        fehler = [v for v in verstoesse if v.schwere != _SCHWERE_BETA]
        beta = [v for v in verstoesse if v.schwere == _SCHWERE_BETA]
        if not fehler:
            print(f"  ✅ {f.name}" + (f"  ({len(beta)} β-Pool-Lücke)" if beta else ""))
            sauber += 1
        else:
            nach_regel: dict[str, list[str]] = defaultdict(list)
            for v in fehler:
                nach_regel[v.regel].append(v.detail)
            print(f"  ❌ {f.name} — {len(fehler)} Verstoß/Verstöße:")
            for regel in sorted(nach_regel):
                print(f"       [{regel}] {len(nach_regel[regel])}:")
                for det in nach_regel[regel]:
                    print(f"          {det}")
        for v in beta:
            print(f"       [β] {v.detail}")

    print()
    print(f"  {sauber}/{len(dateien)} Pläne regelkonform (Regel 6+2+5+4+3)")
    return 0 if sauber == len(dateien) else 1


if __name__ == "__main__":
    if "--kreuzprodukt" in sys.argv:
        raise SystemExit(main_kreuzprodukt())
    if "--run-dir" in sys.argv:
        i = sys.argv.index("--run-dir")
        if i + 1 >= len(sys.argv):
            print("Usage: python3 scripts/plan_checker.py --run-dir <ordner>")
            raise SystemExit(2)
        raise SystemExit(main_run_dir(sys.argv[i + 1]))
    raise SystemExit(main())
