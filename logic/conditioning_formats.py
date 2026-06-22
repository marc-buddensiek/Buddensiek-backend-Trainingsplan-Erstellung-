"""
Conditioning-Format-Baukasten (MVP-7 Naht 2c) — Spec Thema 6.

Level→Format/Work:Rest/Dauer-Map + Block-Stapel-Logik. Geteilt von plan_assembler
(Dosierung); ab Naht 4 auch von split_selector (echte Rotation, ersetzt den
trivialen Platzhalter-Pick hier).

Formate (7): Session-füllend (amrap/zirkel/intervalle) + Block-Formate
(tabata/density/ladders/komplexe). Block-dosierbar (4d): **Tabata + Density + Ladders** (5-Min-Block).
Komplexe bleibt vorerst draußen (TODO(mvp7-komplexe): braucht vordefinierte Coach-Ketten — Flow ohne
Ablegen, nicht aus Einzelübungen stapelbar) — gültiges Enum, aber NICHT im Rotations-Pool.

Conditioning trägt KEINE RPE (Thema 6) — Intensität ergibt sich aus Format/Work:Rest/Dauer.

Dauer-Modell: An REINEN Conditioning-Tagen (Fettabbau 4/5/6) füllt das Conditioning die
vom Klienten gewählte `session_dauer_min` (− Warmup) — **KEINE Level-Deckelung**. Das Level
steuert nur Format-Verfügbarkeit (Level→Format-Map), Work:Rest und Übungskomplexität
(skill_level), NICHT die Dauer. L1/L2/L4 mit 45 Min bekommen je ~45 Min Conditioning, nur in
unterschiedlichen Formaten. Gemischte Tage (Recomp + Fettabbau ≤3) nutzen den kurzen
amrap-Finisher (fix ≤10 Min, bewusste 10-Min-Regel — keine Level-Deckelung); die
Block-Stapelung greift dort nicht.
"""
from __future__ import annotations

from logic.volume_calculator import WARMUP_MIN

SESSION_FILLING = {"amrap", "zirkel", "intervalle"}      # ein Block = ganze Session
BLOCK_IMPLEMENTED = {"tabata", "density", "ladders"}     # block-dosierbar (4d: + ladders, 5-Min-Block)
# TODO(mvp7-komplexe): Komplexe bewusst NICHT aufnehmen — braucht vordefinierte Coach-Ketten (Flow
# ohne Ablegen), nicht aus Einzelübungen stapelbar. Bleibt gültiges Enum, aber aus dem Pool gefiltert
# (steht in _LEVEL_FORMATS/_EQUIPMENT_FORMATS, wird aber von `impl` unten herausgefiltert).
CONDITIONING = SESSION_FILLING | BLOCK_IMPLEMENTED       # was als metabolic/Conditioning gilt

# Level → verfügbare Formate (Reihenfolge wie Spec-Tabelle Thema 6)
_LEVEL_FORMATS: dict[int, list[str]] = {
    1: ["intervalle", "zirkel"],
    2: ["intervalle", "amrap", "density", "ladders"],
    3: ["amrap", "zirkel", "density", "ladders", "tabata"],
    4: ["amrap", "tabata", "density", "komplexe"],
}

# Equipment → bevorzugte Formate (Spec Thema 6). Leeres Set = alle (kein Filter).
# travel ≈ Bodyweight; hybrid ≈ Kettlebell ∪ Bodyweight. (Spec nennt nur KB/BW/Gym/Home.)
_EQUIPMENT_FORMATS: dict[str, set[str]] = {
    "kettlebell": {"komplexe", "density", "ladders"},
    "bodyweight": {"amrap", "tabata", "zirkel"},
    "travel":     {"amrap", "tabata", "zirkel"},
    "hybrid":     {"komplexe", "density", "ladders", "amrap", "tabata", "zirkel"},
    "gym":        set(),
    "home_gym":   set(),
}

# Level → (Work, Rest) Sek. Höheres Level = dichteres Verhältnis (mehr Arbeit, weniger Pause).
# TODO(conditioning-timing-model): level-fest (45/15 + Progression über Runden) vs wochen-rampt
# (_METABOLIC_CONFIG intervalle 30→40) — Entscheid im Conditioning-Methodik-Durchgang (mit
# Fettabbau-Rampe). _LEVEL_WORK_REST ist der level-feste Kandidat; seit Naht 2b NICHT mehr im
# Intervalle-Header (der ist jetzt modell-agnostisch), bis der Entscheid fällt. level_work_rest()
# bleibt für Tests/künftige Nutzung exportiert.
_LEVEL_WORK_REST: dict[int, tuple[int, int]] = {1: (40, 20), 2: (45, 15), 3: (45, 15), 4: (50, 10)}

# (Die früheren Level-Dauer-Bänder steuern die Dauer NICHT mehr — Dauer = session_dauer_min.
#  Verbleiben als reine Doku-Notiz in COACHING_SPEC Thema 6.)

