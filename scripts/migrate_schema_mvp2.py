"""
MVP-2 Schema-Migration für data/exercises.json (einmalig, idempotent).

Transformation je Eintrag (siehe SCHEMA.md):
  - level_min            → skill_level (Rename in Position, Werte unverändert)
  - substitutions_a      → substitution_pool (in Position):
                           dedup(subs_a + subs_b.values()), Reihenfolge erhalten
  - substitutions_b      blieb hier unverändert (lebender Leser bis MVP-5;
                           inzwischen entfernt, s. migrate_remove_substitutions_b.py)
  - joint_stress: []     neu (leer = ungetaggt)
  - impact_level: null   neu (null = ungetaggt, bewusst NICHT "low")
  - equipment_requires: [] neu (dormant, Leser equipment_filter nutzt .get-Default)

Sicherheit: Idempotenz-Check, Verifikation komplett VOR dem Schreiben,
Backup nach exercises.json.bak. Schlägt eine Prüfung fehl, bleibt das
Original unangetastet (Exit 1).

Aufruf: python3 scripts/migrate_schema_mvp2.py
"""
import json
import pathlib
import shutil
import sys

DATA = pathlib.Path(__file__).parent.parent / "data" / "exercises.json"
BACKUP = DATA.with_name("exercises.json.bak")

EXPECTED_COUNT = 125


def migrate_exercise(ex: dict) -> dict:
    """Baut den migrierten Eintrag, Key-Reihenfolge des Originals erhalten."""
    subs_a = ex["substitutions_a"]
    subs_b = ex["substitutions_b"]
    pool = list(dict.fromkeys(subs_a + list(subs_b.values())))

    neu = {}
    for key, value in ex.items():
        if key == "level_min":
            neu["skill_level"] = value
        elif key == "substitutions_a":
            neu["substitution_pool"] = pool
        else:
            neu[key] = value

    neu["joint_stress"] = []
    neu["impact_level"] = None
    neu["equipment_requires"] = []
    return neu


def verify(alt: list[dict], neu: list[dict]) -> list[str]:
    """Alle Prüfungen in-memory, vor jedem Schreiben. Liefert Fehlerliste."""
    fehler = []

    if not (len(alt) == len(neu) == EXPECTED_COUNT):
        fehler.append(
            f"Eintragszahl: vorher={len(alt)} nachher={len(neu)} erwartet={EXPECTED_COUNT}"
        )
        return fehler  # paarweise Checks unten wären sinnlos

    for ex_alt, ex_neu in zip(alt, neu):
        eid = ex_alt["id"]
        subs_a = ex_alt["substitutions_a"]
        subs_b = ex_alt["substitutions_b"]
        pool = ex_neu.get("substitution_pool")

        if "equipment_requires" not in ex_neu:
            fehler.append(f"{eid}: equipment_requires fehlt")
        if "level_min" in ex_neu or "substitutions_a" in ex_neu:
            fehler.append(f"{eid}: Alt-Feld (level_min/substitutions_a) noch vorhanden")
        if ex_neu.get("skill_level") != ex_alt["level_min"]:
            fehler.append(f"{eid}: skill_level != level_min (Wert verändert)")
        if ex_neu.get("substitutions_b") != subs_b:
            fehler.append(f"{eid}: substitutions_b verändert")

        if pool is None:
            fehler.append(f"{eid}: substitution_pool fehlt")
            continue
        if len(pool) < len(subs_a):
            fehler.append(f"{eid}: Pool-Verlust (len {len(pool)} < subs_a {len(subs_a)})")
        if not set(pool) >= set(subs_a) | set(subs_b.values()):
            fehler.append(f"{eid}: Pool ist keine Obermenge von subs_a ∪ subs_b.values()")
        if pool[: len(subs_a)] != subs_a and len(set(subs_a)) == len(subs_a):
            fehler.append(f"{eid}: Pool beginnt nicht mit subs_a (Reihenfolge)")

    return fehler


def main() -> int:
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    alt = data["exercises"]

    # Idempotenz: schon migriert? → nichts tun
    if any("skill_level" in ex for ex in alt):
        print("bereits migriert — nichts zu tun (skill_level existiert bereits).")
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

    print(f"Migration OK: {len(neu)} Einträge geschrieben, Backup: {BACKUP.name}")
    print("  level_min→skill_level, substitution_pool angelegt, substitutions_a entfernt,")
    print("  joint_stress=[] / impact_level=null / equipment_requires=[] ergänzt,")
    print("  substitutions_b unverändert erhalten.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
