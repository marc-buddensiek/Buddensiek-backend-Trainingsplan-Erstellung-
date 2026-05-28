"""
Adds progressions_up / progressions_down to every existing exercise
and appends ~44 new exercises (L3-L4 + equipment gaps).
Run from buddensiek-backend/: python scripts/update_exercises.py
"""
import json, pathlib

DATA = pathlib.Path(__file__).parent.parent / "data" / "exercises.json"

# ── progressions for existing exercises ──────────────────────────────────────
PROGRESSIONS = {
    # SQUAT
    "gym_leg_press_machine":     {"up": ["gym_hack_squat_machine"], "down": []},
    "gym_hack_squat_machine":    {"up": ["gym_goblet_squat_db"], "down": ["gym_leg_press_machine"]},
    "gym_goblet_squat_db":       {"up": ["gym_back_squat", "gym_trap_bar_deadlift"], "down": ["bw_squat"]},
    "kb_goblet_squat":           {"up": ["kb_front_squat"], "down": ["bw_squat"]},
    "gym_box_squat":             {"up": ["gym_back_squat"], "down": ["gym_goblet_squat_db"]},
    "bw_wall_sit":               {"up": ["bw_squat"], "down": []},
    "bw_squat":                  {"up": ["bw_pause_squat", "bw_jump_squat"], "down": ["bw_wall_sit"]},
    "bw_pause_squat":            {"up": ["bw_cossack_squat", "bw_atg_split_squat"], "down": ["bw_squat"]},
    "bw_cossack_squat":          {"up": ["bw_pistol_squat"], "down": ["bw_squat"]},
    "bw_atg_split_squat":        {"up": ["bw_assisted_pistol_squat"], "down": ["bw_reverse_lunge"]},
    "gym_back_squat":            {"up": ["gym_paused_back_squat", "gym_tempo_squat"], "down": ["gym_goblet_squat_db"]},
    "gym_front_squat":           {"up": ["gym_tempo_squat"], "down": ["gym_back_squat"]},
    "bw_pistol_squat":           {"up": [], "down": ["bw_assisted_pistol_squat"]},
    # HINGE
    "bw_glute_bridge":           {"up": ["bw_single_leg_glute_bridge", "gym_hip_thrust_machine"], "down": []},
    "gym_hip_thrust_machine":    {"up": ["gym_hip_thrust_barbell"], "down": ["bw_glute_bridge"]},
    "gym_hip_thrust_barbell":    {"up": ["gym_single_leg_hip_thrust_db"], "down": ["gym_hip_thrust_machine"]},
    "gym_rdl_db":                {"up": ["gym_rdl_barbell", "bw_single_leg_rdl"], "down": ["bw_glute_bridge"]},
    "gym_rdl_barbell":           {"up": ["gym_conventional_deadlift"], "down": ["gym_rdl_db"]},
    "gym_trap_bar_deadlift":     {"up": ["gym_conventional_deadlift"], "down": ["gym_rdl_barbell"]},
    "gym_conventional_deadlift": {"up": ["gym_good_morning", "gym_glute_ham_raise"], "down": ["gym_trap_bar_deadlift"]},
    "kb_deadlift":               {"up": ["kb_swing_two_hand"], "down": ["bw_glute_bridge"]},
    "kb_swing_two_hand":         {"up": ["kb_swing_one_hand"], "down": ["kb_deadlift"]},
    "kb_swing_one_hand":         {"up": ["kb_snatch"], "down": ["kb_swing_two_hand"]},
    "kb_snatch":                 {"up": [], "down": ["kb_swing_one_hand"]},
    "kb_clean":                  {"up": ["kb_snatch"], "down": ["kb_swing_two_hand"]},
    "bw_single_leg_rdl":         {"up": ["gym_single_leg_rdl_db"], "down": ["bw_glute_bridge"]},
    "gym_single_leg_rdl_db":     {"up": [], "down": ["bw_single_leg_rdl"]},
    # PUSH HORIZONTAL
    "gym_machine_chest_press":   {"up": ["gym_db_bench_press"], "down": ["bw_incline_pushup"]},
    "gym_db_floor_press":        {"up": ["gym_db_bench_press"], "down": ["bw_pushup"]},
    "gym_db_bench_press":        {"up": ["gym_bench_press"], "down": ["gym_db_floor_press"]},
    "gym_incline_db_press":      {"up": ["gym_bench_press"], "down": ["gym_db_bench_press"]},
    "gym_bench_press":           {"up": ["gym_weighted_dips", "gym_close_grip_bench"], "down": ["gym_db_bench_press"]},
    "gym_cable_fly":             {"up": [], "down": ["gym_machine_chest_press"]},
    "bw_pushup":                 {"up": ["bw_diamond_pushup", "bw_decline_pushup"], "down": ["bw_incline_pushup"]},
    "bw_archer_pushup":          {"up": ["bw_one_arm_pushup_negatives"], "down": ["bw_pushup"]},
    # PUSH VERTICAL
    "gym_landmine_ohp":          {"up": ["gym_db_shoulder_press"], "down": []},
    "gym_db_shoulder_press":     {"up": ["gym_ohp_barbell", "gym_push_press_barbell"], "down": ["gym_landmine_ohp"]},
    "gym_ohp_barbell":           {"up": ["gym_z_press"], "down": ["gym_db_shoulder_press"]},
    "kb_single_press":           {"up": ["kb_push_press"], "down": ["gym_db_shoulder_press"]},
    "kb_bottoms_up_press":       {"up": [], "down": ["kb_single_press"]},
    "gym_face_pull":             {"up": [], "down": []},
    "gym_cuban_press":           {"up": [], "down": []},
    "gym_cable_lateral_raise":   {"up": [], "down": []},
    "gym_db_lateral_raise":      {"up": [], "down": []},
    # PULL VERTICAL
    "bw_ring_row":               {"up": ["bw_negative_pullup"], "down": []},
    "gym_lat_pulldown":          {"up": ["gym_chinup"], "down": ["bw_ring_row"]},
    "gym_close_grip_pulldown":   {"up": ["gym_chinup"], "down": ["gym_lat_pulldown"]},
    "gym_chinup":                {"up": ["gym_pullup"], "down": ["gym_lat_pulldown"]},
    "gym_pullup":                {"up": ["gym_weighted_pullup"], "down": ["gym_chinup"]},
    "gym_cable_pullover":        {"up": [], "down": []},
    # PULL HORIZONTAL
    "gym_band_pull_apart":       {"up": [], "down": []},
    "kb_row":                    {"up": ["gym_db_row"], "down": ["bw_inverted_row"]},
    "kb_renegade_row":           {"up": [], "down": ["kb_row"]},
    "gym_db_row":                {"up": ["gym_barbell_row", "gym_chest_supported_db_row"], "down": ["bw_inverted_row"]},
    "gym_seated_cable_row":      {"up": ["gym_barbell_row"], "down": ["gym_db_row"]},
    "gym_barbell_row":           {"up": [], "down": ["gym_db_row"]},
    # SINGLE LEG
    "bw_reverse_lunge":          {"up": ["bw_bulgarian_split_squat", "gym_step_up_db"], "down": ["bw_squat"]},
    "gym_step_up_db":            {"up": ["gym_bulgarian_split_squat_db"], "down": ["bw_reverse_lunge"]},
    "kb_reverse_lunge":          {"up": ["kb_bulgarian_split_squat"], "down": ["bw_reverse_lunge"]},
    "bw_bulgarian_split_squat":  {"up": ["gym_bulgarian_split_squat_db", "bw_atg_split_squat"], "down": ["bw_reverse_lunge"]},
    "gym_bulgarian_split_squat_db": {"up": ["bw_skater_squat", "bw_assisted_pistol_squat"], "down": ["bw_bulgarian_split_squat"]},
    "kb_bulgarian_split_squat":  {"up": ["bw_skater_squat"], "down": ["kb_reverse_lunge"]},
    # CARRY
    "gym_farmers_carry_db":      {"up": ["gym_suitcase_carry_db", "gym_overhead_carry_db"], "down": []},
    "gym_suitcase_carry_db":     {"up": ["gym_overhead_carry_db"], "down": ["gym_farmers_carry_db"]},
    "gym_overhead_carry_db":     {"up": ["gym_barbell_overhead_carry"], "down": ["gym_suitcase_carry_db"]},
    "kb_farmers_carry":          {"up": ["kb_rack_walk"], "down": []},
    "kb_rack_walk":              {"up": ["kb_bottoms_up_carry"], "down": ["kb_farmers_carry"]},
    "kb_bottoms_up_carry":       {"up": [], "down": ["kb_rack_walk"]},
    # CORE
    "bw_mcgill_bird_dog":        {"up": ["bw_dead_bug"], "down": []},
    "bw_mcgill_curl_up":         {"up": ["bw_hollow_body"], "down": []},
    "bw_dead_bug":               {"up": ["bw_plank"], "down": ["bw_mcgill_bird_dog"]},
    "bw_plank":                  {"up": ["bw_hollow_body", "gym_ab_wheel"], "down": ["bw_dead_bug"]},
    "bw_side_plank":             {"up": ["bw_copenhagen_plank"], "down": ["bw_plank"]},
    "bw_hollow_body":            {"up": ["bw_l_sit", "gym_ab_wheel"], "down": ["bw_plank"]},
    "bw_copenhagen_plank":       {"up": [], "down": ["bw_side_plank"]},
    "gym_pallof_press":          {"up": [], "down": ["bw_plank"]},
    "gym_cable_crunch":          {"up": ["gym_hanging_knee_raise"], "down": ["bw_dead_bug"]},
    "gym_ab_wheel":              {"up": ["gym_ab_rollout_standing"], "down": ["bw_plank"]},
    "gym_reverse_hyper":         {"up": [], "down": ["bw_glute_bridge"]},
    "kb_turkish_getup":          {"up": [], "down": ["bw_plank"]},
    "kb_windmill":               {"up": [], "down": ["gym_pallof_press"]},
    "bw_tibialis_raise":         {"up": [], "down": []},
}

