"""
Generiert einen vollständigen 4-Wochen-Plan und speichert ihn als JSON.

Verwendung:
  ANTHROPIC_API_KEY=sk-ant-... python3 scripts/generate_plan.py
  → Speichert: output/plan_<client_id>.json
"""

from __future__ import annotations
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()   # .env selbst laden — CLI läuft nicht über main.py, das sonst den Key bereitstellt

from parsers import parse_typeform_payload
from logic.level_calculator import berechne_level
from logic.volume_calculator import berechne_volumen
from logic.split_selector import waehle_split
from logic.equipment_filter import filtere_uebungen
from logic.plan_assembler import assemble_plan
from claude.claude_client import generiere_uebungsauswahl
from logging_config import setup_logging

OUTPUT_DIR = pathlib.Path(__file__).parent.parent / "output"


def main():
    setup_logging()   # damit das claude_client-Logging (ohne main) sichtbar ist
    # ── Daten laden ───────────────────────────────────────────────────────────
    payload_path = pathlib.Path(__file__).parent.parent / "data" / "fake_typeform.json"
    payload = json.loads(payload_path.read_text())
    klient = parse_typeform_payload(payload)

    # ── Berechnungen ──────────────────────────────────────────────────────────
    level, punkte = berechne_level(klient)
    woche_typ = "akkumulation"
    volumen = berechne_volumen(klient, level, woche_typ)
    split = waehle_split(klient, level)
    uebungen = filtere_uebungen(klient, level)

    print(f"Klient:  {klient.vorname}, Level {level}, {split['split_typ']}")
    print(f"Volumen: {volumen['ziel_saetze']} Sätze, RPE {volumen['ziel_rpe']}")

    # ── Claude API ────────────────────────────────────────────────────────────
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n⚠️  ANTHROPIC_API_KEY fehlt.")
        print("   export ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)

    print("\nClaude wählt Übungen aus...")
    claude_output = generiere_uebungsauswahl(
        klient=klient,
        level=level,
        split_typ=split["split_typ"],
        block_nummer=1,
        sessions=split["sessions"],
        uebungen_gefiltert=uebungen,
        woche_typ=woche_typ,
        ziel_saetze=volumen["ziel_saetze"],
        ziel_rpe=volumen["ziel_rpe"],
    )
    print(f"✓ {len(claude_output.sessions)} Sessions erhalten")

    # ── Plan zusammenbauen ────────────────────────────────────────────────────
    print("Plan wird zusammengebaut...")
    plan = assemble_plan(
        klient=klient,
        level=level,
        split=split,
        claude_output=claude_output,
        block_nummer=1,
    )

    # ── Ausgabe ───────────────────────────────────────────────────────────────
    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / f"plan_{klient.client_id[:8]}.json"
    out_path.write_text(json.dumps(plan.model_dump(), indent=2, ensure_ascii=False))
    print(f"\n✅ Plan gespeichert: {out_path}")

    # Kurzübersicht
    print(f"\n{'='*60}")
    print(f"Plan-ID:   {plan.plan_id}")
    print(f"Klient:    {klient.vorname}, Block {plan.block_nummer}")
    print(f"Split:     {plan.klient_snapshot.split_typ}")
    print()
    for woche in plan.wochen:
        print(f"  Woche {woche.woche_nummer} ({woche.block_typ.upper()}) — {woche.ziel_saetze} Sätze × RIR {woche.ziel_rir}:")
        for s in woche.sessions:
            cardio_str = f" + {s.cardio.typ.upper()} {s.cardio.dauer_min}min" if s.cardio else ""
            pst_str = " [PST RE-TEST]" if s.pst_tests else ""
            print(f"    {s.tag.capitalize():<12} {s.fokus:<35} ~{s.dauer_min_geschaetzt}min{cardio_str}{pst_str}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
