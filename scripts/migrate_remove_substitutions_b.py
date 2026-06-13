"""
MVP-5 Naht 3: substitutions_b aus data/exercises.json entfernen (einmalig, idempotent).

Das Feld ist leserlos: der letzte Konsument (verletzungs_flag in equipment_filter →
Prompt-Hinweis) wurde durch den 2-Stufen-Filter abgelöst; die Ersatz-IDs sind seit der
MVP-2-Migration vollständig im substitution_pool konserviert (wird hier verifiziert).

Sicherheit wie migrate_schema_mvp2.py: Idempotenz-Check, Verifikation VOR dem
Schreiben, Backup nach exercises.json.bak. Fehler → nichts geschrieben, Exit 1.

Aufruf: python3 scripts/migrate_remove_substitutions_b.py
"""
import json
import pathlib
import shutil
import sys

DATA = pathlib.Path(__file__).parent.parent / "data" / "exercises.json"
BACKUP = DATA.with_name("exercises.json.bak")

EXPECTED_COUNT = 125


def main() -> int:
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    exs = data["exercises"]

    if not any("substitutions_b" in ex for ex in exs):
        print("bereits migriert — nichts zu tun (substitutions_b existiert nicht mehr).")
        return 0

    fehler = []
    if len(exs) != EXPECTED_COUNT:
        fehler.append(f"Eintragszahl {len(exs)} != {EXPECTED_COUNT}")
    for ex in exs:
        subs_b = ex.get("substitutions_b", {})
        fehlend = [ziel for ziel in subs_b.values() if ziel not in ex.get("substitution_pool", [])]
        if fehlend:
            fehler.append(f"{ex['id']}: subs_b-Werte fehlen im substitution_pool: {fehlend}")

    if fehler:
        print(f"VERIFIKATION FEHLGESCHLAGEN ({len(fehler)} Fehler) — NICHTS geschrieben:")
        for f_ in fehler:
            print(" -", f_)
        return 1

    for ex in exs:
        ex.pop("substitutions_b", None)

    shutil.copy2(DATA, BACKUP)
    with open(DATA, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Migration OK: substitutions_b aus {len(exs)} Einträgen entfernt "
          f"(Werte im substitution_pool verifiziert), Backup: {BACKUP.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
