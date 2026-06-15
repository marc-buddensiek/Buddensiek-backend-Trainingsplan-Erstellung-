"""
MVP-7 — Conditioning- + Athletik-Übungen anlegen (einmalig, idempotent).

Fügt 35 neue Übungen hinzu (Gruppe A: pattern "conditioning" · Gruppe B:
conditioning_friendly · Athletik) und korrigiert die 6 mis-filed (conditioning_friendly,
pattern_tags). Coach-abgenommene Tags (2026-06-15).

Sicherheit: Idempotenz-Check, Verifikation komplett VOR dem Schreiben, Backup nach
exercises.json.bak. Validator (validate_exercises.py) ist die fachliche Gate danach.

Aufruf: python3 scripts/migrate_add_conditioning_athletik.py
"""
import json
import pathlib
import shutil
import sys

DATA = pathlib.Path(__file__).parent.parent / "data" / "exercises.json"
BACKUP = DATA.with_name("exercises.json.bak")

# Equipment-Listen
BW   = ["bodyweight", "gym", "home_gym", "travel", "hybrid", "kettlebell"]
KB   = ["kettlebell", "hybrid"]
DB   = ["gym", "home_gym", "hybrid"]
BB   = ["gym"]
GH   = ["gym", "home_gym"]
AIR  = ["gym", "home_gym", "hybrid"]
BOX  = ["gym", "home_gym", "hybrid"]
BWT  = ["bodyweight", "travel"]


def ex(id, name, equipment, pattern, skill, impact, js, primary, secondary, cf, cues, subs, ptags=None):
    """Baut einen Eintrag mit der Feld-Reihenfolge der bestehenden 125."""
    return {
        "id": id, "name": name, "equipment": equipment, "pattern": pattern,
        "muscle_groups": {"primary": primary, "secondary": secondary},
        "skill_level": skill, "coaching_cues": cues, "substitution_pool": subs,
        "progressions_up": [], "progressions_down": [], "pattern_tags": ptags or [],
        "joint_stress": js, "impact_level": impact, "equipment_requires": [],
        "conditioning_friendly": cf,
    }


