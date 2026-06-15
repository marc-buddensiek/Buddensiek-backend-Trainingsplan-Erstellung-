"""
Conditioning-Format-Baukasten (MVP-7 Naht 2c) — Spec Thema 6.

Level→Format/Work:Rest/Dauer-Map + Block-Stapel-Logik. Geteilt von plan_assembler
(Dosierung); ab Naht 4 auch von split_selector (echte Rotation, ersetzt den
trivialen Platzhalter-Pick hier).

Formate (7): Session-füllend (amrap/zirkel/intervalle) + Block-Formate
(tabata/density/ladders/komplexe). In 2c sind nur **Tabata + Density** block-dosierbar;
Ladders + Komplexe bleiben gültige Enum-Formate, ihre Block-Dauern kommen mit Naht 4.

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
BLOCK_IMPLEMENTED = {"tabata", "density"}                # block-dosierbar in 2c (Naht 4: + ladders/komplexe)
CONDITIONING = SESSION_FILLING | BLOCK_IMPLEMENTED       # was als metabolic/Conditioning gilt

# Level → verfügbare Formate (Reihenfolge wie Spec-Tabelle Thema 6)
_LEVEL_FORMATS: dict[int, list[str]] = {
    1: ["intervalle", "zirkel"],
    2: ["intervalle", "amrap", "density", "ladders"],
    3: ["amrap", "zirkel", "density", "ladders", "tabata"],
    4: ["amrap", "tabata", "density", "komplexe"],
}

# Level → (Work, Rest) Sek — repräsentativ (erstes Spec-Paar). Gilt für Work:Rest-Formate
# (Intervall/Circuit); Block-Formate mit festem Timing ignorieren das. Voll konsumiert ab
# Naht 4 (Intervall-Dosierung + Rotation); in 2c Bestandteil der Map.
_LEVEL_WORK_REST: dict[int, tuple[int, int]] = {1: (20, 40), 2: (40, 20), 3: (40, 20), 4: (45, 15)}

# (Die früheren Level-Dauer-Bänder steuern die Dauer NICHT mehr — Dauer = session_dauer_min.
#  Verbleiben als reine Doku-Notiz in COACHING_SPEC Thema 6.)

# Block-Formate: feste Block-Dauer (Min) — Format-eigenes Timing schlägt Level-Work:Rest.
_BLOCK_DAUER_MIN: dict[str, int] = {"tabata": 4, "density": 5}

# Per-Block-Parameter (eine Übung je Block). saetze/wdh sind Anzeige; keine RPE (Thema 6).
_BLOCK_PARAMS: dict[str, dict] = {
    "tabata":  {"saetze": 8, "wdh": "20 s an / 10 s aus"},                       # 8 Runden = 4 Min, fix
    "density": {"saetze": 1, "wdh": "5 Min — max. Wiederholungen bei festem Gewicht"},
}

REST_BETWEEN_BLOCKS_SEK = 60   # ~60 s Pause zwischen Blöcken
_REST_MIN = 1                  # = 60 s in Minuten (für die Dauer-Rechnung)


def is_conditioning(session_typ: str) -> bool:
    return session_typ in CONDITIONING


def is_block_format(session_typ: str) -> bool:
    return session_typ in BLOCK_IMPLEMENTED


def trivial_format_pick(level: int) -> str:
    """Platzhalter-Pick — TODO(mvp7-formate): Naht 4 ersetzt das durch echte Rotation
    (Block-Rotation, nie 2× hintereinander, Equipment-Bevorzugung). Hier deterministisch:
    erstes implementiertes Block-Format der Level-Map, sonst erstes (Session-füllendes)."""
    formate = _LEVEL_FORMATS[level]
    for f in formate:
        if f in BLOCK_IMPLEMENTED:
            return f
    return formate[0]


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


def block_session_dauer(format_name: str, target_min: int) -> int:
    """Reale Conditioning-Arbeitsdauer (Min): n Blöcke à Block-Dauer + (n−1)×60 s Pause.
    TODO(mvp7-cleanup): aktuell nur in Tests benutzt — die angezeigte Dauer kommt aus
    session_dauer_min, nicht aus dieser Summe. Bei Naht 4 zusammenführen."""
    n = block_count(format_name, target_min)
    return n * _BLOCK_DAUER_MIN[format_name] + (n - 1) * _REST_MIN


def block_params(format_name: str) -> dict:
    return _BLOCK_PARAMS[format_name]


def level_work_rest(level: int) -> tuple[int, int]:
    # TODO(mvp7-cleanup): _LEVEL_WORK_REST hat aktuell KEINEN Produktions-Leser (nur Tests).
    # intervalle hardcodiert sein Work:Rest in plan_assembler._format_notiz — bei Naht 4 verdrahten.
    return _LEVEL_WORK_REST[level]