# Block-Formate: feste Block-Dauer (Min) — Format-eigenes Timing schlägt Level-Work:Rest.
_BLOCK_DAUER_MIN: dict[str, int] = {"tabata": 4, "density": 5, "ladders": 5}

# Per-Block-Parameter (eine Übung je Block). saetze/wdh sind Anzeige; keine RPE (Thema 6).
_BLOCK_PARAMS: dict[str, dict] = {
    "tabata":  {"saetze": 8, "wdh": "20 s an / 10 s aus"},                       # 8 Runden = 4 Min, fix
    "density": {"saetze": 1, "wdh": "5 Min — max. Wiederholungen bei festem Gewicht"},
    "ladders": {"saetze": 1, "wdh": "5 Min — Leiter aufsteigend (1-2-3-…) bis Zeitablauf"},
}

REST_BETWEEN_BLOCKS_SEK = 60   # ~60 s Pause zwischen Blöcken
_REST_MIN = 1                  # = 60 s in Minuten (für die Dauer-Rechnung)


def is_conditioning(session_typ: str) -> bool:
    return session_typ in CONDITIONING


def is_block_format(session_typ: str) -> bool:
    return session_typ in BLOCK_IMPLEMENTED


def _conditioning_pool(level: int, equipment: str) -> list[str]:
    """Implementierte Formate für das Level, **equipment-bevorzugt zuerst** (weiche Bevorzugung):
    erst die vom Equipment bevorzugten, dann der Rest des Levels — so bleibt der Pool ≥ 2 und die
    2 C-Tage differenzieren immer. Leerer Equipment-Filter (gym/home) = alle Level-Formate.
    (Ladders/Komplexe sind noch nicht dosierbar → Naht 4; bis dahin füllt der Level-Rest die
    KB-Präferenz auf.)"""
    impl = SESSION_FILLING | BLOCK_IMPLEMENTED          # nur dosierbare Formate (Ladders/Komplexe → Naht 4)
    level_impl = [f for f in _LEVEL_FORMATS[level] if f in impl]
    eq = _EQUIPMENT_FORMATS.get(equipment, set())
    if not eq:
        return level_impl
    preferred = [f for f in level_impl if f in eq]
    rest = [f for f in level_impl if f not in eq]
    return preferred + rest


def pick_conditioning_formats(level: int, equipment: str, n: int) -> list[str]:
    """n Formate für die Conditioning-Tage einer Woche — aufeinanderfolgend verschieden
    (zyklisch durch den Pool; nie 2× direkt hintereinander, solange Pool ≥ 2). Equipment-
    Bevorzugung + Level + nur implementierte Formate. Durch die weiche Bevorzugung (Level-Rest
    füllt auf) ist der Pool praktisch immer ≥ 2."""
    pool = _conditioning_pool(level, equipment) or ["amrap"]
    return [pool[i % len(pool)] for i in range(n)]


# ── Multi-Format-Aufteilung langer C-Tage (Naht 4d) ───────────────────────────
# Maximaldauer pro Format am Stück (Min). Länger ⇒ auf 2 Segmente aufteilen.
# Komplexe ausgelassen (TODO(mvp7-komplexe): nicht im Pool, braucht vordefinierte Ketten).
_FORMAT_MAX_MIN: dict[str, int] = {
    "amrap": 20, "density": 30, "tabata": 20, "intervalle": 25, "ladders": 20, "zirkel": 30,
}

_SEGMENT_MIN = 10   # jedes Format-Segment ≥ 10 Min


def pick_second_format(level: int, equipment: str, exclude: str) -> str | None:
    """Zweitformat für einen langen C-Tag (Naht 4d): **AMRAP bevorzugt**, wenn im Level-Pool —
    sonst das nächste Pool-Format (weiche Equipment-Bevorzugung wie Naht 3), in jedem Fall
    ≠ `exclude`. Kein anderes Format verfügbar → None (Aufrufer füllt dann 1 Segment voll)."""
    pool = [f for f in _conditioning_pool(level, equipment) if f != exclude]
    if not pool:
        return None
    return "amrap" if "amrap" in pool else pool[0]


_BIG_FORMATS = ("zirkel", "density")   # Max 30 — Ausweich-Erstformat für lange Sessions (Zirkel bevorzugt)


def _try_split(target_min: int, first: str, level: int, equipment: str) -> list[tuple[str, int]] | None:
    """Split-Versuch mit gegebenem Erstformat + AMRAP-bevorzugtem Zweitformat. Gibt die Segmente
    zurück, wenn alles innerhalb der Maxima liegt (Segment ≤ Max[first] bzw. ≤ Max[second]),
    sonst None (Erstformat deckt die Zeit nicht regelkonform ab)."""
    max1 = _FORMAT_MAX_MIN.get(first)
    if max1 is None:
        return None
    if target_min <= max1:
        return [(first, target_min)]
    second = pick_second_format(level, equipment, exclude=first)
    if second is None:
        return None
    seg1 = min(max1, target_min - _SEGMENT_MIN)         # dem zweiten Segment mind. 10 Min lassen
    seg2 = target_min - seg1
    if seg2 > _FORMAT_MAX_MIN.get(second, 0):
        return None                                     # zweites Segment über seinem Maximum → ungültig
    return [(first, seg1), (second, seg2)]