NEW_EXERCISES = [
    # ── Gruppe A — pattern "conditioning" (kein Kraft-Pattern, muscle_groups leer) ──
    ex("cond_air_bike", "Assault/Air Bike", AIR, "conditioning", 1, "low", [], [], [], False,
       ["Arme und Beine gleichmäßig im Rhythmus", "Tempo über die volle Intervalldauer halten"],
       ["cond_row_erg", "cond_ski_erg"]),
    ex("cond_row_erg", "Rudergerät (Erg)", GH, "conditioning", 1, "low", ["spine"], [], [], False,
       ["Reihenfolge Beine–Hüfte–Arme", "Rücken neutral, nicht rund ziehen"],
       ["cond_air_bike", "cond_ski_erg"]),
    ex("cond_ski_erg", "Ski-Ergometer", GH, "conditioning", 2, "low", [], [], [], False,
       ["Aus der Hüfte arbeiten", "Arme kräftig nach unten ziehen"],
       ["cond_air_bike", "cond_row_erg"]),
    ex("cond_battle_ropes", "Battle Ropes", GH, "conditioning", 1, "low", ["shoulder"], [], [], False,
       ["Wellen aus den Schultern", "Leichte Kniebeuge halten"],
       ["cond_air_bike"]),
    ex("cond_sled_push", "Sled Push (Prowler)", BB, "conditioning", 1, "low", [], [], [], False,
       ["Tiefer Körperwinkel, Arme gestreckt", "Kurze, kräftige Schritte"],
       ["cond_sled_drag"]),
    ex("cond_sled_drag", "Sled Drag/Pull", BB, "conditioning", 1, "low", [], [], [], False,
       ["Knie gebeugt, gleichmäßig ziehen", "Rumpf stabil halten"],
       ["cond_sled_push"]),
    ex("cond_jump_rope", "Springseil", ["bodyweight", "travel", "home_gym", "gym", "hybrid"],
       "conditioning", 2, "medium", ["ankle"], [], [], False,
       ["Aus den Fußgelenken springen, flach", "Handgelenke drehen, nicht die Arme"],
       ["cond_jumping_jacks", "cond_high_knees"]),
    ex("cond_jumping_jacks", "Jumping Jacks", BWT, "conditioning", 1, "low", [], [], [], False,
       ["Arme über Kopf, Beine seitlich", "Weich landen"],
       ["cond_high_knees", "cond_jump_rope"]),
    ex("cond_high_knees", "High Knees", BWT, "conditioning", 1, "low", [], [], [], False,
       ["Knie auf Hüfthöhe", "Schneller Vorfuß-Kontakt"],
       ["cond_jumping_jacks", "cond_shuttle_run"]),
    ex("cond_shuttle_run", "Shuttle Run / Pendellauf", BWT, "conditioning", 1, "medium",
       ["knee", "ankle"], [], [], False,
       ["Tief abbremsen, Knie über dem Fuß", "Explosiv aus der Wende"],
       ["cond_high_knees", "cond_sprint_intervals"]),
    ex("cond_sprint_intervals", "Sprint-Intervalle", BWT, "conditioning", 2, "high",
       ["knee", "ankle"], [], [], False,
       ["Aufrechter Sprint, hohe Frequenz", "Vollständige Pausen zwischen Sprints"],
       ["cond_shuttle_run", "cond_high_knees"]),

    # ── Gruppe B — conditioning_friendly (echtes Kraft-Pattern, metcon-tauglich) ──
    ex("bw_burpee", "Burpee", BW, "push_horizontal", 2, "high", ["shoulder", "wrist"],
       ["chest", "quads"], ["shoulders", "triceps", "abs"], True,
       ["Brust zum Boden, dann explosiv hoch", "Hüfte mitnehmen, nicht durchhängen"],
       ["bw_squat_thrust", "bw_mountain_climber"]),
    ex("bw_mountain_climber", "Mountain Climbers", BW, "core", 1, "low", ["shoulder", "wrist"],
       ["abs"], ["hip_flexors", "shoulders"], True,
       ["Hüfte tief, Rücken flach", "Knie schnell zur Brust"],
       ["bw_bear_crawl", "bw_crab_walk"]),
    ex("bw_bear_crawl", "Bear Crawl", BW, "core", 2, "low", ["shoulder", "wrist"],
       ["abs"], ["shoulders", "quads"], True,
       ["Knie knapp über dem Boden", "Gegengleich Arm und Bein"],
       ["bw_crab_walk", "bw_mountain_climber"]),
    ex("bw_crab_walk", "Crab Walk", BW, "core", 1, "low", ["shoulder", "wrist"],
       ["abs"], ["glutes", "triceps"], True,
       ["Hüfte hoch halten", "Kontrolliert gegengleich gehen"],
       ["bw_bear_crawl"]),
    ex("bw_inchworm", "Inchworm / Walkout", BW, "core", 1, "low", ["shoulder", "wrist"],
       ["abs"], ["chest", "shoulders"], True,
       ["Beine gestreckt, mit den Händen vorlaufen", "Rumpf fest, nicht durchhängen"],
       ["bw_mountain_climber"]),
    ex("bw_pushup_conditioning", "Push-Up (Conditioning)", BW, "push_horizontal", 1, "low",
       ["shoulder", "wrist", "elbow"], ["chest"], ["triceps", "shoulders"], True,
       ["Körper in einer Linie", "Ellbogen ~45° am Körper"],
       ["bw_squat_thrust"]),
    ex("bw_squat_thrust", "Squat Thrust (Burpee ohne Sprung)", BW, "push_horizontal", 1, "low",
       ["shoulder", "wrist"], ["quads", "chest"], ["shoulders"], True,
       ["Hände am Boden, Beine zurück und vor", "Rumpf stabil"],
       ["bw_burpee", "bw_mountain_climber"]),
    ex("kb_thruster", "Kettlebell Thruster", KB, "push_vertical", 3, "low", ["shoulder", "knee"],
       ["quads", "shoulders"], ["glutes", "triceps"], True,
       ["Aus der Hocke explosiv über Kopf", "Bizeps am Ohr oben"],
       ["db_thruster", "kb_push_press"]),
    ex("db_thruster", "Dumbbell Thruster", DB, "push_vertical", 3, "low", ["shoulder", "knee"],
       ["quads", "shoulders"], ["glutes", "triceps"], True,
       ["Tiefe Hocke, dann drücken", "Kurzhanteln über der Schulter ablegen"],
       ["kb_thruster", "wall_ball"]),
    ex("bb_thruster", "Barbell Thruster", BB, "push_vertical", 4, "low",
       ["shoulder", "knee", "wrist"], ["quads", "shoulders"], ["glutes", "triceps"], True,
       ["Front Squat in den Press übergehen", "Stange dicht über Kopf"],
       ["db_thruster", "kb_thruster"]),
    ex("kb_high_pull", "Kettlebell High Pull", KB, "hinge", 3, "medium", ["shoulder", "spine"],
       ["hamstrings", "glutes"], ["shoulders", "back_upper"], True,
       ["Aus der Hüfte beschleunigen", "Ellbogen führt nach oben"],
       ["kb_swing_two_hand"]),
    ex("kb_clean_and_press", "KB Clean & Press", KB, "hinge", 3, "medium", ["shoulder", "spine"],
       ["glutes", "shoulders"], ["hamstrings", "triceps"], True,
       ["Sauber in Racking-Position", "Dann kontrolliert drücken"],
       ["kb_clean", "kb_push_press"]),
    ex("wall_ball", "Wall Ball Shot", GH, "push_vertical", 2, "medium", ["shoulder", "knee"],
       ["quads", "shoulders"], ["glutes"], True,
       ["Aus der Hocke an die Wand werfen", "Ball weich fangen, direkt tief"],
       ["db_thruster", "kb_goblet_squat"]),

    # ── Athletik — Kraft-Pattern + conditioning_friendly + pattern_tags ──
    ex("ath_box_jump", "Box Jump", BOX, "squat", 2, "high", ["knee", "ankle"],
       ["quads", "glutes"], ["calves"], True,
       ["Arme mitschwingen, weich landen", "Volle Hüftstreckung oben"],
       ["ath_broad_jump", "bw_jump_squat"], ["athletik", "jump"]),
    ex("ath_broad_jump", "Broad Jump", BW, "squat", 2, "high", ["knee", "ankle"],
       ["quads", "glutes"], ["hamstrings"], True,
       ["Weit nach vorn, Arme führen", "Weich auf beiden Füßen landen"],
       ["ath_box_jump", "bw_jump_squat"], ["athletik", "jump"]),
    ex("ath_tuck_jump", "Tuck Jump", BW, "squat", 3, "high", ["knee", "ankle"],
       ["quads"], ["calves", "abs"], True,
       ["Knie zur Brust ziehen", "Sofort weich abfedern"],
       ["bw_jump_squat", "ath_box_jump"], ["athletik", "jump"]),
    ex("ath_depth_jump", "Depth Jump", GH, "squat", 4, "high", ["knee", "ankle"],
       ["quads"], ["calves"], True,
       ["Von der Box abspringen, kurzer Bodenkontakt", "Sofort maximal hoch"],
       ["ath_box_jump", "ath_tuck_jump"], ["athletik", "jump"]),
    ex("ath_lateral_bound", "Lateral Bound", BW, "single_leg", 3, "high", ["knee", "ankle"],
       ["glutes", "quads"], ["hip_adductors"], True,
       ["Seitlich abdrücken, einbeinig landen", "Landung kontrolliert abfangen"],
       ["bw_skater_squat"], ["athletik", "jump"]),
    ex("ath_pogo_hops", "Pogo Hops", BW, "squat", 2, "high", ["ankle"],
       ["calves"], ["quads"], True,
       ["Steife Knöchel, kurze Bodenkontakte", "Aus den Waden federn"],
       ["cond_jump_rope", "bw_jump_squat"], ["athletik", "jump"]),
    ex("ath_med_ball_slam", "Med Ball Slam", GH, "core", 1, "low", ["shoulder", "spine"],
       ["abs", "shoulders"], ["back_lat"], True,
       ["Über Kopf, dann mit ganzem Körper schmettern", "Rumpf fest"],
       ["ath_med_ball_rotational_throw"], ["athletik"]),
    ex("ath_med_ball_rotational_throw", "Med Ball Rotational Throw", GH, "core", 2, "low",
       ["spine", "shoulder"], ["obliques"], ["abs", "shoulders"], True,
       ["Rotation aus der Hüfte", "Explosiv gegen die Wand"],
       ["ath_med_ball_slam"], ["athletik"]),
    ex("ath_med_ball_chest_pass", "Med Ball Chest Pass", GH, "push_horizontal", 1, "low",
       ["shoulder", "elbow"], ["chest"], ["triceps", "shoulders"], True,
       ["Explosiv von der Brust wegdrücken", "Stand stabil"],
       ["bw_pushup_conditioning"], ["athletik"]),
]

