"""
Automatische Tests aller kritischen Pipeline-Pfade.

Testet Schritt 1–5 (Parse → Level → Volumen → Split → Filter) für alle Kombinationen.
Mit --claude testet es zusätzlich den Claude-Aufruf + Plan-Assembler für eine Auswahl.

Verwendung:
  python3 scripts/run_tests.py              # Logik-Tests (schnell, kein API-Key nötig)
  python3 scripts/run_tests.py --claude     # Inkl. Claude-Aufrufe (langsam, API-Key nötig)
"""

from __future__ import annotations
import json
import pathlib
import sys
import time
import traceback

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from parsers import parse_typeform_payload
from logic.level_calculator import berechne_level
from logic.volume_calculator import berechne_volumen, tier_floor, _RPE_RANGES
from logic.split_selector import waehle_split
from logic.equipment_filter import filtere_uebungen
from logic.plan_assembler import assemble_plan
from realism_validator import pruefe_realismus
from models import Hauptziel

BASE_HIDDEN   = {"client_id": "00000000-0000-0000-0000-000000000001"}
BASE_SUBMITTED = "2026-05-28T12:00:00Z"


def make_payload(
    vorname="Test",
    alter=35,
    hauptziel_ref="muskelaufbau",
    nebenziel_ref=None,
    tage=4,
    session_min=60,
    equipment_ref="gym",
    trainingsjahre_ref="ein_bis_zwei",
    stress=5,
    schlaf="7",
    verletzungen_labels=None,
    schmerzen_akut=False,
    kniebeugen=22, pushups=18, situps=14, burpees=7, plank=52,
    client_id="00000000-0000-0000-0000-000000000001",
) -> dict:
    """Baut einen minimalen Typeform-Payload für Tests."""
    answers = [
        {"type": "text",   "text": vorname,
         "field": {"ref": "vorname", "type": "short_text"}},
        {"type": "number", "number": alter,
         "field": {"ref": "alter", "type": "number"}},
        {"type": "choice", "choice": {"ref": hauptziel_ref, "label": hauptziel_ref},
         "field": {"ref": "hauptziel", "type": "multiple_choice"}},
        {"type": "choice", "choice": {"ref": f"uuid-{tage}", "label": str(tage)},
         "field": {"ref": "tage_pro_woche", "type": "multiple_choice"}},
        {"type": "choice", "choice": {"ref": f"uuid-{session_min}", "label": str(session_min)},
         "field": {"ref": "session_dauer_min", "type": "multiple_choice"}},
        {"type": "choice", "choice": {"ref": equipment_ref, "label": equipment_ref},
         "field": {"ref": "equipment", "type": "multiple_choice"}},
        {"type": "choice", "choice": {"ref": trainingsjahre_ref, "label": trainingsjahre_ref},
         "field": {"ref": "trainingsjahre", "type": "multiple_choice"}},
        {"type": "number", "number": stress,
         "field": {"ref": "stress_level", "type": "opinion_scale"}},
        {"type": "choice", "choice": {"ref": f"uuid-{schlaf}h", "label": schlaf},
         "field": {"ref": "schlaf_stunden", "type": "multiple_choice"}},
        {"type": "boolean", "boolean": schmerzen_akut,
         "field": {"ref": "schmerzen_akut", "type": "yes_no"}},
        {"type": "number", "number": kniebeugen,
         "field": {"ref": "kniebeugen_wdh", "type": "number"}},
        {"type": "number", "number": pushups,
         "field": {"ref": "pushups_wdh", "type": "number"}},
        {"type": "number", "number": situps,
         "field": {"ref": "situps_wdh", "type": "number"}},
        {"type": "number", "number": burpees,
         "field": {"ref": "burpees_wdh", "type": "number"}},
        {"type": "number", "number": plank,
         "field": {"ref": "plank_sek", "type": "number"}},
    ]

    # Nebenziel optional
    if nebenziel_ref:
        answers.append({
            "type": "choice",
            "choice": {"ref": nebenziel_ref, "label": nebenziel_ref},
            "field": {"ref": "nebenziel", "type": "multiple_choice"},
        })

    # Verletzungen
    labels = verletzungen_labels or ["keine"]
    answers.append({
        "type": "choices",
        "choices": {"labels": labels, "ids": [], "refs": []},
        "field": {"ref": "verletzungen", "type": "multiple_choice"},
    })

    return {
        "event_type": "form_response",
        "form_response": {
            "form_id": "TEST",
            "token": "test",
            "submitted_at": BASE_SUBMITTED,
            "hidden": {"client_id": client_id},
            "answers": answers,
        },
    }


# ── Test-Cases ────────────────────────────────────────────────────────────────

