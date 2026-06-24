"""
Plan-Checker — prüft EINEN fertigen Plan (model_dump()-Dict) gegen fachliche Regeln.

Deterministisch, ohne Claude/DB. Erweiterbares Gerüst: jede Regel ist ein Prüfer
`_regelN_*(plan, EXMAP) -> list[Verstoss]`, registriert in REGELN. Ein Verstoß ist
eine lesbare, lokalisierte Meldung (welche Regel, welcher Plan, welche Übung, warum).

Stand (MVP-11, erste Naht): NUR Regel 6 (Verletzungs-Sicherheit). Regeln 1-5 folgen
je als eigene Naht — einfach einen weiteren Prüfer in REGELN ergänzen.

  python3 scripts/plan_checker.py     # läuft über die 12 Profil-Cases, Exit 0/1
"""

from __future__ import annotations

import json
import pathlib
import sys
from dataclasses import dataclass

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

# Single source of truth: Map + Gating aus dem Filter IMPORTIEREN, nicht duplizieren.
# Regel 6 ist die exakte Negation von equipment_filter Stufe 1/2 — bleibt so bei
# Filter-Änderungen automatisch konsistent.
from logic.equipment_filter import _VERLETZUNG_MAP, _HIGH_IMPACT_GATED

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

def _regel6_verletzung(plan: dict, EXMAP: dict[str, dict]) -> list[Verstoss]:
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


# ── Regel-Registry (erweiterbar: Regeln 1-5 hier ergänzen) ────────────────────────

REGELN = [
    _regel6_verletzung,
]


def pruefe_plan(plan: dict, profil_label: str = "", EXMAP: dict[str, dict] | None = None) -> list[Verstoss]:
    """Prüft EINEN Plan gegen alle registrierten Regeln; sammelt alle Verstöße."""
    EXMAP = EXMAP if EXMAP is not None else lade_exmap()
    verstoesse: list[Verstoss] = []
    for regel in REGELN:
        verstoesse.extend(regel(plan, EXMAP))
    return verstoesse


# ── Runner: über die 12 Profil-Cases ──────────────────────────────────────────────

def _baue_plan(case: dict) -> dict:
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
    return plan.model_dump()


def main() -> int:
    from scripts.run_test_matrix import CASES

    EXMAP = lade_exmap()
    print("=" * 70)
    print("PLAN-CHECKER — Regel 6 (Verletzungs-Sicherheit) über 12 Profile")
    print("=" * 70)

    sauber = 0
    for c in CASES:
        label = f"{c['nr']}_{c['kurzname']}"
        plan = _baue_plan(c)
        verstoesse = pruefe_plan(plan, label, EXMAP)
        if not verstoesse:
            print(f"  ✅ {label}")
            sauber += 1
        else:
            print(f"  ❌ {label} — {len(verstoesse)} Verstoß/Verstöße:")
            for v in verstoesse:
                print(f"       {v.detail}")

    print()
    print(f"  {sauber}/{len(CASES)} Pläne regelkonform (Regel 6)")
    return 0 if sauber == len(CASES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