# mis-filed + bereits vorhandene Conditioning-Kandidaten: Pattern bleibt, conditioning_friendly:true;
# Jump Squat/Skater zusätzlich Athletik-Tag. (kb_push_press + kb_goblet_squat existierten schon →
# gepatcht statt dupliziert.)
MISFILED = {
    "kb_swing_two_hand": {"conditioning_friendly": True},
    "kb_swing_one_hand": {"conditioning_friendly": True},
    "kb_snatch":         {"conditioning_friendly": True},
    "kb_clean":          {"conditioning_friendly": True},
    "kb_push_press":     {"conditioning_friendly": True},
    "kb_goblet_squat":   {"conditioning_friendly": True},
    "bw_jump_squat":     {"conditioning_friendly": True, "pattern_tags_add": ["athletik", "jump"]},
    "bw_skater_squat":   {"conditioning_friendly": True, "pattern_tags_add": ["athletik"]},
}

_SENTINEL_ID = "cond_air_bike"


def verify(alt: list[dict], neu: list[dict]) -> list[str]:
    fehler = []
    all_ids = {e["id"] for e in neu}

    if len(neu) != len(alt) + len(NEW_EXERCISES):
        fehler.append(f"Eintragszahl: {len(alt)} + {len(NEW_EXERCISES)} != {len(neu)}")

    # Eindeutige IDs
    ids = [e["id"] for e in neu]
    if len(set(ids)) != len(ids):
        fehler.append("doppelte IDs nach Migration")

    # Neue Übungen: Pflichtfelder + Referenzen + Gruppe-A-Konvention
    pflicht = {"id", "name", "equipment", "pattern", "muscle_groups", "skill_level",
               "coaching_cues", "substitution_pool", "progressions_up", "progressions_down",
               "pattern_tags", "joint_stress", "impact_level", "equipment_requires",
               "conditioning_friendly"}
    for e in NEW_EXERCISES:
        miss = pflicht - set(e)
        if miss:
            fehler.append(f"{e['id']}: Pflichtfelder fehlen: {sorted(miss)}")
        if e["pattern"] == "conditioning" and e["muscle_groups"]["primary"]:
            fehler.append(f"{e['id']}: pattern conditioning, aber muscle_groups.primary nicht leer")
        for ref in e["substitution_pool"]:
            if ref not in all_ids:
                fehler.append(f"{e['id']}.substitution_pool → fehlende ID: {ref}")

    # Mis-filed: Patch angewendet
    by_id = {e["id"]: e for e in neu}
    for mid, patch in MISFILED.items():
        if mid not in by_id:
            fehler.append(f"mis-filed {mid}: ID nicht gefunden")
            continue
        if by_id[mid].get("conditioning_friendly") is not True:
            fehler.append(f"mis-filed {mid}: conditioning_friendly != True")
        for t in patch.get("pattern_tags_add", []):
            if t not in by_id[mid]["pattern_tags"]:
                fehler.append(f"mis-filed {mid}: pattern_tag {t} fehlt")

    return fehler


def main() -> int:
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    alt = data["exercises"]

    if any(e["id"] == _SENTINEL_ID for e in alt):
        print(f"bereits migriert — nichts zu tun ({_SENTINEL_ID} existiert).")
        return 0

    # Mis-filed patchen (in-place auf Kopie)
    neu = [dict(e) for e in alt]
    by_id = {e["id"]: e for e in neu}
    for mid, patch in MISFILED.items():
        if mid in by_id:
            e = by_id[mid]
            if "conditioning_friendly" in patch:
                e["conditioning_friendly"] = patch["conditioning_friendly"]
            for t in patch.get("pattern_tags_add", []):
                if t not in e["pattern_tags"]:
                    e["pattern_tags"] = e["pattern_tags"] + [t]

    neu = neu + [dict(e) for e in NEW_EXERCISES]

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

    print(f"Migration OK: +{len(NEW_EXERCISES)} neue Übungen, {len(MISFILED)} mis-filed gepatcht. "
          f"Gesamt {len(neu)}. Backup: {BACKUP.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