# ── equipment overrides for existing exercises ────────────────────────────────
EQUIPMENT_UPDATES = {
    "gym_pullup":  ["gym", "bodyweight", "kettlebell", "hybrid"],
    "gym_chinup":  ["gym", "bodyweight", "kettlebell", "hybrid"],
    "bw_negative_pullup": ["bodyweight", "gym", "home_gym", "kettlebell", "hybrid"],
}

# ── new exercises ─────────────────────────────────────────────────────────────
NEW_EXERCISES = [
    # ── SQUAT ─────────────────────────────────────────────────────────────────
    {
        "id": "gym_paused_back_squat", "name": "Paused Back Squat",
        "equipment": ["gym"], "pattern": "squat",
        "muscle_groups": {"primary": ["quads", "glutes"], "secondary": ["hamstrings", "spinal_erectors", "abs"]},
        "level_min": 3,
        "coaching_cues": ["3 Sek. unten halten — keine Entspannung", "Aus dem Loch heraus drücken, kein Rebound", "Knie nach außen, Oberkörper stabil durch die Pause"],
        "progressions_up": ["gym_tempo_squat"], "progressions_down": ["gym_back_squat"],
        "substitutions_a": ["gym_front_squat", "gym_tempo_squat", "gym_back_squat"],
        "substitutions_b": {"knee": "gym_box_squat", "spine": "gym_goblet_squat_db", "hip": "gym_box_squat"}
    },
    {
        "id": "gym_tempo_squat", "name": "Tempo Squat (4-0-1-0)",
        "equipment": ["gym"], "pattern": "squat",
        "muscle_groups": {"primary": ["quads", "glutes"], "secondary": ["hamstrings", "spinal_erectors", "abs"]},
        "level_min": 3,
        "coaching_cues": ["4 Sek. runter — maximal langsam und kontrolliert", "Kein Pause unten, sofort hoch", "Gewicht reduzieren — 30–40% weniger als normal"],
        "progressions_up": [], "progressions_down": ["gym_paused_back_squat"],
        "substitutions_a": ["gym_paused_back_squat", "gym_front_squat", "gym_back_squat"],
        "substitutions_b": {"knee": "gym_box_squat", "spine": "gym_goblet_squat_db", "hip": "gym_goblet_squat_db"}
    },
    {
        "id": "bw_jump_squat", "name": "Jump Squat",
        "equipment": ["bodyweight", "gym", "home_gym", "travel", "hybrid"], "pattern": "squat",
        "muscle_groups": {"primary": ["quads", "glutes"], "secondary": ["hamstrings", "calves", "abs"]},
        "level_min": 2,
        "coaching_cues": ["Sanft landen — erst Zehen, dann Ferse", "Squat-Tiefe vor dem Sprung, nicht nur Hüftbeuge", "Sofort wieder in die nächste Wiederholung"],
        "progressions_up": [], "progressions_down": ["bw_squat"],
        "substitutions_a": ["bw_squat", "bw_pause_squat", "bw_cossack_squat"],
        "substitutions_b": {"knee": "bw_squat", "hip": "bw_squat", "ankle": "bw_squat"}
    },
    {
        "id": "kb_front_squat", "name": "Kettlebell Front Squat",
        "equipment": ["kettlebell", "hybrid"], "pattern": "squat",
        "muscle_groups": {"primary": ["quads", "glutes"], "secondary": ["abs", "shoulders"]},
        "level_min": 2,
        "coaching_cues": ["Beide KBs in Rack-Position — Unterarme senkrecht", "Oberkörper so aufrecht wie möglich", "Ellenbogen hoch halten, nicht fallen lassen"],
        "progressions_up": [], "progressions_down": ["kb_goblet_squat"],
        "substitutions_a": ["kb_goblet_squat", "bw_pause_squat", "bw_atg_split_squat"],
        "substitutions_b": {"knee": "kb_goblet_squat", "spine": "kb_goblet_squat", "wrist": "kb_goblet_squat"}
    },
    {
        "id": "bw_assisted_pistol_squat", "name": "Assisted Pistol Squat",
        "equipment": ["bodyweight", "gym", "home_gym", "hybrid"], "pattern": "single_leg",
        "muscle_groups": {"primary": ["quads", "glutes"], "secondary": ["hamstrings", "abs", "calves"]},
        "level_min": 3,
        "coaching_cues": ["An einer Stange oder Tür festhalten — Gewicht langsam reduzieren", "Spielbein nach vorne strecken", "Tief gehen — Ferse bleibt auf dem Boden"],
        "progressions_up": ["bw_pistol_squat"], "progressions_down": ["bw_atg_split_squat"],
        "substitutions_a": ["bw_atg_split_squat", "bw_bulgarian_split_squat", "bw_skater_squat"],
        "substitutions_b": {"knee": "bw_reverse_lunge", "hip": "bw_reverse_lunge"}
    },
    # ── HINGE ─────────────────────────────────────────────────────────────────
    {
        "id": "bw_single_leg_glute_bridge", "name": "Single Leg Glute Bridge",
        "equipment": ["bodyweight", "gym", "home_gym", "travel", "hybrid"], "pattern": "hinge",
        "muscle_groups": {"primary": ["glutes"], "secondary": ["hamstrings", "abs"]},
        "level_min": 1,
        "coaching_cues": ["Ein Bein gestreckt, das andere Knie gebeugt", "Hüfte voll strecken oben — Glutes maximal anspannen", "Hüfte gerade halten — nicht zur Seite kippen"],
        "progressions_up": ["gym_hip_thrust_machine", "gym_rdl_db"], "progressions_down": ["bw_glute_bridge"],
        "substitutions_a": ["bw_glute_bridge", "gym_hip_thrust_machine", "gym_rdl_db"],
        "substitutions_b": {"knee": "bw_glute_bridge", "spine": "bw_glute_bridge"}
    },
    {
        "id": "gym_45_degree_back_extension", "name": "45° Rückenstrecker",
        "equipment": ["gym"], "pattern": "hinge",
        "muscle_groups": {"primary": ["spinal_erectors", "glutes"], "secondary": ["hamstrings"]},
        "level_min": 2,
        "coaching_cues": ["Oberkörper nur bis parallel zum Boden heben — kein Hyperextend", "Langsam absenken — Dehnung im unteren Rücken", "Arme vor der Brust verschränkt oder hinter dem Kopf"],
        "progressions_up": ["gym_good_morning"], "progressions_down": ["bw_glute_bridge"],
        "substitutions_a": ["gym_rdl_db", "bw_glute_bridge", "gym_hip_thrust_machine"],
        "substitutions_b": {"spine": "bw_glute_bridge", "hip": "bw_glute_bridge"}
    },
    {
        "id": "gym_good_morning", "name": "Good Morning (Langhantel)",
        "equipment": ["gym"], "pattern": "hinge",
        "muscle_groups": {"primary": ["spinal_erectors", "hamstrings"], "secondary": ["glutes", "abs"]},
        "level_min": 3,
        "coaching_cues": ["Stange auf dem Trapezius — weiche Knie, nicht gestreckt", "Hüfte zurück schieben — Oberkörper neigt sich nach vorne", "Nicht weiter als parallel — Rücken bleibt flach"],
        "progressions_up": ["gym_glute_ham_raise"], "progressions_down": ["gym_rdl_barbell"],
        "substitutions_a": ["gym_rdl_barbell", "gym_45_degree_back_extension", "gym_glute_ham_raise"],
        "substitutions_b": {"spine": "gym_rdl_db", "knee": "gym_rdl_barbell"}
    },
    {
        "id": "gym_glute_ham_raise", "name": "Glute Ham Raise",
        "equipment": ["gym"], "pattern": "hinge",
        "muscle_groups": {"primary": ["hamstrings", "glutes"], "secondary": ["spinal_erectors", "calves"]},
        "level_min": 3,
        "coaching_cues": ["Füße fixiert, Körper langsam absenken — exzentrisch ist der Schlüssel", "Hüfte gestreckt halten während der Bewegung", "Anfänger: assistiert mit Armen abstützen"],
        "progressions_up": ["gym_nordic_curl"], "progressions_down": ["gym_good_morning"],
        "substitutions_a": ["gym_nordic_curl", "gym_rdl_barbell", "gym_good_morning"],
        "substitutions_b": {"spine": "gym_rdl_db", "knee": "gym_hip_thrust_barbell"}
    },
    {
        "id": "gym_nordic_curl", "name": "Nordic Curl (Hamstring)",
        "equipment": ["gym", "home_gym"], "pattern": "hinge",
        "muscle_groups": {"primary": ["hamstrings"], "secondary": ["glutes", "spinal_erectors"]},
        "level_min": 4,
        "coaching_cues": ["Füße fixiert — langsam fallen lassen, so lang wie möglich kontrollieren", "Hüfte gestreckt — keine Beugung während der Bewegung", "Konzentrisch mit Armen helfen — exzentrisch alleine"],
        "progressions_up": [], "progressions_down": ["gym_glute_ham_raise"],
        "substitutions_a": ["gym_glute_ham_raise", "gym_rdl_barbell", "gym_conventional_deadlift"],
        "substitutions_b": {"spine": "gym_rdl_db", "knee": "gym_hip_thrust_barbell"}
    },
    {
        "id": "gym_single_leg_hip_thrust_db", "name": "Single Leg Hip Thrust (Kurzhantel)",
        "equipment": ["gym", "home_gym"], "pattern": "hinge",
        "muscle_groups": {"primary": ["glutes"], "secondary": ["hamstrings", "abs"]},
        "level_min": 2,
        "coaching_cues": ["Schulterblätter auf der Bank, Hantel auf der Hüfte", "Ein Bein gestreckt, volle Hüftstreckung oben", "Hüfte gerade — nicht zur Seite kippen"],
        "progressions_up": ["gym_hip_thrust_barbell"], "progressions_down": ["gym_hip_thrust_machine"],
        "substitutions_a": ["gym_hip_thrust_barbell", "bw_single_leg_glute_bridge", "gym_hip_thrust_machine"],
        "substitutions_b": {"spine": "bw_single_leg_glute_bridge", "knee": "bw_glute_bridge"}
    },
    # ── PUSH HORIZONTAL ───────────────────────────────────────────────────────
    {
        "id": "bw_incline_pushup", "name": "Incline Push-Up (Hände erhöht)",
        "equipment": ["bodyweight", "gym", "home_gym", "travel", "hybrid"], "pattern": "push_horizontal",
        "muscle_groups": {"primary": ["chest", "triceps"], "secondary": ["shoulders_front", "abs"]},
        "level_min": 1,
        "coaching_cues": ["Hände auf Bank oder Stuhl — Winkel reduziert Körpergewicht", "Körper als Brett — Hüfte nicht hängen", "Volle ROM — Brust zur Bank"],
        "progressions_up": ["bw_pushup"], "progressions_down": [],
        "substitutions_a": ["bw_pushup", "gym_machine_chest_press", "gym_db_floor_press"],
        "substitutions_b": {"shoulder": "gym_machine_chest_press", "elbow": "gym_machine_chest_press", "wrist": "gym_machine_chest_press"}
    },
    {
        "id": "bw_wide_pushup", "name": "Wide Push-Up",
        "equipment": ["bodyweight", "gym", "home_gym", "travel", "hybrid"], "pattern": "push_horizontal",
        "muscle_groups": {"primary": ["chest"], "secondary": ["triceps", "shoulders_front", "abs"]},
        "level_min": 1,
        "coaching_cues": ["Hände weiter als schulterbreit — mehr Brustfokus", "Körper als Brett, kein Hohlkreuz", "Tiefe erreichen — Brust berührt fast den Boden"],
        "progressions_up": ["bw_archer_pushup"], "progressions_down": ["bw_pushup"],
        "substitutions_a": ["bw_pushup", "bw_diamond_pushup", "bw_archer_pushup"],
        "substitutions_b": {"shoulder": "bw_incline_pushup", "wrist": "bw_incline_pushup", "elbow": "gym_machine_chest_press"}
    },
    {
        "id": "bw_diamond_pushup", "name": "Diamond Push-Up",
        "equipment": ["bodyweight", "gym", "home_gym", "travel", "hybrid"], "pattern": "push_horizontal",
        "muscle_groups": {"primary": ["triceps", "chest"], "secondary": ["shoulders_front", "abs"]},
        "level_min": 2,
        "coaching_cues": ["Hände bilden Diamant unter der Brust", "Ellenbogen nah am Körper bleiben", "Mehr Trizeps als Standard-Push-Up"],
        "progressions_up": ["bw_archer_pushup"], "progressions_down": ["bw_pushup"],
        "substitutions_a": ["bw_pushup", "bw_wide_pushup", "bw_archer_pushup"],
        "substitutions_b": {"shoulder": "bw_pushup", "elbow": "bw_incline_pushup", "wrist": "bw_incline_pushup"}
    },
    {
        "id": "bw_decline_pushup", "name": "Decline Push-Up (Füße erhöht)",
        "equipment": ["bodyweight", "gym", "home_gym", "travel", "hybrid"], "pattern": "push_horizontal",
        "muscle_groups": {"primary": ["chest", "shoulders_front"], "secondary": ["triceps", "abs"]},
        "level_min": 2,
        "coaching_cues": ["Füße auf Bank oder Stuhl — obere Brust und Schultern betont", "Körper als Brett, Hüfte nicht fallen lassen", "Kontrolliert absenken"],
        "progressions_up": ["bw_archer_pushup", "bw_pike_pushup"], "progressions_down": ["bw_pushup"],
        "substitutions_a": ["bw_pushup", "bw_archer_pushup", "bw_wide_pushup"],
        "substitutions_b": {"shoulder": "bw_pushup", "wrist": "bw_incline_pushup"}
    },
    {
        "id": "bw_one_arm_pushup_negatives", "name": "One-Arm Push-Up Negatives",
        "equipment": ["bodyweight", "gym", "travel", "hybrid"], "pattern": "push_horizontal",
        "muscle_groups": {"primary": ["chest", "triceps"], "secondary": ["shoulders_front", "abs", "obliques"]},
        "level_min": 3,
        "coaching_cues": ["Nur die exzentrische Phase (runter) einhändig — 5 Sek.", "Andere Hand kurz abstützen für den Rückweg", "Füße weit auseinander für Stabilität"],
        "progressions_up": ["bw_one_arm_pushup"], "progressions_down": ["bw_archer_pushup"],
        "substitutions_a": ["bw_archer_pushup", "bw_diamond_pushup", "gym_weighted_dips"],
        "substitutions_b": {"shoulder": "bw_pushup", "wrist": "bw_archer_pushup"}
    },
    {
        "id": "bw_one_arm_pushup", "name": "One-Arm Push-Up",
        "equipment": ["bodyweight", "gym"], "pattern": "push_horizontal",
        "muscle_groups": {"primary": ["chest", "triceps"], "secondary": ["shoulders_front", "abs", "obliques"]},
        "level_min": 4,
        "coaching_cues": ["Hand unter der Brust, Beine weit auseinander", "Körper so gerade wie möglich — keine starke Rotation", "Vollständige ROM — Brust zum Boden"],
        "progressions_up": [], "progressions_down": ["bw_one_arm_pushup_negatives"],
        "substitutions_a": ["bw_one_arm_pushup_negatives", "bw_archer_pushup", "gym_weighted_dips"],
        "substitutions_b": {"shoulder": "bw_archer_pushup", "wrist": "bw_archer_pushup"}
    },
    {
        "id": "kb_floor_press", "name": "Kettlebell Floor Press",
        "equipment": ["kettlebell", "hybrid"], "pattern": "push_horizontal",
        "muscle_groups": {"primary": ["chest", "triceps"], "secondary": ["shoulders_front"]},
        "level_min": 1,
        "coaching_cues": ["Auf dem Boden liegend — Ellenbogen werden gestoppt", "Keine Schulterüberdehnung möglich", "Volle Streckung oben, Trizeps hart"],
        "progressions_up": ["gym_db_floor_press"], "progressions_down": ["bw_pushup"],
        "substitutions_a": ["bw_pushup", "gym_db_floor_press", "bw_diamond_pushup"],
        "substitutions_b": {"shoulder": "bw_pushup", "elbow": "bw_incline_pushup", "wrist": "bw_incline_pushup"}
    },
    {
        "id": "gym_weighted_dips", "name": "Weighted Dips (Gürtel)",
        "equipment": ["gym"], "pattern": "push_horizontal",
        "muscle_groups": {"primary": ["chest", "triceps"], "secondary": ["shoulders_front"]},
        "level_min": 3,
        "coaching_cues": ["Oberkörper leicht nach vorne für mehr Brustfokus", "Bis Schultern unter Ellenbogen absenken — volle ROM", "Gewicht am Gürtel — kontrollierte Ausführung"],
        "progressions_up": [], "progressions_down": ["gym_bench_press"],
        "substitutions_a": ["gym_bench_press", "gym_close_grip_bench", "bw_one_arm_pushup_negatives"],
        "substitutions_b": {"shoulder": "gym_db_bench_press", "elbow": "gym_machine_chest_press"}
    },
    {
        "id": "gym_close_grip_bench", "name": "Close Grip Bench Press",
        "equipment": ["gym"], "pattern": "push_horizontal",
        "muscle_groups": {"primary": ["triceps", "chest"], "secondary": ["shoulders_front"]},
        "level_min": 3,
        "coaching_cues": ["Griffweite schulterbreit — nicht zu eng", "Ellenbogen nah am Körper, ca. 30° Winkel", "Trizeps-Fokus: Streckung oben maximal"],
        "progressions_up": [], "progressions_down": ["gym_bench_press"],
        "substitutions_a": ["gym_bench_press", "gym_weighted_dips", "gym_db_bench_press"],
        "substitutions_b": {"shoulder": "gym_db_floor_press", "elbow": "gym_machine_chest_press", "wrist": "gym_machine_chest_press"}
    },
    # ── PUSH VERTICAL ─────────────────────────────────────────────────────────
    {
        "id": "bw_pike_pushup", "name": "Pike Push-Up",
        "equipment": ["bodyweight", "gym", "home_gym", "travel", "hybrid"], "pattern": "push_vertical",
        "muscle_groups": {"primary": ["shoulders_front", "shoulders_lateral"], "secondary": ["triceps", "abs"]},
        "level_min": 2,
        "coaching_cues": ["Hüfte hoch — umgekehrtes V mit dem Körper", "Kopf zwischen den Armen zum Boden", "Ellenbogen leicht nach außen, kein Flare"],
        "progressions_up": ["bw_pike_pushup_elevated"], "progressions_down": ["bw_decline_pushup"],
        "substitutions_a": ["bw_decline_pushup", "kb_single_press", "gym_db_shoulder_press"],
        "substitutions_b": {"shoulder": "bw_decline_pushup", "elbow": "bw_incline_pushup", "wrist": "bw_incline_pushup"}
    },
    {
        "id": "bw_pike_pushup_elevated", "name": "Pike Push-Up (Füße erhöht)",
        "equipment": ["bodyweight", "gym", "home_gym", "travel", "hybrid"], "pattern": "push_vertical",
        "muscle_groups": {"primary": ["shoulders_front", "shoulders_lateral"], "secondary": ["triceps", "abs"]},
        "level_min": 3,
        "coaching_cues": ["Füße auf Bank — je höher, desto schwerer und schulterähnlicher", "Kopf tief zum Boden", "Vorstufe zum Handstand-Push-Up"],
        "progressions_up": ["bw_wall_handstand_pushup"], "progressions_down": ["bw_pike_pushup"],
        "substitutions_a": ["bw_pike_pushup", "bw_decline_pushup", "gym_db_shoulder_press"],
        "substitutions_b": {"shoulder": "bw_pike_pushup", "wrist": "bw_pike_pushup"}
    },
    {
        "id": "bw_wall_handstand_pushup", "name": "Wall Handstand Push-Up",
        "equipment": ["bodyweight", "gym", "travel"], "pattern": "push_vertical",
        "muscle_groups": {"primary": ["shoulders_front", "shoulders_lateral"], "secondary": ["triceps", "abs", "spinal_erectors"]},
        "level_min": 4,
        "coaching_cues": ["Gesicht zur Wand — Hände 15cm entfernt", "Körper so gerade wie möglich", "Nur so tief wie kontrolliert ausführbar"],
        "progressions_up": [], "progressions_down": ["bw_pike_pushup_elevated"],
        "substitutions_a": ["bw_pike_pushup_elevated", "gym_ohp_barbell", "gym_z_press"],
        "substitutions_b": {"shoulder": "bw_pike_pushup", "wrist": "bw_pike_pushup", "elbow": "bw_pike_pushup"}
    },
    {
        "id": "kb_push_press", "name": "Kettlebell Push Press",
        "equipment": ["kettlebell", "hybrid"], "pattern": "push_vertical",
        "muscle_groups": {"primary": ["shoulders_front", "shoulders_lateral"], "secondary": ["triceps", "quads", "abs"]},
        "level_min": 2,
        "coaching_cues": ["Kurzer Knie-Dip als Impuls — dann explosiv drücken", "Mehr Gewicht als bei Strict Press möglich", "Lockout oben, Rumpf stabil"],
        "progressions_up": [], "progressions_down": ["kb_single_press"],
        "substitutions_a": ["kb_single_press", "gym_db_shoulder_press", "gym_push_press_barbell"],
        "substitutions_b": {"shoulder": "kb_single_press", "elbow": "gym_db_shoulder_press", "knee": "kb_single_press"}
    },
    {
        "id": "gym_push_press_barbell", "name": "Push Press (Langhantel)",
        "equipment": ["gym"], "pattern": "push_vertical",
        "muscle_groups": {"primary": ["shoulders_front", "shoulders_lateral"], "secondary": ["triceps", "quads", "abs"]},
        "level_min": 2,
        "coaching_cues": ["Knie-Dip: nur 10–15cm — kein tiefer Squat", "Impuls aus den Beinen, Arme drücken durch", "Stange über dem Kopf — nicht vor dem Körper"],
        "progressions_up": [], "progressions_down": ["gym_ohp_barbell"],
        "substitutions_a": ["gym_ohp_barbell", "gym_db_shoulder_press", "kb_push_press"],
        "substitutions_b": {"shoulder": "gym_landmine_ohp", "elbow": "gym_db_shoulder_press", "knee": "gym_ohp_barbell"}
    },
    {
        "id": "gym_z_press", "name": "Z-Press (Sitzen ohne Rückenlehne)",
        "equipment": ["gym"], "pattern": "push_vertical",
        "muscle_groups": {"primary": ["shoulders_front", "shoulders_lateral"], "secondary": ["triceps", "abs", "spinal_erectors"]},
        "level_min": 3,
        "coaching_cues": ["Auf dem Boden sitzen, Beine gestreckt — kein Rückhalt möglich", "Maximale Core-Aktivierung nötig für Stabilität", "Gewicht deutlich reduzieren vs. stehende OHP"],
        "progressions_up": [], "progressions_down": ["gym_ohp_barbell"],
        "substitutions_a": ["gym_ohp_barbell", "gym_db_shoulder_press", "kb_single_press"],
        "substitutions_b": {"shoulder": "gym_landmine_ohp", "spine": "gym_db_shoulder_press"}
    },
    # ── PULL VERTICAL ─────────────────────────────────────────────────────────
    {
        "id": "bw_negative_pullup", "name": "Negative Pull-Up (exzentrisch)",
        "equipment": ["bodyweight", "gym", "home_gym", "kettlebell", "hybrid"], "pattern": "pull_vertical",
        "muscle_groups": {"primary": ["back_lat"], "secondary": ["biceps", "back_upper"]},
        "level_min": 2,
        "coaching_cues": ["Oben starten (springen oder Box), langsam absenken — 5-8 Sek.", "Volle Streckung am Ende — Schultern aktiv", "Exzentrisch ist der stärkste Kraftgewinn"],
        "progressions_up": ["gym_chinup"], "progressions_down": ["bw_ring_row"],
        "substitutions_a": ["gym_lat_pulldown", "bw_ring_row", "gym_close_grip_pulldown"],
        "substitutions_b": {"shoulder": "gym_lat_pulldown", "elbow": "gym_lat_pulldown", "wrist": "bw_ring_row"}
    },
    {
        "id": "gym_close_grip_pulldown", "name": "Neutral Grip Pulldown",
        "equipment": ["gym"], "pattern": "pull_vertical",
        "muscle_groups": {"primary": ["back_lat"], "secondary": ["biceps", "back_upper"]},
        "level_min": 1,
        "coaching_cues": ["Neutraler Griff (Palmen zueinander) — schulterschonender", "Stange zur Brust, Ellenbogen zur Hüfte führen", "Schulterblätter zusammen am Endpunkt"],
        "progressions_up": ["gym_chinup"], "progressions_down": ["gym_lat_pulldown"],
        "substitutions_a": ["gym_lat_pulldown", "gym_chinup", "bw_ring_row"],
        "substitutions_b": {"shoulder": "gym_cable_pullover", "elbow": "gym_cable_pullover", "wrist": "bw_ring_row"}
    },
    {
        "id": "gym_weighted_pullup", "name": "Weighted Pull-Up (Gürtel)",
        "equipment": ["gym"], "pattern": "pull_vertical",
        "muscle_groups": {"primary": ["back_lat"], "secondary": ["biceps", "back_upper", "abs"]},
        "level_min": 3,
        "coaching_cues": ["Gewicht am Gürtel — Technik identisch mit Pull-Up", "Kein Schwung — strikt", "Kontrolliertes Absenken bis volle Streckung"],
        "progressions_up": [], "progressions_down": ["gym_pullup"],
        "substitutions_a": ["gym_pullup", "gym_chinup", "gym_lat_pulldown"],
        "substitutions_b": {"shoulder": "gym_lat_pulldown", "elbow": "gym_lat_pulldown", "wrist": "gym_lat_pulldown"}
    },
    # ── PULL HORIZONTAL ───────────────────────────────────────────────────────
    {
        "id": "bw_inverted_row", "name": "Inverted Row (Tisch / Stange)",
        "equipment": ["bodyweight", "gym", "home_gym", "travel", "hybrid"], "pattern": "pull_horizontal",
        "muscle_groups": {"primary": ["back_lat", "back_upper"], "secondary": ["biceps", "abs"]},
        "level_min": 1,
        "coaching_cues": ["Unter Tisch oder Stange — Brust zur Kante ziehen", "Schwierigkeit durch Körperwinkel steuern", "Schulterblätter zusammen am Endpunkt"],
        "progressions_up": ["gym_db_row"], "progressions_down": ["bw_towel_row"],
        "substitutions_a": ["bw_ring_row", "gym_db_row", "bw_towel_row"],
        "substitutions_b": {"shoulder": "gym_lat_pulldown", "elbow": "gym_lat_pulldown"}
    },
    {
        "id": "bw_towel_row", "name": "Towel Row (Handtuch an Tür)",
        "equipment": ["bodyweight", "travel", "hybrid"], "pattern": "pull_horizontal",
        "muscle_groups": {"primary": ["back_lat", "back_upper"], "secondary": ["biceps"]},
        "level_min": 1,
        "coaching_cues": ["Handtuch um Türknauf — zurücklehnen und Brust zur Tür ziehen", "Füße an der Wand neben der Tür für Stabilität", "Schulterblätter zusammen am Endpunkt"],
        "progressions_up": ["bw_inverted_row"], "progressions_down": [],
        "substitutions_a": ["bw_inverted_row", "bw_ring_row", "gym_band_pull_apart"],
        "substitutions_b": {"shoulder": "gym_band_pull_apart", "elbow": "gym_band_pull_apart"}
    },
    {
        "id": "gym_chest_supported_db_row", "name": "Chest Supported Row (Kurzhantel)",
        "equipment": ["gym", "home_gym"], "pattern": "pull_horizontal",
        "muscle_groups": {"primary": ["back_lat", "back_upper"], "secondary": ["biceps", "shoulders_rear"]},
        "level_min": 2,
        "coaching_cues": ["Brust auf Schrägbank — kein Schwung aus dem Rücken möglich", "Ideal für Rücken-Isolation ohne Rückenbeschwerden", "Schulterblätter maximieren am Endpunkt"],
        "progressions_up": ["gym_barbell_row"], "progressions_down": ["gym_db_row"],
        "substitutions_a": ["gym_db_row", "gym_seated_cable_row", "gym_barbell_row"],
        "substitutions_b": {"spine": "bw_ring_row", "shoulder": "gym_seated_cable_row"}
    },
    {
        "id": "gym_single_arm_cable_row", "name": "Single Arm Cable Row",
        "equipment": ["gym"], "pattern": "pull_horizontal",
        "muscle_groups": {"primary": ["back_lat", "back_upper"], "secondary": ["biceps", "shoulders_rear", "obliques"]},
        "level_min": 2,
        "coaching_cues": ["Einhändig — mehr Rotation und Schulterblatt-ROM möglich", "Zur Hüfte ziehen, Ellenbogen nah", "Leichtes Eindrehen des Oberkörpers ist OK"],
        "progressions_up": ["gym_barbell_row"], "progressions_down": ["gym_seated_cable_row"],
        "substitutions_a": ["gym_seated_cable_row", "gym_db_row", "gym_barbell_row"],
        "substitutions_b": {"spine": "gym_seated_cable_row", "elbow": "gym_seated_cable_row"}
    },
    # ── SINGLE LEG ────────────────────────────────────────────────────────────
    {
        "id": "bw_skater_squat", "name": "Skater Squat",
        "equipment": ["bodyweight", "gym", "home_gym", "travel", "hybrid"], "pattern": "single_leg",
        "muscle_groups": {"primary": ["quads", "glutes"], "secondary": ["hamstrings", "abs"]},
        "level_min": 3,
        "coaching_cues": ["Kein Aufstützen — freistehend auf einem Bein", "Hinteres Knie taucht fast den Boden", "Arme als Gegengewicht nach vorne"],
        "progressions_up": ["bw_assisted_pistol_squat"], "progressions_down": ["gym_bulgarian_split_squat_db"],
        "substitutions_a": ["bw_assisted_pistol_squat", "gym_bulgarian_split_squat_db", "bw_reverse_lunge"],
        "substitutions_b": {"knee": "bw_reverse_lunge", "hip": "bw_reverse_lunge"}
    },
    {
        "id": "gym_single_leg_press", "name": "Single Leg Press (Maschine)",
        "equipment": ["gym"], "pattern": "single_leg",
        "muscle_groups": {"primary": ["quads", "glutes"], "secondary": ["hamstrings"]},
        "level_min": 1,
        "coaching_cues": ["Ein Fuß auf der Plattform — Mitte", "Knie trackt über die Zehen", "Volle ROM — kein Durchstrecken am oberen Punkt"],
        "progressions_up": ["gym_step_up_db"], "progressions_down": ["bw_reverse_lunge"],
        "substitutions_a": ["gym_step_up_db", "bw_reverse_lunge", "gym_leg_press_machine"],
        "substitutions_b": {"knee": "gym_leg_press_machine", "hip": "gym_leg_press_machine"}
    },
    {
        "id": "kb_single_leg_rdl", "name": "Single Leg RDL (Kettlebell)",
        "equipment": ["kettlebell", "hybrid"], "pattern": "single_leg",
        "muscle_groups": {"primary": ["hamstrings", "glutes"], "secondary": ["spinal_erectors", "abs"]},
        "level_min": 2,
        "coaching_cues": ["KB in Gegenhand zum Standbein — mehr Balance-Challenge", "Hüfte und Schultern parallel zum Boden", "Standbein hat weiche Knie"],
        "progressions_up": [], "progressions_down": ["kb_deadlift"],
        "substitutions_a": ["bw_single_leg_rdl", "gym_single_leg_rdl_db", "kb_deadlift"],
        "substitutions_b": {"knee": "bw_glute_bridge", "spine": "bw_glute_bridge", "hip": "bw_glute_bridge"}
    },
    # ── CARRY ─────────────────────────────────────────────────────────────────
    {
        "id": "gym_barbell_overhead_carry", "name": "Barbell Overhead Carry",
        "equipment": ["gym"], "pattern": "carry",
        "muscle_groups": {"primary": ["shoulders", "abs"], "secondary": ["back_upper", "quads", "spinal_erectors"]},
        "level_min": 3,
        "coaching_cues": ["Stange über dem Kopf — Schultern aktiv gepackt", "Kein Hohlkreuz — Rippen runter", "Kleine stabile Schritte"],
        "progressions_up": [], "progressions_down": ["gym_overhead_carry_db"],
        "substitutions_a": ["gym_overhead_carry_db", "kb_bottoms_up_carry", "gym_farmers_carry_db"],
        "substitutions_b": {"shoulder": "gym_farmers_carry_db", "elbow": "gym_farmers_carry_db", "spine": "gym_farmers_carry_db"}
    },
    # ── CORE ──────────────────────────────────────────────────────────────────
    {
        "id": "bw_side_plank", "name": "Side Plank",
        "equipment": ["bodyweight", "gym", "home_gym", "travel", "hybrid"], "pattern": "core",
        "muscle_groups": {"primary": ["obliques"], "secondary": ["abs", "glutes", "shoulders"]},
        "level_min": 1,
        "coaching_cues": ["Hüfte nicht durchhängen lassen — gerade Linie", "Schulter aktiv — nicht ins Gelenk sinken", "Für Einsteiger: Knie aufgestützt"],
        "progressions_up": ["bw_copenhagen_plank"], "progressions_down": ["bw_plank"],
        "substitutions_a": ["bw_plank", "bw_dead_bug", "gym_pallof_press"],
        "substitutions_b": {"shoulder": "bw_dead_bug", "wrist": "bw_dead_bug", "spine": "bw_dead_bug"}
    },
    {
        "id": "gym_hanging_knee_raise", "name": "Hanging Knee Raise",
        "equipment": ["gym", "bodyweight"], "pattern": "core",
        "muscle_groups": {"primary": ["abs", "hip_flexors"], "secondary": ["obliques", "back_lat"]},
        "level_min": 1,
        "coaching_cues": ["Keine Schwungbewegung — Knie kontrolliert heben", "Schultern aktiv — nicht hängen lassen", "Oben kurz halten, kontrolliert absenken"],
        "progressions_up": ["gym_hanging_leg_raise"], "progressions_down": ["gym_cable_crunch"],
        "substitutions_a": ["gym_cable_crunch", "bw_dead_bug", "bw_hollow_body"],
        "substitutions_b": {"shoulder": "bw_dead_bug", "wrist": "gym_cable_crunch", "elbow": "gym_cable_crunch"}
    },
    {
        "id": "gym_hanging_leg_raise", "name": "Hanging Leg Raise (gestreckt)",
        "equipment": ["gym", "bodyweight"], "pattern": "core",
        "muscle_groups": {"primary": ["abs"], "secondary": ["hip_flexors", "obliques"]},
        "level_min": 2,
        "coaching_cues": ["Beine gestreckt bis horizontal — kein Schwung", "Hüfte leicht nach hinten rollen am Endpunkt", "Schultern aktiv gepackt"],
        "progressions_up": ["bw_l_sit"], "progressions_down": ["gym_hanging_knee_raise"],
        "substitutions_a": ["gym_hanging_knee_raise", "bw_hollow_body", "bw_v_up"],
        "substitutions_b": {"shoulder": "bw_hollow_body", "wrist": "gym_cable_crunch", "spine": "bw_dead_bug"}
    },
    {
        "id": "bw_v_up", "name": "V-Up",
        "equipment": ["bodyweight", "gym", "home_gym", "travel", "hybrid"], "pattern": "core",
        "muscle_groups": {"primary": ["abs"], "secondary": ["hip_flexors"]},
        "level_min": 2,
        "coaching_cues": ["Arme und Beine gleichzeitig heben — treffen sich oben", "Lendenwirbel nicht durchhängen — kurz am Boden", "Kontrolliert absenken — nicht fallen lassen"],
        "progressions_up": ["bw_l_sit"], "progressions_down": ["bw_hollow_body"],
        "substitutions_a": ["bw_hollow_body", "bw_dead_bug", "gym_hanging_knee_raise"],
        "substitutions_b": {"spine": "bw_dead_bug", "hip": "bw_dead_bug"}
    },
    {
        "id": "bw_l_sit", "name": "L-Sit (Boden / Parallelbarren)",
        "equipment": ["bodyweight", "gym"], "pattern": "core",
        "muscle_groups": {"primary": ["abs", "hip_flexors"], "secondary": ["quads", "shoulders", "triceps"]},
        "level_min": 3,
        "coaching_cues": ["Hände neben den Hüften — Arme gestreckt", "Beine horizontal halten — Quads aktiv anspannen", "Für Einsteiger: ein Bein gestreckt, eines gebeugt"],
        "progressions_up": ["bw_dragon_flag"], "progressions_down": ["bw_hollow_body"],
        "substitutions_a": ["bw_hollow_body", "gym_hanging_leg_raise", "bw_v_up"],
        "substitutions_b": {"shoulder": "bw_hollow_body", "wrist": "gym_hanging_leg_raise", "spine": "bw_dead_bug"}
    },
    {
        "id": "bw_dragon_flag", "name": "Dragon Flag",
        "equipment": ["bodyweight", "gym"], "pattern": "core",
        "muscle_groups": {"primary": ["abs", "spinal_erectors"], "secondary": ["hip_flexors", "shoulders", "back_lat"]},
        "level_min": 4,
        "coaching_cues": ["Schultern auf der Bank — Körper als Brett nach oben", "Langsam absenken, nie den Boden berühren", "Bruce Lee Lieblingsübung — volle Körperspannung"],
        "progressions_up": [], "progressions_down": ["bw_l_sit"],
        "substitutions_a": ["bw_l_sit", "bw_hollow_body", "gym_ab_rollout_standing"],
        "substitutions_b": {"shoulder": "bw_hollow_body", "spine": "bw_dead_bug"}
    },
    {
        "id": "gym_ab_rollout_standing", "name": "Ab Wheel Rollout (stehend)",
        "equipment": ["gym", "home_gym"], "pattern": "core",
        "muscle_groups": {"primary": ["abs"], "secondary": ["back_lat", "shoulders", "spinal_erectors"]},
        "level_min": 3,
        "coaching_cues": ["Von stehend ausrollen — viel schwerer als kniend", "Lendenwirbel flach halten — kein Durchhängen", "Nur so weit wie kontrollierbar"],
        "progressions_up": ["bw_dragon_flag"], "progressions_down": ["gym_ab_wheel"],
        "substitutions_a": ["gym_ab_wheel", "bw_l_sit", "bw_hollow_body"],
        "substitutions_b": {"shoulder": "bw_hollow_body", "wrist": "bw_plank", "spine": "bw_dead_bug"}
    },
]