TEST_CASES = [
    # (Name, kwargs für make_payload)

    # Alle Equipment-Pfade
    ("Gym / 4T / Muskelaufbau",          dict(equipment_ref="gym",        tage=4, hauptziel_ref="muskelaufbau")),
    ("Home Gym / 3T / Fettabbau",        dict(equipment_ref="home_gym",   tage=3, hauptziel_ref="fettabbau")),
    ("Kettlebell / 3T / Longevity",      dict(equipment_ref="kettlebell", tage=3, hauptziel_ref="longevity")),
    ("Bodyweight / 5T / Longevity",      dict(equipment_ref="bodyweight", tage=5, hauptziel_ref="longevity")),
    ("Travel / 3T / Muskelaufbau",       dict(equipment_ref="travel",     tage=3, hauptziel_ref="muskelaufbau")),
    ("Hybrid / 4T / Fettabbau",          dict(equipment_ref="hybrid",     tage=4, hauptziel_ref="fettabbau")),

    # Alle Ziele mit 4 Tagen Gym
    ("Gym / 4T / Fettabbau",             dict(equipment_ref="gym", tage=4, hauptziel_ref="fettabbau")),
    ("Gym / 6T / Longevity",             dict(equipment_ref="gym", tage=6, hauptziel_ref="longevity")),
    ("Gym / 4T / Longevity",             dict(equipment_ref="gym", tage=4, hauptziel_ref="longevity")),

    # Verschiedene Tage
    ("Gym / 6T / Fettabbau",             dict(equipment_ref="gym", tage=6, hauptziel_ref="fettabbau")),
    ("Gym / 3T / Muskelaufbau",          dict(equipment_ref="gym", tage=3, hauptziel_ref="muskelaufbau")),
    ("Gym / 5T / Muskelaufbau",          dict(equipment_ref="gym", tage=5, hauptziel_ref="muskelaufbau")),
    ("Gym / 6T / Muskelaufbau",          dict(equipment_ref="gym", tage=6, hauptziel_ref="muskelaufbau")),

    # Level-Extremwerte
    ("Level 1 — Absoluter Anfänger",     dict(kniebeugen=5, pushups=5, situps=5, burpees=3, plank=20,
                                              trainingsjahre_ref="keine")),
    ("Level 4 — Athlet",                 dict(kniebeugen=80, pushups=60, situps=75, burpees=40, plank=200,
                                              trainingsjahre_ref="fuenf_plus")),

    # Verletzungen
    ("Schulter-Verletzung",              dict(verletzungen_labels=["schulter"])),
    ("Knie-Verletzung",                  dict(verletzungen_labels=["knie"])),
    ("Mehrere Verletzungen",             dict(verletzungen_labels=["schulter", "knie", "hüfte"])),
    ("Akuter Schmerz",                   dict(schmerzen_akut=True, verletzungen_labels=["wirbelsäule"])),

    # Recovery-Modifier
    ("Hoher Stress (9/10)",              dict(stress=9, schlaf="5")),
    ("Optimale Recovery",                dict(stress=3, schlaf="8")),

    # Nebenziel
    ("Mit Nebenziel (Muskel+Fett)",      dict(hauptziel_ref="muskelaufbau", nebenziel_ref="fettabbau")),
    ("Mit Nebenziel (Fett+Ausdauer)",    dict(hauptziel_ref="fettabbau",    nebenziel_ref="ausdauer")),

    # Dauer-kontrollierte Slot-Architektur
    ("Anna — L1, Recomp, 4×45, 5 Slots",
     dict(hauptziel_ref="recomp", tage=4, session_min=45,
          kniebeugen=20, pushups=10, situps=25, burpees=10, plank=45,
          trainingsjahre_ref="keine")),
    ("Max — L2, Muskelaufbau, 4×60, 6 Slots",
     dict(hauptziel_ref="muskelaufbau", tage=4, session_min=60,
          kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80,
          trainingsjahre_ref="ein_bis_zwei")),
    ("Tim — Muskelaufbau, 3×20, 3-Slot FB",
     dict(hauptziel_ref="muskelaufbau", tage=3, session_min=20)),
]

# Subset für Claude-Tests (teuer + langsam)
CLAUDE_TEST_CASES = [
    ("Gym / 4T / Muskelaufbau / Schulter",
     dict(equipment_ref="gym", tage=4, hauptziel_ref="muskelaufbau", verletzungen_labels=["schulter"])),
    ("Kettlebell / 3T / Fettabbau",
     dict(equipment_ref="kettlebell", tage=3, hauptziel_ref="fettabbau")),
    ("Bodyweight / 3T / Longevity / Hoher Stress",
     dict(equipment_ref="bodyweight", tage=3, hauptziel_ref="longevity", stress=9, schlaf="5")),
]


# ── Test-Runner ────────────────────────────────────────────────────────────────

def run_logic_test(name: str, kwargs: dict) -> tuple[bool, str]:
    try:
        payload = make_payload(**kwargs)
        klient  = parse_typeform_payload(payload)
        level, punkte = berechne_level(klient)

        for woche_typ in ["akkumulation", "progression", "intensivierung", "deload"]:
            volumen = berechne_volumen(klient, level, woche_typ)
            assert volumen["ziel_saetze"] >= 1
            assert 4 <= volumen["ziel_rpe"] <= 10

        split    = waehle_split(klient, level)
        uebungen = filtere_uebungen(klient, level)

        assert split["sessions"], "Keine Sessions"
        total = sum(len(v) for v in uebungen.values())
        assert total >= 4, f"Zu wenige Übungen: {total}"

        # Slot-Anzahl der ersten Kraft-Session
        kraft_s = next((s for s in split["sessions"] if s.get("session_typ","kraft") == "kraft"), None)
        slots_str = f"{len(kraft_s['slots'])}S" if kraft_s and "slots" in kraft_s else "?"

        detail = f"Level {level} | {split['split_typ']} | {slots_str} Slots | {total} Übungen"
        return True, detail

    except Exception as e:
        return False, f"{type(e).__name__}: {e}"


