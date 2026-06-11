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
from logic.volume_calculator import berechne_volumen
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
    # TODO(ausdauer-rename): Testdaten umgestellt (MVP-4 Naht 1); Rest-Crash liegt in split_selector.py:399 (toter ausdauer-Zweig, faellt mit MVP-4 Naht 2).
    ("Kettlebell / 3T / Longevity",      dict(equipment_ref="kettlebell", tage=3, hauptziel_ref="longevity")),
    ("Bodyweight / 5T / Longevity",      dict(equipment_ref="bodyweight", tage=5, hauptziel_ref="longevity")),
    # TODO(testdata-tage-min3): tage=2 < Modell-Minimum (tage_pro_woche >= 3) — veraltete Testdaten, eigener Commit.
    ("Travel / 2T / Muskelaufbau",       dict(equipment_ref="travel",     tage=2, hauptziel_ref="muskelaufbau")),
    ("Hybrid / 4T / Fettabbau",          dict(equipment_ref="hybrid",     tage=4, hauptziel_ref="fettabbau")),

    # Alle Ziele mit 4 Tagen Gym
    ("Gym / 4T / Fettabbau",             dict(equipment_ref="gym", tage=4, hauptziel_ref="fettabbau")),
    ("Gym / 6T / Longevity",             dict(equipment_ref="gym", tage=6, hauptziel_ref="longevity")),
    ("Gym / 4T / Longevity",             dict(equipment_ref="gym", tage=4, hauptziel_ref="longevity")),

    # Verschiedene Tage
    # TODO(testdata-tage-min3): tage=2 < Modell-Minimum (tage_pro_woche >= 3) — veraltete Testdaten, eigener Commit.
    ("Gym / 2T / Muskelaufbau",          dict(equipment_ref="gym", tage=2, hauptziel_ref="muskelaufbau")),
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
    # TODO(testdata-tage-min3): tage=2 < Modell-Minimum (tage_pro_woche >= 3) — veraltete Testdaten, eigener Commit.
    ("Tim — Muskelaufbau, 2×20, 3-Slot FB",
     dict(hauptziel_ref="muskelaufbau", tage=2, session_min=20)),
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