# ── main ──────────────────────────────────────────────────────────────────────
with open(DATA) as f:
    data = json.load(f)

# Update existing exercises
for ex in data["exercises"]:
    prog = PROGRESSIONS.get(ex["id"], {})
    ex["progressions_up"] = prog.get("up", [])
    ex["progressions_down"] = prog.get("down", [])
    if ex["id"] in EQUIPMENT_UPDATES:
        ex["equipment"] = EQUIPMENT_UPDATES[ex["id"]]

# Append new exercises
existing_ids = {ex["id"] for ex in data["exercises"]}
for new_ex in NEW_EXERCISES:
    if new_ex["id"] not in existing_ids:
        data["exercises"].append(new_ex)

# Save
with open(DATA, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Done. Total exercises: {len(data['exercises'])}")

# Validate all cross-references
all_ids = {ex["id"] for ex in data["exercises"]}
errors = []
for ex in data["exercises"]:
    for ref in ex.get("substitutions_a", []):
        if ref not in all_ids:
            errors.append(f"{ex['id']}.substitutions_a → missing: {ref}")
    for ref in ex.get("substitutions_b", {}).values():
        if ref not in all_ids:
            errors.append(f"{ex['id']}.substitutions_b → missing: {ref}")
    for ref in ex.get("progressions_up", []):
        if ref not in all_ids:
            errors.append(f"{ex['id']}.progressions_up → missing: {ref}")
    for ref in ex.get("progressions_down", []):
        if ref not in all_ids:
            errors.append(f"{ex['id']}.progressions_down → missing: {ref}")

if errors:
    print(f"\n{len(errors)} BROKEN REFERENCES:")
    for e in errors:
        print(" ", e)
else:
    print("All cross-references valid.")
