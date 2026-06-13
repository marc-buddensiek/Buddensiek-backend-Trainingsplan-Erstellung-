"""
Dauervalidierung für data/exercises.json (Schema + Tagging-Fortschritt, MVP-2+).

Prüft gegen SCHEMA.md:
  - Vokabular: pattern (9), joint_stress (8, englisch), impact_level (low/medium/high
    oder null = ungetaggt), equipment (6 Pfade), skill_level 1-4
  - Struktur: muscle_groups nested {primary, secondary}, Pflichtfelder, eindeutige IDs
  - ID-Referenzen: substitution_pool, progressions_up/down
  - substitutions_b darf nicht mehr existieren (entfernt MVP-5 Naht 3)
  - Tagging-Konsistenz: joint_stress gesetzt aber impact_level null = halb getaggt → Fehler
  - Fortschritt: getaggt := impact_level != null (Fertig-Marker, siehe SCHEMA.md Abschn. 2)

Ersetzt die Validierung im schema-stalen update_exercises.py; dient auch dem
Bibliotheks-Ausbau (250-300) und später dem V1.5-Backoffice ("Neue Übung anlegen").

Aufruf: python3 scripts/validate_exercises.py   (Exit 0 = ok, 1 = Fehler)
"""
import json
import pathlib
import sys

DATA = pathlib.Path(__file__).parent.parent / "data" / "exercises.json"

PATTERNS = {
    "squat", "hinge", "single_leg", "push_horizontal", "push_vertical",
    "pull_horizontal", "pull_vertical", "core", "carry",
}
JOINTS = {"knee", "shoulder", "spine", "hip", "elbow", "wrist", "neck", "ankle"}
IMPACT = {"low", "medium", "high"}
EQUIPMENT = {"gym", "home_gym", "kettlebell", "bodyweight", "travel", "hybrid"}
PFLICHTFELDER = [
    "id", "name", "equipment", "pattern", "muscle_groups", "skill_level",
    "coaching_cues", "substitution_pool",
    "progressions_up", "progressions_down", "pattern_tags",
    "joint_stress", "impact_level", "equipment_requires",
]


def main() -> int:
    with open(DATA, encoding="utf-8") as f:
        exs = json.load(f)["exercises"]

    fehler: list[str] = []
    ids = [ex.get("id") for ex in exs]
    all_ids = set(ids)
    if len(all_ids) != len(ids):
        dupes = {i for i in ids if ids.count(i) > 1}
        fehler.append(f"doppelte IDs: {sorted(dupes)}")

    for ex in exs:
        eid = ex.get("id", "<ohne id>")

        for feld in PFLICHTFELDER:
            if feld not in ex:
                fehler.append(f"{eid}: Pflichtfeld fehlt: {feld}")

        if ex.get("pattern") not in PATTERNS:
            fehler.append(f"{eid}: ungültiges pattern: {ex.get('pattern')!r}")
        if not isinstance(ex.get("skill_level"), int) or not 1 <= ex["skill_level"] <= 4:
            fehler.append(f"{eid}: skill_level nicht int 1-4: {ex.get('skill_level')!r}")

        bad_eq = set(ex.get("equipment", [])) - EQUIPMENT
        if bad_eq:
            fehler.append(f"{eid}: ungültiges equipment: {sorted(bad_eq)}")

        mg = ex.get("muscle_groups")
        if not (isinstance(mg, dict)
                and isinstance(mg.get("primary"), list)
                and isinstance(mg.get("secondary"), list)):
            fehler.append(f"{eid}: muscle_groups nicht nested {{primary:[], secondary:[]}}")

        js = ex.get("joint_stress")
        if not isinstance(js, list):
            fehler.append(f"{eid}: joint_stress keine Liste: {js!r}")
        else:
            bad_js = set(js) - JOINTS
            if bad_js:
                fehler.append(f"{eid}: ungültige joint_stress-Werte: {sorted(bad_js)} "
                              f"(erlaubt: {sorted(JOINTS)})")

        il = ex.get("impact_level")
        if il is not None and il not in IMPACT:
            fehler.append(f"{eid}: ungültiges impact_level: {il!r} (erlaubt: low/medium/high/null)")
        if isinstance(js, list) and js and il is None:
            fehler.append(f"{eid}: halb getaggt — joint_stress gesetzt, impact_level null")

        if not isinstance(ex.get("equipment_requires"), list):
            fehler.append(f"{eid}: equipment_requires keine Liste")

        if "substitutions_b" in ex:
            fehler.append(f"{eid}: substitutions_b sollte entfernt sein (MVP-5 Naht 3)")

        for feld in ("substitution_pool", "progressions_up", "progressions_down"):
            for ref in ex.get(feld, []):
                if ref not in all_ids:
                    fehler.append(f"{eid}.{feld} → fehlende ID: {ref}")

    getaggt = sum(1 for ex in exs if ex.get("impact_level") is not None)
    print(f"{len(exs)} Übungen · Tagging-Fortschritt: {getaggt}/{len(exs)} "
          f"(Marker: impact_level != null)")

    if fehler:
        print(f"\n{len(fehler)} FEHLER:")
        for f_ in fehler:
            print(" -", f_)
        return 1
    print("Validierung OK — Schema, Vokabular und Referenzen sauber.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