def run_claude_test(name: str, kwargs: dict) -> tuple[bool, str]:
    import os
    from logic.volume_calculator import berechne_volumen
    from claude.claude_client import generiere_uebungsauswahl

    try:
        payload  = make_payload(**kwargs)
        klient   = parse_typeform_payload(payload)
        level, _ = berechne_level(klient)
        volumen  = berechne_volumen(klient, level, "akkumulation")
        split    = waehle_split(klient, level)
        uebungen = filtere_uebungen(klient, level)

        t0 = time.time()
        claude_out = generiere_uebungsauswahl(
            klient=klient, level=level, split_typ=split["split_typ"],
            block_nummer=1, sessions=split["sessions"],
            uebungen_gefiltert=uebungen, woche_typ="akkumulation",
            ziel_saetze=volumen["ziel_saetze"], ziel_rpe=volumen["ziel_rpe"],
        )
        plan = assemble_plan(klient=klient, level=level, split=split,
                             claude_output=claude_out, block_nummer=1)
        dauer = time.time() - t0

        sessions_total = sum(len(w["sessions"]) for w in plan.model_dump()["wochen"])
        return True, f"{len(claude_out.sessions)} Sessions, Plan in {dauer:.1f}s"

    except Exception as e:
        return False, f"{type(e).__name__}: {e}\n{traceback.format_exc()[-300:]}"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    with_claude = "--claude" in sys.argv

    print("=" * 65)
    print("LOGIK-TESTS (Parse → Level → Volumen → Split → Filter)")
    print("=" * 65)

    passed = failed = 0
    for name, kwargs in TEST_CASES:
        ok, detail = run_logic_test(name, kwargs)
        icon = "✅" if ok else "❌"
        status = "OK" if ok else "FEHLER"
        print(f"  {icon} {name:<42}  {detail}")
        if ok: passed += 1
        else:  failed += 1

    print()
    print(f"  Ergebnis: {passed}/{passed+failed} bestanden")

    # ── Realism-Validator-Tests ───────────────────────────────────────────────
    print()
    print("=" * 65)
    print("REALISM-VALIDATOR TESTS")
    print("=" * 65)

    realismus_cases = [
        # (beschreibung, ziel, tage, dauer, erwarteter_typ)
        ("Tim 2×20 → Warnung Muskelaufbau",   "muskelaufbau", 2, 20,  "warnung"),
        ("3×30 → Warnung Recomp",              "recomp",       3, 30,  "warnung"),
        ("3×45 → Hinweis Muskelaufbau",        "muskelaufbau", 3, 45,  "hinweis"),  # 135 min < 180
        ("4×45 → OK Muskelaufbau",             "muskelaufbau", 4, 45,  None),
        ("4×60 → OK Recomp",                   "recomp",       4, 60,  None),
        ("2×60 → OK Longevity",                "longevity",    2, 60,  None),       # 120 min = schwelle, nicht drunter
        ("2×20 → Warnung Longevity",           "longevity",    2, 20,  "warnung"),
    ]

    r_passed = r_failed = 0
    for desc, ziel_str, tage, dauer, erwartet in realismus_cases:
        result = pruefe_realismus(Hauptziel(ziel_str), tage, dauer)
        got_typ = result["typ"] if result else None
        ok = got_typ == erwartet
        icon = "✅" if ok else "❌"
        got_label = got_typ or "OK"
        erwartet_label = erwartet or "OK"
        print(f"  {icon} {desc:<40}  erwartet={erwartet_label:<8} got={got_label}")
        if ok: r_passed += 1
        else:  r_failed += 1

    print()
    print(f"  Ergebnis: {r_passed}/{r_passed+r_failed} bestanden")

    # ── RPE-Wellen-Tests (MVP-6 Naht 1) ───────────────────────────────────────
    print()
    print("=" * 65)
    print("RPE-WELLEN-TESTS (Periodisierung + Recovery-Deckel, Spec Thema 1/5)")
    print("=" * 65)

    def _klient(stress: int, schlaf: str):
        return parse_typeform_payload(make_payload(stress=stress, schlaf=schlaf))

    w_passed = w_failed = 0

    def _check(desc: str, fn):
        nonlocal w_passed, w_failed
        try:
            fn()
            print(f"  ✅ {desc}")
            w_passed += 1
        except AssertionError as e:
            print(f"  ❌ {desc}  →  {e}")
            w_failed += 1

    k_normal = _klient(5, "6")   # lage 'normal' → reine Wellen-Basis (kein Deckel)

    def wave_per_level():
        for lvl in (1, 2, 3, 4):
            lo, hi = _RPE_RANGES[lvl]
            akku   = berechne_volumen(k_normal, lvl, "akkumulation")["ziel_rpe"]
            prog   = berechne_volumen(k_normal, lvl, "progression")["ziel_rpe"]
            intens = berechne_volumen(k_normal, lvl, "intensivierung")["ziel_rpe"]
            assert akku < prog < intens, f"L{lvl}: nicht streng monoton {akku}/{prog}/{intens}"
            assert akku == float(lo) and intens == float(hi), f"L{lvl}: Anker {akku}/{intens} != {lo}/{hi}"
            step = prog - akku
            assert step in (0.5, 1.0), f"L{lvl}: Schritt {step} nicht in {{0.5,1.0}}"
            assert (intens - prog) == step, f"L{lvl}: ungleiche Schritte"

    def deload_rpe_und_saetze():
        for lvl in (1, 2, 3, 4):
            lo, _ = _RPE_RANGES[lvl]
            d = berechne_volumen(k_normal, lvl, "deload")
            assert d["ziel_rpe"] == max(4.0, lo - 1), f"L{lvl}: Deload-RPE {d['ziel_rpe']} != rpe_low-1"
            for tier in ("compound", "accessory", "isolation", "core"):
                assert d[f"{tier}_saetze"] == tier_floor(tier), f"L{lvl}/{tier}: Deload-Sätze != Cap-Floor"

    def recovery_deckel():
        # L2/Progression, Wellen-Basis 7.5; lo=7 hi=8
        erwartet = {"sehr_hoch": 6.0, "hoch": 7.0, "gut": 8.0, "normal": 7.5}
        lagen = {"sehr_hoch": (9, "5"), "hoch": (8, "6"), "gut": (3, "8"), "normal": (5, "6")}
        for lage, (s, sl) in lagen.items():
            got = berechne_volumen(_klient(s, sl), 2, "progression")["ziel_rpe"]
            assert got == erwartet[lage], f"lage {lage}: {got} != {erwartet[lage]}"
        # gute Recovery nie über rpe_high
        assert berechne_volumen(_klient(3, "8"), 2, "progression")["ziel_rpe"] <= _RPE_RANGES[2][1]

    def deload_ignoriert_recovery():
        # sehr_hoch darf den Deload-RPE nicht weiter senken (Floor rpe_low-1 greift direkt)
        for lvl in (1, 2, 3, 4):
            lo, _ = _RPE_RANGES[lvl]
            got = berechne_volumen(_klient(9, "4"), lvl, "deload")["ziel_rpe"]
            assert got == max(4.0, lo - 1), f"L{lvl}: Deload+sehr_hoch {got} != {max(4.0, lo-1)}"

    def kein_float_in_saetzen():
        v = berechne_volumen(k_normal, 2, "progression")
        for key, val in v.items():
            if "saetze" in key:
                assert isinstance(val, int), f"{key} ist {type(val).__name__}, erwartet int"
            if "rpe" in key:
                assert isinstance(val, float), f"{key} ist {type(val).__name__}, erwartet float"

    _check("Welle streng monoton + Anker (rpe_low→rpe_high), Schritt 0.5/1.0", wave_per_level)
    _check("Deload-RPE == rpe_low−1 (Floor 4) + Deload-Sätze == Cap-Floor",      deload_rpe_und_saetze)
    _check("Recovery-Deckel über 4 Lagen, gute Recovery nie > rpe_high",         recovery_deckel)
    _check("Deload ignoriert Recovery (Floor greift direkt)",                    deload_ignoriert_recovery)
    _check("Kein Float in Sätzen, RPE ist float (Frontend-Vertrag)",            kein_float_in_saetzen)

    print()
    print(f"  Ergebnis: {w_passed}/{w_passed+w_failed} bestanden")

    # ── RIR-Hilfe-Tests (MVP-6 Naht 3, additiv) ───────────────────────────────
    print()
    print("=" * 65)
    print("RIR-HILFE-TESTS (Level-1-rpe_hinweis, rein additiv)")
    print("=" * 65)

    from scripts.generate_test_plans import _auto_claude_output
    from logic.conditioning_formats import CONDITIONING as _METABOLIC

    _L1 = dict(kniebeugen=5, pushups=5, situps=5, burpees=3, plank=20, trainingsjahre_ref="keine")

    def _plan(kwargs: dict):
        klient   = parse_typeform_payload(make_payload(**kwargs))
        level, _ = berechne_level(klient)
        split    = waehle_split(klient, level)
        ueb      = filtere_uebungen(klient, level)
        plan     = assemble_plan(klient=klient, level=level, split=split,
                                 claude_output=_auto_claude_output(split, ueb), block_nummer=1)
        return level, plan.model_dump()

    def _split_kind(plan: dict):
        strength, metcon = [], []
        for w in plan["wochen"]:
            for s in w["sessions"]:
                (metcon if s.get("session_typ") in _METABOLIC else strength).extend(s["haupt_uebungen"])
        return strength, metcon

    rir_passed = rir_failed = 0

    def _rcheck(desc: str, fn):
        nonlocal rir_passed, rir_failed
        try:
            fn()
            print(f"  ✅ {desc}")
            rir_passed += 1
        except AssertionError as e:
            print(f"  ❌ {desc}  →  {e}")
            rir_failed += 1

    def l1_kraft_hat_hinweis():
        lvl, plan = _plan(dict(hauptziel_ref="muskelaufbau", tage=4, **_L1))
        assert lvl == 1, f"Fixture nicht L1 (got L{lvl})"
        st, _ = _split_kind(plan)
        assert st, "keine Kraft-Übungen im Plan"
        assert all(u["rpe_hinweis"] for u in st), "L1-Kraftsatz ohne rpe_hinweis"

    def l1_metcon_bleibt_none():
        lvl, plan = _plan(dict(hauptziel_ref="fettabbau", tage=4, **_L1))
        assert lvl == 1, f"Fixture nicht L1 (got L{lvl})"
        _, mc = _split_kind(plan)
        assert mc, "kein Metcon-Anteil im Fettabbau-Plan"
        assert all(u["rpe_hinweis"] is None for u in mc), "L1-Metcon-Satz trägt rpe_hinweis"

    def l2_komplett_none():
        lvl, plan = _plan(dict(hauptziel_ref="muskelaufbau", tage=4, session_min=60,
                               kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80,
                               trainingsjahre_ref="ein_bis_zwei"))
        assert lvl == 2, f"Fixture nicht L2 (got L{lvl})"
        st, mc = _split_kind(plan)
        assert all(u["rpe_hinweis"] is None for u in st + mc), "L2 trägt rpe_hinweis"

    _rcheck("L1-Kraftsätze tragen rpe_hinweis (RIR-Klartext)", l1_kraft_hat_hinweis)
    _rcheck("L1-Metcon-Sätze bleiben None",                    l1_metcon_bleibt_none)
    _rcheck("L2 komplett None (kein RIR-Hinweis)",             l2_komplett_none)

    print()
    print(f"  Ergebnis: {rir_passed}/{rir_passed+rir_failed} bestanden")

    # ── Conditioning ohne RPE (MVP-7 Naht 2a) ─────────────────────────────────
    print()
    print("=" * 65)
    print("CONDITIONING OHNE RPE (MVP-7 Naht 2a)")
    print("=" * 65)

    cr_passed = cr_failed = 0

    def _crcheck(desc: str, fn):
        nonlocal cr_passed, cr_failed
        try:
            fn()
            print(f"  ✅ {desc}")
            cr_passed += 1
        except AssertionError as e:
            print(f"  ❌ {desc}  →  {e}")
            cr_failed += 1

    def metcon_ohne_rpe_kraft_mit():
        _, plan = _plan(dict(hauptziel_ref="fettabbau", tage=4, **_L1))
        st, mc = _split_kind(plan)
        assert mc, "kein Metcon-Anteil im Fettabbau-Plan"
        assert all(u["rpe"] is None for u in mc), "Conditioning-Satz trägt RPE"
        assert st and all(u["rpe"] is not None for u in st), "Kraft-Satz ohne RPE"

    def recomp_finisher_ohne_rpe():
        _, plan = _plan(dict(hauptziel_ref="recomp", tage=4, session_min=45, **_L1))
        blocks = [s["metcon_block"] for w in plan["wochen"] for s in w["sessions"] if s.get("metcon_block")]
        assert blocks, "kein Recomp-Finisher (metcon_block) im Plan"
        assert all(u["rpe"] is None for mb in blocks for u in mb["uebungen"]), "Finisher-Satz trägt RPE"

    _crcheck("Conditioning-Sätze rpe None, Kraft-Sätze rpe gesetzt", metcon_ohne_rpe_kraft_mit)
    _crcheck("Recomp-Finisher (metcon_block) rpe None",             recomp_finisher_ohne_rpe)

    print()
    print(f"  Ergebnis: {cr_passed}/{cr_passed+cr_failed} bestanden")

    # ── Conditioning-Format-Baukasten (MVP-7 Naht 2c) ─────────────────────────
    print()
    print("=" * 65)
    print("CONDITIONING-FORMAT-BAUKASTEN (MVP-7 Naht 2c)")
    print("=" * 65)

    from logic.conditioning_formats import (
        pick_conditioning_formats, conditioning_target_min, block_count, block_session_dauer,
        block_params, level_work_rest, CONDITIONING, conditioning_pool,
        split_conditioning_segments, pick_second_format, _FORMAT_MAX_MIN, _BIG_FORMATS,
    )

    cf_passed = cf_failed = 0

    def _cfcheck(desc: str, fn):
        nonlocal cf_passed, cf_failed
        try:
            fn()
            print(f"  ✅ {desc}")
            cf_passed += 1
        except AssertionError as e:
            print(f"  ❌ {desc}  →  {e}")
            cf_failed += 1

    def pool_helfer():
        # Naht 4a: conditioning_pool sammelt pattern==conditioning + conditioning_friendly,
        # dedup, kein Kraft-only. (Helfer existiert, noch nicht verdrahtet.)
        k = parse_typeform_payload(make_payload(hauptziel_ref="fettabbau", tage=6,
                                                equipment_ref="bodyweight", kniebeugen=35, pushups=20,
                                                situps=35, burpees=20, plank=80, trainingsjahre_ref="ein_bis_zwei"))
        lvl, _ = berechne_level(k)
        f = filtere_uebungen(k, lvl)
        pool = conditioning_pool(f)
        ids = [e["id"] for e in pool]
        assert pool, "leerer Conditioning-Pool"
        assert len(ids) == len(set(ids)), "Dubletten im Pool"
        assert all(e["pattern"] == "conditioning" or e.get("conditioning_friendly") for e in pool), "Kraft-only im Pool"
        assert any(e["pattern"] == "conditioning" for e in pool), "kein pattern==conditioning im Pool"
        assert any(e.get("conditioning_friendly") and e["pattern"] != "conditioning" for e in pool), "kein cf-true im Pool"
        kraft_only = [e for e in f.get("squat", []) if not e.get("conditioning_friendly")]
        if kraft_only:
            assert kraft_only[0]["id"] not in set(ids), "Kraft-only-Squat im Pool"

    def finisher_aus_pool():
        # Naht 4b: Finisher zieht aus dem Conditioning-Pool (equipment-korrekt), nicht aus Kraft-Pattern.
        def setup(eq):
            kw = dict(hauptziel_ref="recomp", tage=4, session_min=45, equipment_ref=eq,
                      kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80, trainingsjahre_ref="ein_bis_zwei")
            k = parse_typeform_payload(make_payload(**kw))
            lvl, _ = berechne_level(k)
            sp = waehle_split(k, lvl); ub = filtere_uebungen(k, lvl)
            plan = assemble_plan(klient=k, level=lvl, split=sp,
                                 claude_output=_auto_claude_output(sp, ub), block_nummer=1).model_dump()
            pool = conditioning_pool(ub)
            fin = {u["exercise_id"] for w in plan["wochen"] for s in w["sessions"]
                   if s.get("metcon_block") for u in s["metcon_block"]["uebungen"]}
            return pool, fin
        # Bodyweight-Kunde: Finisher-Übungen alle aus dem Pool, keine reine-KB-Übung
        pool_bw, fin_bw = setup("bodyweight")
        assert fin_bw, "kein Finisher (BW)"
        assert fin_bw <= {e["id"] for e in pool_bw}, "Finisher nicht aus Conditioning-Pool (BW)"
        kb_only_bw = {e["id"] for e in pool_bw if "kettlebell" in e["equipment"] and "bodyweight" not in e["equipment"]}
        assert not (fin_bw & kb_only_bw), "reine-KB-Übung im BW-Finisher"
        # Kettlebell-Kunde: Pool gemischt (BW + KB), BW ist Mehrheit
        pool_kb, fin_kb = setup("kettlebell")
        bw = [e for e in pool_kb if "bodyweight" in e["equipment"]]
        kb_only = [e for e in pool_kb if "kettlebell" in e["equipment"] and "bodyweight" not in e["equipment"]]
        assert bw and kb_only, "KB-Pool nicht gemischt (BW + KB)"
        assert len(bw) > len(kb_only), f"Bodyweight nicht Mehrheit im KB-Pool (bw={len(bw)} kb={len(kb_only)})"
        assert fin_kb <= {e["id"] for e in pool_kb}, "Finisher nicht aus Conditioning-Pool (KB)"
        # BW-first-Pick: Bodyweight bleibt Hauptteil auch im gepickten KB-Finisher
        pool_kb_by_id = {e["id"]: e for e in pool_kb}
        bw_in_fin = sum(1 for fid in fin_kb if "bodyweight" in pool_kb_by_id[fid]["equipment"])
        assert bw_in_fin * 2 >= len(fin_kb), f"Bodyweight nicht Mehrheit im KB-Finisher ({bw_in_fin}/{len(fin_kb)})"

    def rotation_zwei_verschiedene():
        # Naht 3: die 2 C-Tage einer Woche → 2 verschiedene Formate (weiche Bevorzugung, Pool ≥ 2)
        for lvl in (1, 2, 3, 4):
            for eq in ("gym", "bodyweight", "kettlebell", "home_gym", "travel", "hybrid"):
                fmts = pick_conditioning_formats(lvl, eq, 2)
                assert len(fmts) == 2 and fmts[0] != fmts[1], f"L{lvl}/{eq}: {fmts} nicht 2 verschieden"
        # Equipment-Bevorzugung: bevorzugtes Format zuerst
        assert pick_conditioning_formats(4, "kettlebell", 2)[0] == "density", "KB-Bevorzugung"
        assert pick_conditioning_formats(4, "bodyweight", 2)[0] in {"amrap", "tabata"}, "BW-Bevorzugung"
        # kein Format 2× direkt hintereinander, auch bei n=4 (zyklisch durch den Pool)
        fmts = pick_conditioning_formats(3, "gym", 4)
        assert all(fmts[i] != fmts[i + 1] for i in range(3)), f"2× hintereinander: {fmts}"

    def ziel_dauer_session_minus_warmup():
        # Dauer = Client-Session − Warmup, KEINE Level-Deckelung (level-unabhängig)
        assert conditioning_target_min(45) == 35, conditioning_target_min(45)
        assert conditioning_target_min(60) == 50
        assert conditioning_target_min(30) == 20

    def tabata_block_stapelung():
        # Ziel 30 min → 6 Blöcke à 4 Min + 5×60 s = 29 min; festes 20/10-Timing
        assert block_count("tabata", 30) == 6 and block_session_dauer("tabata", 30) == 29
        assert block_count("tabata", 10) == 2                                           # min. 2 Blöcke
        assert block_params("tabata")["saetze"] == 8 and "20 s" in block_params("tabata")["wdh"]

    def density_5min_bloecke():
        assert block_count("density", 18) == 3 and block_session_dauer("density", 18) == 17
        for t in (12, 18, 30):
            n = block_count("density", t)
            assert block_session_dauer("density", t) == n * 5 + (n - 1), f"Density-Dauer-Formel @ {t}"

    def l4_work_rest():
        assert level_work_rest(4) == (45, 15)

    def alle_level_fuellen_45():
        # Dauer-Kernregel (format-agnostisch): ALLE reinen C-Tage @45min sind ~45 (Level deckelt NICHT),
        # egal welches Format die Rotation wählt; je Woche 2 verschiedene Formate.
        fixtures = [
            (dict(kniebeugen=5, pushups=5, situps=5, burpees=3, plank=20), "keine"),
            (dict(kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80), "ein_bis_zwei"),
            (dict(kniebeugen=80, pushups=60, situps=75, burpees=40, plank=200), "fuenf_plus"),
        ]
        for pst, tj in fixtures:
            lvl, plan = _plan(dict(hauptziel_ref="fettabbau", tage=6, session_min=45,
                                   trainingsjahre_ref=tj, **pst))
            cond = [s for w in plan["wochen"] for s in w["sessions"] if s["session_typ"] in CONDITIONING]
            assert cond, f"L{lvl}: keine Conditioning-Sessions"
            wk1 = [s["session_typ"] for s in plan["wochen"][0]["sessions"] if s["session_typ"] in CONDITIONING]
            assert len(wk1) == 2 and wk1[0] != wk1[1], f"L{lvl}: C-Tage je Woche nicht 2 verschieden: {wk1}"
            for s in cond:
                d = s["dauer_min_geschaetzt"]
                assert 40 <= d <= 50, f"L{lvl} {s['session_typ']} {d}min != ~45 (Level deckelt die Dauer nicht)"
                assert all(u["rpe"] is None for u in s["haupt_uebungen"])

    def e2e_a_recomp_finisher_kurz():
        # (a) gemischter Tag: Kraft + Finisher (NICHT block-gestapelt, kurz). 4e-2: Format rotiert {amrap, zirkel}.
        lvl, plan = _plan(dict(hauptziel_ref="recomp", tage=4, session_min=45,
                               kniebeugen=80, pushups=60, situps=75, burpees=40, plank=200,
                               trainingsjahre_ref="fuenf_plus"))
        sess = [s for w in plan["wochen"] for s in w["sessions"]]
        blocks = [s["metcon_block"] for s in sess if s.get("metcon_block")]
        assert blocks, "kein Recomp-Finisher"
        assert all(mb["typ"] in ("amrap", "zirkel") for mb in blocks), "Finisher außerhalb {amrap, zirkel}"
        assert not any(s["session_typ"] in ("tabata", "density") for s in sess), "Block-Stapelung leakt in gemischten Tag"
        # Fix 2 (C5): AMRAP-Finisher zeigt echte Dauer (≤10 Min); Zirkel-Finisher rundenbasiert (kurz).
        import re
        for mb in blocks:
            if mb["typ"] == "amrap":
                m = re.match(r"(\d+) Min\. AMRAP", mb["format_notiz"])
                assert m and int(m.group(1)) <= 10, f"AMRAP-Finisher-Dauer falsch: {mb['format_notiz']!r}"
            else:
                assert "Zirkel" in mb["format_notiz"], f"Zirkel-Finisher-Notiz falsch: {mb['format_notiz']!r}"

    def multi_format_split():
        # Naht 4d: lange C-Tage auf 1/2 Format-Segmente (reine Funktion, noch nicht verdrahtet).
        split = split_conditioning_segments
        # Maxima gepinnt (Komplexe ausgelassen)
        assert _FORMAT_MAX_MIN == {"amrap":20,"density":30,"tabata":20,"intervalle":25,"ladders":20,"zirkel":30}
        assert "komplexe" not in _FORMAT_MAX_MIN, "Komplexe darf nicht im Maxima-Pool sein"
        # 1 Segment: target ≤ Max[first] (inkl. genau am Maximum)
        assert split(20, "amrap",   2, "bodyweight") == [("amrap", 20)]      # genau am Max
        assert split(30, "density", 2, "kettlebell") == [("density", 30)]    # genau am Max
        assert split(30, "zirkel",  3, "gym") == [("zirkel", 30)]            # Zirkel max 30 → 1 Segment
        assert split(20, "tabata",  4, "bodyweight") == [("tabata", 20)]     # genau am Max
        # 2 Segmente: erstes bis Max, zweites Rest — Coach-Beispiele
        s = split(35, "amrap", 2, "bodyweight")
        assert s[0] == ("amrap", 20) and s[1][1] == 15, s                    # 35 → 20+15
        s = split(35, "density", 3, "gym")
        assert s[0] == ("density", 25) and s[1][1] == 10, s                  # 35 → 25+10 (NIE 30+5)
        assert s[0][1] != 30, "Rumpf 30+5 verboten"
        s = split(50, "density", 3, "gym")
        assert s[0] == ("density", 30) and s[1][1] == 20, s                  # 50 → 30+20
        # Invarianten über alle Formate: Summe = target, jedes ≥10 + 5-Min-Raster, ≤2 Segmente, ≠ erstes
        for tgt in (35, 40, 50):
            for ff in ("amrap", "density", "tabata", "intervalle", "ladders", "zirkel"):
                segs = split(tgt, ff, 4, "hybrid")
                assert sum(d for _, d in segs) == tgt,         (tgt, ff, segs)
                assert all(d >= 10 and d % 5 == 0 for _, d in segs), (tgt, ff, segs)
                assert len(segs) <= 2,                         (tgt, ff, segs)
                if len(segs) == 2:
                    assert segs[0][0] != segs[1][0],           (tgt, ff, segs)
        # KEIN Segment darf sein eigenes Maximum überschreiten (Kapazitäts-Regel, s.u.)
        for tgt in (35, 40, 50):
            for ff in ("amrap", "density", "tabata", "intervalle", "ladders", "zirkel"):
                for fmt, d in split(tgt, ff, 4, "hybrid"):
                    assert d <= _FORMAT_MAX_MIN[fmt], f"{fmt} {d} > Max {_FORMAT_MAX_MIN[fmt]} @ {tgt}/{ff}"

    def kapazitaetsbewusstes_erstformat():
        # Naht 4d: großes Erstformat NUR wenn die Zeit es erzwingt (sonst Naht-3-Rotation unangetastet).
        split = split_conditioning_segments
        # (1) BW-L4 60 Min (=50 Conditioning): Rotation-Erstformat amrap(20) deckt 50 nicht ab →
        #     großes Erstformat. BW-L4-Pool hat kein Zirkel → Density 30 + AMRAP 20 = 50.
        first_bw_l4 = pick_conditioning_formats(4, "bodyweight", 1)[0]
        s = split(50, first_bw_l4, 4, "bodyweight")
        assert s == [("density", 30), ("amrap", 20)], s
        assert sum(d for _, d in s) == 50 and all(d <= _FORMAT_MAX_MIN[f] for f, d in s)
        # (3) Level MIT Zirkel: Zirkel als großes Erstformat bevorzugt (vor Density).
        s = split(50, "tabata", 3, "bodyweight")          # L3-BW-Pool enthält zirkel
        assert s == [("zirkel", 30), ("amrap", 20)], s
        # (2) Kurze Session (40 Min = 30 Conditioning): normale Rotation, KEIN erzwungenes großes
        #     Erstformat — das kleine Rotations-Erstformat bleibt erhalten.
        s = split(30, first_bw_l4, 4, "bodyweight")
        assert s[0][0] == first_bw_l4 and s[0][0] not in _BIG_FORMATS, s   # amrap bleibt erstes
        assert s == [("amrap", 20), ("tabata", 10)], s
        # Randfall: nicht abdeckbar (auch großes Erstformat reicht nicht) → ValueError, nicht still
        try:
            split(100, "amrap", 4, "bodyweight")
            assert False, "100 min sollte als nicht abdeckbar gemeldet werden (ValueError)"
        except ValueError:
            pass

    def zweitformat_amrap_bevorzugt():
        # Naht 4d: Zweitformat ≠ erstes, AMRAP bevorzugt wenn im Level-Pool, sonst nächstes Pool-Format.
        assert pick_second_format(3, "gym", exclude="density") == "amrap"        # amrap im L3-Pool → bevorzugt
        assert pick_second_format(1, "bodyweight", exclude="zirkel") == "intervalle"  # L1 ohne amrap → Rest
        # immer ≠ exclude über alle realen Level/Equipment (Pool praktisch ≥ 2)
        for lvl in (1, 2, 3, 4):
            for eq in ("gym", "bodyweight", "kettlebell", "home_gym", "travel", "hybrid"):
                first = pick_conditioning_formats(lvl, eq, 1)[0]
                second = pick_second_format(lvl, eq, exclude=first)
                assert second is not None and second != first, f"L{lvl}/{eq}: {first}->{second}"

    def e2e_multi_format_verdrahtet():
        # Naht 4d-3: langer reiner C-Tag (60min=50 cond) → 2 Segmente (Segment 2 im conditioning_block_2,
        # ≠ Erstformat, RPE None); kurzer C-Tag (30min=20 cond) → 1 Segment (kein block_2).
        base = dict(hauptziel_ref="fettabbau", tage=6, kniebeugen=80, pushups=60, situps=75,
                    burpees=40, plank=200, trainingsjahre_ref="fuenf_plus", equipment_ref="kettlebell")
        _, lang = _plan(dict(base, session_min=60))
        cdays = [s for s in lang["wochen"][0]["sessions"] if s["session_typ"] in CONDITIONING]
        assert cdays and all(s.get("conditioning_block_2") for s in cdays), "60min-C-Tag ohne 2. Segment"
        for s in cdays:
            b2 = s["conditioning_block_2"]
            assert b2["uebungen"], "Segment 2 leer"
            assert all(u["rpe"] is None for u in b2["uebungen"]), "Segment 2 mit RPE (Conditioning!)"
            assert b2["typ"] != s["session_typ"], f"Segment 2 == Segment 1 ({b2['typ']})"
        _, kurz = _plan(dict(base, session_min=30))
        cshort = [s for s in kurz["wochen"][0]["sessions"] if s["session_typ"] in CONDITIONING]
        assert cshort and not any(s.get("conditioning_block_2") for s in cshort), "30min-C-Tag hat fälschlich 2. Segment"

    def c_tage_uebungs_rotation():
        # Naht 4e-1: die 2 reinen C-Tage einer Woche ziehen VERSCHIEDENE Übungen (nicht nur Format),
        # über die Wochen variiert die Auswahl, KB-Kunde behält BW-Mehrheit.
        import json, pathlib
        exb = {e["id"]: e for e in json.loads(
            (pathlib.Path(__file__).parent.parent / "data" / "exercises.json").read_text())["exercises"]}
        _, plan = _plan(dict(hauptziel_ref="fettabbau", tage=6, session_min=45,
                             kniebeugen=80, pushups=60, situps=75, burpees=40, plank=200,
                             trainingsjahre_ref="fuenf_plus", equipment_ref="kettlebell"))
        def c_ids(wi):
            cs = [s for s in plan["wochen"][wi]["sessions"] if s["session_typ"] in CONDITIONING]
            return [tuple(u["exercise_id"] for u in s["haupt_uebungen"]) for s in cs]
        w1 = c_ids(0)
        assert len(w1) == 2 and w1[0] != w1[1], f"2 C-Tage Woche 1 übungsgleich: {w1}"   # räumlich
        assert w1 != c_ids(1), "C-Tag-Übungen Woche 1 == Woche 2 (keine zeitliche Rotation)"  # zeitlich
        # BW-Mehrheit im C-Tag erhalten (Equipment = Obergrenze, BW Hauptteil)
        for s in [s for s in plan["wochen"][0]["sessions"] if s["session_typ"] in CONDITIONING]:
            ids = [u["exercise_id"] for u in s["haupt_uebungen"]]
            bw = sum(1 for i in ids if "bodyweight" in exb[i]["equipment"])
            assert bw * 2 >= len(ids), f"BW nicht Mehrheit im C-Tag: {ids}"

    def finisher_rotation():
        # Naht 4e-2: Mischtag-Finisher rotiert Format über die 4 Wochen aus {amrap, zirkel} (nie 2×
        # hintereinander); bei wiederkehrendem Format sind die Übungen verschieden. F4: mehrere
        # Mischtage/Woche (Fettabbau 6) unterscheiden sich untereinander.
        _, plan = _plan(dict(hauptziel_ref="recomp", tage=4, session_min=45,
                             kniebeugen=80, pushups=60, situps=75, burpees=40, plank=200,
                             trainingsjahre_ref="fuenf_plus"))
        def first_fin(wi):
            return next((s["metcon_block"] for s in plan["wochen"][wi]["sessions"] if s.get("metcon_block")), None)
        seq = [first_fin(w) for w in range(4)]
        assert all(seq), "nicht jede Woche ein Finisher"
        typen = [mb["typ"] for mb in seq]
        assert set(typen) <= {"amrap", "zirkel"}, f"Finisher-Format außerhalb {{amrap,zirkel}}: {typen}"
        assert all(typen[i] != typen[i + 1] for i in range(3)), f"Finisher 2× hintereinander: {typen}"
        for i in range(4):
            for j in range(i + 1, 4):
                if typen[i] == typen[j]:   # wiederkehrendes Format → verschiedene Übungen
                    a = tuple(u["exercise_id"] for u in seq[i]["uebungen"])
                    b = tuple(u["exercise_id"] for u in seq[j]["uebungen"])
                    assert a != b, f"gleiches Format W{i+1}/W{j+1} mit gleichen Übungen: {a}"
        # F4: Fettabbau 6 — mehrere Mischtag-Finisher/Woche, untereinander verschieden (Format ODER Übungen)
        _, plan6 = _plan(dict(hauptziel_ref="fettabbau", tage=6, session_min=45,
                              kniebeugen=80, pushups=60, situps=75, burpees=40, plank=200,
                              trainingsjahre_ref="fuenf_plus"))
        fins = [s["metcon_block"] for s in plan6["wochen"][0]["sessions"] if s.get("metcon_block")]
        assert len(fins) >= 2, f"Fettabbau 6 sollte mehrere Mischtag-Finisher haben ({len(fins)})"
        sigs = [(mb["typ"], tuple(u["exercise_id"] for u in mb["uebungen"])) for mb in fins]
        assert len(set(sigs)) == len(sigs), f"Mischtag-Finisher nicht alle verschieden: {sigs}"

    _cfcheck("Naht 4e-1 C-Tag-Übungs-Rotation (2 C-Tage + Wochen verschieden, BW-Mehrheit)", c_tage_uebungs_rotation)
    _cfcheck("Naht 4e-2 Finisher-Rotation (W1–W4 kein 2×, gleiches Format → andere Übungen, F4)", finisher_rotation)
    _cfcheck("Naht 4d Multi-Format-Split (35→20+15/25+10, 50→30+20, ≤2 Segmente)", multi_format_split)
    _cfcheck("Naht 4d-3 verdrahtet (60min→2 Segmente/block_2, 30min→1 Segment)",   e2e_multi_format_verdrahtet)
    _cfcheck("Naht 4d Kapazitäts-Erstformat (BW-L4-60→Density+AMRAP, kurz=Rotation)", kapazitaetsbewusstes_erstformat)
    _cfcheck("Naht 4d Zweitformat AMRAP-bevorzugt, ≠ erstes",                     zweitformat_amrap_bevorzugt)
    _cfcheck("Naht 4a Conditioning-Pool-Helfer (cond/cf, dedup, kein Kraft-only)", pool_helfer)
    _cfcheck("Naht 4b Finisher aus Pool (BW equipment-korrekt, KB BW-mehrheitlich)", finisher_aus_pool)
    _cfcheck("Naht 3 Rotation: 2 C-Tage/Woche verschieden + Equipment-Bevorzugung", rotation_zwei_verschiedene)
    _cfcheck("Ziel-Dauer = Session − Warmup (keine Level-Deckelung)",            ziel_dauer_session_minus_warmup)
    _cfcheck("Tabata-Block-Stapelung (Ziel 30→6 Blöcke, festes 20/10-Timing)",   tabata_block_stapelung)
    _cfcheck("Density 5-Min-Blöcke (Dauer-Formel n×5 + Pausen)",                 density_5min_bloecke)
    _cfcheck("L4 Work:Rest == 45:15",                                           l4_work_rest)
    _cfcheck("L1/L2/L4 @45min → alle ~45 min (Level deckelt Dauer NICHT)",       alle_level_fuellen_45)
    _cfcheck("(a) Recomp = Kraft + amrap-Finisher (kurz, nicht block-gestapelt)", e2e_a_recomp_finisher_kurz)

    print()
    print(f"  Ergebnis: {cf_passed}/{cf_passed+cf_failed} bestanden")

    if with_claude:
        import os
        if not os.environ.get("OPENROUTER_API_KEY"):
            print("\n⚠️  OPENROUTER_API_KEY nicht gesetzt — Claude-Tests übersprungen.")
            return

        print()
        print("=" * 65)
        print("CLAUDE-TESTS (inkl. API-Aufruf + Plan-Assembler)")
        print("=" * 65)

        c_passed = c_failed = 0
        for name, kwargs in CLAUDE_TEST_CASES:
            print(f"  ... {name}", end="", flush=True)
            ok, detail = run_claude_test(name, kwargs)
            icon = "✅" if ok else "❌"
            print(f"\r  {icon} {name:<42}  {detail}")
            if ok: c_passed += 1
            else:  c_failed += 1

        print()
        print(f"  Ergebnis: {c_passed}/{c_passed+c_failed} bestanden")


if __name__ == "__main__":
    main()
