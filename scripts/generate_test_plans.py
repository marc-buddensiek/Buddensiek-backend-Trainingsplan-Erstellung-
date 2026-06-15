"""
Generiert Test-PDFs für alle relevanten Pipeline-Pfade — ohne Claude API.

Übungen werden deterministisch zugewiesen: erstes Exercise je Slot-Pattern
aus der gefilterten Liste. Testet Struktur, Volumen, Splits, Slots, Warm-Up,
Cardio, Realism-Warnings — alles außer Claude's Übungsauswahl-Intelligenz.

Verwendung:
  python3 scripts/generate_test_plans.py
  → Speichert PDFs in output/test_plans/
"""

from __future__ import annotations
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from scripts.run_tests import make_payload
from parsers import parse_typeform_payload
from logic.level_calculator import berechne_level
from logic.split_selector import waehle_split
from logic.equipment_filter import filtere_uebungen
from logic.plan_assembler import assemble_plan
from models import ClaudeOutput, SessionAuswahl, UebungAuswahl
from pdf_generator import build_pdf


# ── Deterministischer Exercise-Picker ─────────────────────────────────────────

def _auto_claude_output(split: dict, uebungen: dict[str, list]) -> ClaudeOutput:
    """
    Wählt für jeden Slot die erste passende Übung aus der gefilterten Liste.
    Fallback: nächste verfügbare Pattern wenn exakter Match fehlt.
    """
    alle_exercises = [ex for exs in uebungen.values() for ex in exs]
    pattern_index: dict[str, int] = {}  # round-robin je Pattern

    sessions = []
    for session_tmpl in split["sessions"]:
        uebungen_auswahl = []
        slots = session_tmpl.get("slots", [])

        for i, slot in enumerate(slots):
            pattern = slot["pattern"]

            # Versuche passendes Exercise zu finden (round-robin für Abwechslung)
            candidates = uebungen.get(pattern, [])
            if not candidates:
                # Fallback: irgendein Exercise
                candidates = alle_exercises

            idx = pattern_index.get(pattern, 0)
            ex = candidates[idx % len(candidates)]
            pattern_index[pattern] = idx + 1

            uebungen_auswahl.append(UebungAuswahl(
                reihenfolge=i + 1,
                exercise_id=ex["id"],
                notiz="",
            ))

        if uebungen_auswahl:
            sessions.append(SessionAuswahl(
                session_id=session_tmpl["session_id"],
                uebungen=uebungen_auswahl,
            ))

    return ClaudeOutput(sessions=sessions)


# ── Test-Cases ─────────────────────────────────────────────────────────────────

