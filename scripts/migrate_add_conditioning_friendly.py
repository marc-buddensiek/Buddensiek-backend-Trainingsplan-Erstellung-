"""
MVP-7 Naht 1 — Schema-Enabler für data/exercises.json (einmalig, idempotent).

Ergänzt je Eintrag das neue Feld:
  - conditioning_friendly: false  (bool, default false; "darf in den Metcon-Pool")

Nur additiv — kein bestehendes Feld wird verändert. Das neue Feld ist zunächst
dormant (kein Konsument liest es; der Metcon-Selektor zieht es erst in MVP-7 Naht 4).
Das neue pattern "conditioning" (Gruppe A) wird NICHT hier gesetzt — es entsteht beim
Coach-Tagging der net-new Übungen; dieses Skript berührt nur die bestehenden 125.

Sicherheit: Idempotenz-Check, Verifikation komplett VOR dem Schreiben,
Backup nach exercises.json.bak. Schlägt eine Prüfung fehl, bleibt das
Original unangetastet (Exit 1).

Aufruf: python3 scripts/migrate_add_conditioning_friendly.py
"""
import json
import pathlib
import shutil
import sys

DATA = pathlib.Path(__file__).parent.parent / "data" / "exercises.json"
BACKUP = DATA.with_name("exercises.json.bak")

EXPECTED_COUNT = 125


def migrate_exercise(ex: dict) -> dict:
    """Kopiert den Eintrag unverändert und hängt conditioning_friendly=False an."""
    neu = dict(ex)                      # Key-Reihenfolge erhalten
    neu["conditioning_friendly"] = False
    return neu


def verify(alt: list[dict], neu: list[dict]) -> list[str]:
    """Alle Prüfungen in-memory, vor jedem Schreiben. Liefert Fehlerliste."""
    fehler = []

    if not (len(alt) == len(neu) == EXPECTED_COUNT):
        fehler.append(
            f"Eintragszahl: vorher={len(alt)} nachher={len(neu)} erwartet={EXPECTED_COUNT}"
        )
        return fehler

    for ex_alt, ex_neu in zip(alt, neu):
        eid = ex_alt["id"]
        if ex_neu.get("conditioning_friendly") is not False:
            fehler.append(f"{eid}: conditioning_friendly != False")
        # Additiv: jedes Alt-Feld muss unverändert erhalten sein
        for key, val in ex_alt.items():
            if ex_neu.get(key) != val:
                fehler.append(f"{eid}: Alt-Feld '{key}' verändert")
        # Genau ein neues Feld dazu, sonst nichts
        neue_keys = set(ex_neu) - set(ex_alt)
        if neue_keys != {"conditioning_friendly"}:
            fehler.append(f"{eid}: unerwartete neue Keys: {sorted(neue_keys)}")

    return fehler


def main() -> int:
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    alt = data["exercises"]

    # Idempotenz: schon migriert? → nichts tun
    if any("conditioning_friendly" in ex for ex in alt):
        print("bereits migriert — nichts zu tun (conditioning_friendly existiert bereits).")
        return 0

    neu = [migrate_exercise(ex) for ex in alt]

    fehler = verify(alt, neu)
    if fehler:
        print(f"VERIFIKATION FEHLGESCHLAGEN ({len(fehler)} Fehler) — NICHTS geschrieben:")
        for f_ in fehler:
            print(" -", f_)
        return 1

    shutil.copy2(DATA, BACKUP)
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump({"exercises": neu}, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Migration OK: {len(neu)} Einträge, conditioning_friendly=false ergänzt. Backup: {BACKUP.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