def split_conditioning_segments(target_min: int, first_format: str, level: int,
                                equipment: str) -> list[tuple[str, int]]:
    """Reine C-Tage: `target_min` (= session_dauer_min − Warmup) auf 1 oder 2 Format-Segmente.

    Normalfall — das Rotations-Erstformat (Naht 3) bleibt: ≤ Max[first] → 1 Segment über die volle
    Zeit; sonst 2 Segmente (erstes bis zu seinem Maximum, zweites kriegt den Rest — jedes ≥ 10 Min,
    5-Min-Raster, **nie ein Rumpf < 10**, z.B. 35/density → 25+10, nicht 30+5; Zweitformat ≠ erstes,
    AMRAP-bevorzugt).

    **Kapazitätsbewusst NUR wenn nötig:** deckt das Rotations-Erstformat + das AMRAP-bevorzugte
    Zweitformat die Zeit nicht innerhalb beider Maxima ab (lange Session, kleine Maxima), wird auf ein
    großes Erstformat (Zirkel 30 bevorzugt, sonst Density 30) aus dem Level-Pool ausgewichen — z.B.
    50 Min, Erstformat-Pool nur Max-20 → Zirkel/Density 30 + AMRAP 20. Bei kurzen/mittleren Sessions
    greift das NICHT → Naht-3-Rotation und die Variation der 2 C-Tage bleiben unangetastet.

    Deckt auch das große Erstformat die Zeit nicht ab → ValueError (melden, nicht still strecken/kürzen).

    Tabata-Granularität (4-Min-Blöcke) realisiert `block_count` beim Füllen; die Segment-Dauer bleibt
    auf dem 5-Min-Raster (Praxis-Targets 10/20/35/50 sind Vielfache von 5)."""
    segs = _try_split(target_min, first_format, level, equipment)
    if segs is not None:
        return segs                                      # Rotations-Erstformat deckt ab → unverändert
    pool = _conditioning_pool(level, equipment)
    for big in _BIG_FORMATS:                             # Zirkel zuerst, dann Density (Max 30)
        if big in pool and big != first_format:
            segs = _try_split(target_min, big, level, equipment)
            if segs is not None:
                return segs
    raise ValueError(
        f"Conditioning-Zeit {target_min} min im Level-{level}/{equipment}-Pool nicht durch "
        f"max. 2 Formate (je ≤ Maximum) abdeckbar — Pool={pool}")


def conditioning_pool(uebungen_gefiltert: dict[str, list[dict]]) -> list[dict]:
    """ÜBUNGS-Pool für den Metcon-Selektor (MVP-7 Naht 4): alle conditioning-tauglichen
    Übungen aus den gefilterten Pattern-Buckets — `pattern == "conditioning"` ODER
    `conditioning_friendly == true`. Dedup nach id (eine Übung kann durch den
    Pattern-Fallback in mehreren Buckets liegen), Reihenfolge des ersten Auftretens erhalten.
    Naht 4a: Helfer existiert, ist aber noch NICHT verdrahtet (4b/4c)."""
    pool: dict[str, dict] = {}
    for exs in uebungen_gefiltert.values():
        for ex in exs:
            if ex.get("pattern") == "conditioning" or ex.get("conditioning_friendly"):
                pool.setdefault(ex["id"], ex)
    return list(pool.values())


def conditioning_target_min(session_min: int) -> int:
    """Ziel-Arbeitsdauer (Min) für REINE Conditioning-Tage: die vom Klienten gewählte
    Session-Dauer minus Warmup. KEINE Level-Deckelung (Level steuert Format/Work:Rest/
    skill_level, NICHT die Dauer)."""
    return session_min - WARMUP_MIN


def block_count(format_name: str, target_min: int) -> int:
    """Blockzahl, die in die Ziel-Dauer passt: n Blöcke + (n−1)×60 s Pause ≤ target.
    Mindestens 2 Blöcke."""
    block_min = _BLOCK_DAUER_MIN[format_name]
    n = (target_min + _REST_MIN) // (block_min + _REST_MIN)
    return max(2, n)


def block_params(format_name: str) -> dict:
    return _BLOCK_PARAMS[format_name]


def level_work_rest(level: int) -> tuple[int, int]:
    """Level → (Arbeit s, Pause s) für Work:Rest-Formate (Intervall). Konsumiert in
    plan_assembler._format_notiz (intervalle-Notiz)."""
    return _LEVEL_WORK_REST[level]