TEST_CASES = [
    # (dateiname, vorname, make_payload kwargs)

    # ── Standard-Basis (Gym × Level × Dauer) ──────────────────────────────────
    ("01_gym_muskel_4x60_L1",  "Alex",
     dict(hauptziel_ref="muskelaufbau", tage=4, session_min=60, equipment_ref="gym",
          trainingsjahre_ref="keine",
          kniebeugen=12, pushups=8, situps=10, burpees=5, plank=35)),

    ("02_gym_muskel_4x60_L2",  "Max",
     dict(hauptziel_ref="muskelaufbau", tage=4, session_min=60, equipment_ref="gym",
          trainingsjahre_ref="ein_bis_zwei",
          kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80)),

    ("03_gym_muskel_4x60_L4",  "Stefan",
     dict(hauptziel_ref="muskelaufbau", tage=4, session_min=60, equipment_ref="gym",
          trainingsjahre_ref="fuenf_plus",
          kniebeugen=80, pushups=60, situps=75, burpees=40, plank=200)),

    # ── Slot-Varianten (Dauer) ─────────────────────────────────────────────────
    ("04_gym_muskel_3x45_L2_fullbody", "Julia",
     dict(hauptziel_ref="muskelaufbau", tage=3, session_min=45, equipment_ref="gym",
          trainingsjahre_ref="ein_bis_zwei",
          kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80)),

    ("05_gym_muskel_3x20_L1_warnung",  "Tim",
     dict(hauptziel_ref="muskelaufbau", tage=3, session_min=20, equipment_ref="gym",
          trainingsjahre_ref="keine",
          kniebeugen=12, pushups=8, situps=10, burpees=5, plank=35)),

    ("06_gym_muskel_4x30_L2",  "Nina",
     dict(hauptziel_ref="muskelaufbau", tage=4, session_min=30, equipment_ref="gym",
          trainingsjahre_ref="ein_bis_zwei",
          kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80)),

    # ── Alle Ziele (4T × 45min × L2) ──────────────────────────────────────────
    ("07_gym_fettabbau_4x45_L2",  "Sarah",
     dict(hauptziel_ref="fettabbau", tage=4, session_min=45, equipment_ref="gym",
          trainingsjahre_ref="ein_bis_zwei",
          kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80)),

    ("08_gym_recomp_4x45_L2",  "Anna",
     dict(hauptziel_ref="recomp", tage=4, session_min=45, equipment_ref="gym",
          trainingsjahre_ref="ein_bis_zwei",
          kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80)),

    ("09_gym_longevity_5x60_L2",  "Lukas",
     dict(hauptziel_ref="longevity", tage=5, session_min=60, equipment_ref="gym",
          trainingsjahre_ref="ein_bis_zwei",
          kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80)),

    ("10_gym_longevity_3x30_L1",  "Hans",
     dict(hauptziel_ref="longevity", tage=3, session_min=30, equipment_ref="gym",
          trainingsjahre_ref="keine",
          kniebeugen=12, pushups=8, situps=10, burpees=5, plank=35)),

    # ── Equipment-Pfade ────────────────────────────────────────────────────────
    ("11_homegym_muskel_4x60_L2",  "Marc",
     dict(hauptziel_ref="muskelaufbau", tage=4, session_min=60, equipment_ref="home_gym",
          trainingsjahre_ref="ein_bis_zwei",
          kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80)),

    ("12_kettlebell_fettabbau_3x45_L2",  "Lisa",
     dict(hauptziel_ref="fettabbau", tage=3, session_min=45, equipment_ref="kettlebell",
          trainingsjahre_ref="ein_bis_zwei",
          kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80)),

    ("13_bodyweight_muskel_3x45_L1",  "Tom",
     dict(hauptziel_ref="muskelaufbau", tage=3, session_min=45, equipment_ref="bodyweight",
          trainingsjahre_ref="keine",
          kniebeugen=12, pushups=8, situps=10, burpees=5, plank=35)),

    ("14_travel_longevity_3x30_L1",  "Petra",
     dict(hauptziel_ref="longevity", tage=3, session_min=30, equipment_ref="travel",
          trainingsjahre_ref="keine",
          kniebeugen=12, pushups=8, situps=10, burpees=5, plank=35)),

    # ── Sonderfälle ────────────────────────────────────────────────────────────
    ("15_gym_muskel_4x60_L2_schulter",  "Klaus",
     dict(hauptziel_ref="muskelaufbau", tage=4, session_min=60, equipment_ref="gym",
          trainingsjahre_ref="ein_bis_zwei",
          kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80,
          verletzungen_labels=["schulter"])),

    ("16_gym_muskel_4x60_L2_stress",  "Bernd",
     dict(hauptziel_ref="muskelaufbau", tage=4, session_min=60, equipment_ref="gym",
          trainingsjahre_ref="ein_bis_zwei",
          kniebeugen=35, pushups=20, situps=35, burpees=20, plank=80,
          stress=9, schlaf="5")),

    # MVP-7 Naht 2c: L4-Fettabbau (6T) → Trivial-Pick = Tabata → Block-Stapelung im PDF sichtbar
    ("17_gym_fettabbau_6x60_L4_tabata",  "Nina",
     dict(hauptziel_ref="fettabbau", tage=6, session_min=60, equipment_ref="gym",
          trainingsjahre_ref="fuenf_plus",
          kniebeugen=80, pushups=60, situps=75, burpees=40, plank=200)),
]


# ── Runner ─────────────────────────────────────────────────────────────────────

def generate_one(slug: str, vorname: str, kwargs: dict, out_dir: pathlib.Path) -> str:
    payload = make_payload(vorname=vorname, **kwargs)
    klient  = parse_typeform_payload(payload)
    level, _ = berechne_level(klient)
    split    = waehle_split(klient, level)
    uebungen = filtere_uebungen(klient, level)

    claude_out = _auto_claude_output(split, uebungen)
    plan = assemble_plan(klient=klient, level=level, split=split,
                         claude_output=claude_out, block_nummer=1)

    plan_data = plan.model_dump()
    plan_data["vorname"] = vorname

    pdf = build_pdf(plan_data)
    pdf_path = out_dir / f"{slug}.pdf"
    pdf.output(str(pdf_path))

    snap = plan.klient_snapshot
    return (f"L{level} | {snap.split_typ:<35} | "
            f"{klient.tage_pro_woche}×{klient.session_dauer_min}min")


def main():
    out_dir = pathlib.Path(__file__).parent.parent / "output" / "test_plans"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'='*70}")
    print(f"TEST-PLAN GENERATOR — {len(TEST_CASES)} Pfade")
    print(f"Output: {out_dir}")
    print(f"{'='*70}")

    passed = failed = 0
    for slug, vorname, kwargs in TEST_CASES:
        try:
            detail = generate_one(slug, vorname, kwargs, out_dir)
            print(f"  ✅ {slug:<42}  {detail}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {slug:<42}  {type(e).__name__}: {e}")
            failed += 1

    print(f"{'='*70}")
    print(f"  {passed}/{passed+failed} PDFs generiert → {out_dir}")


if __name__ == "__main__":
    main()
