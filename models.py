"""
Pydantic-Modelle für das Buddensiek Performance KI-Trainingsplan-System.

KlientenInput   — validiert den Typeform-Webhook-Payload (nach Parsing)
ClaudeOutput    — validiert was Claude zurückgibt (exercise_ids + notizen)
Plan            — vollständiger 4-Wochen-Plan der in Supabase gespeichert wird
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS — exakt wie die Typeform Choice-Labels
# Ändere hier, nicht im Code — alle Module importieren von hier
# ═══════════════════════════════════════════════════════════════════════════════

class Hauptziel(str, Enum):
    muskelaufbau = "muskelaufbau"
    fettabbau    = "fettabbau"
    recomp       = "recomp"
    longevity    = "longevity"   # ersetzt ausdauer + gesundheit (Spec Thema 4)


class Equipment(str, Enum):
    gym        = "gym"
    home_gym   = "home_gym"
    kettlebell = "kettlebell"
    bodyweight = "bodyweight"
    travel     = "travel"
    hybrid     = "hybrid"


class Trainingsjahre(str, Enum):
    keine          = "keine"           # 0 Jahre → Level-Cap: 1
    unter_1        = "unter_1"         # < 1 Jahr → Level-Cap: 2
    ein_bis_zwei   = "ein_bis_zwei"    # 1–2 Jahre → Level-Cap: 3
    drei_bis_fuenf = "drei_bis_fuenf"  # 3–5 Jahre → Level-Cap: 4
    fuenf_plus     = "fuenf_plus"      # 5+ Jahre → kein Cap


class VerletzungsBereich(str, Enum):
    knie        = "knie"
    schulter    = "schulter"
    wirbelsaeule = "wirbelsäule"
    huefte      = "hüfte"
    ellenbogen  = "ellenbogen"
    handgelenk  = "handgelenk"
    hals        = "hals"
    knoechel    = "knöchel"


# ═══════════════════════════════════════════════════════════════════════════════
# KLIENTEN INPUT — kommt vom Typeform-Webhook (nach parsers.py)
# Typeform field.ref → Python-Feldname: immer snake_case, kein Umlaut
# ═══════════════════════════════════════════════════════════════════════════════

class KlientenInput(BaseModel):

    # ── Hidden fields (Typeform hidden fields) ─────────────────────────────
    # Typeform ref: client_id
    client_id: str = Field(..., description="UUID — wird von unserem System als hidden field gesetzt")

    # ── Basis-Infos ────────────────────────────────────────────────────────
    # Typeform ref: vorname
    vorname: str = Field(..., min_length=1, max_length=50)

    # Typeform ref: alter
    alter: int = Field(..., ge=18, le=80)

    # ── Trainingspräferenzen ───────────────────────────────────────────────
    # Typeform ref: hauptziel
    # Typeform Choice-Labels: "muskelaufbau" | "fettabbau" | "recomp" | "longevity"
    hauptziel: Hauptziel

    # Typeform ref: tage_pro_woche
    tage_pro_woche: int = Field(..., ge=3, le=6)

    # Typeform ref: session_dauer_min
    # Typeform Choice-Labels: "20" | "30" | "45" | "60"
    session_dauer_min: Literal[20, 30, 45, 60]

    # Typeform ref: equipment
    # Typeform Choice-Labels: "gym" | "home_gym" | "kettlebell" | "bodyweight" | "travel" | "hybrid"
    equipment: Equipment

    # Typeform ref: trainingsjahre
    # Typeform Choice-Labels: "keine" | "unter_1" | "ein_bis_zwei" | "drei_plus"
    trainingsjahre: Trainingsjahre

    # Typeform ref: schwachstelle
    # TODO(v15-schwachstelle): dormant — Schwachstellen-Fokus-Tag gestrichen (2026-06-11),
    # 5T = Ganzkörper-Akzent. Feld bleibt für die V1.5-Idee (BACKLOG), kein Konsument.
    # Typeform Choice-Labels: "arme" | "brust" | "ruecken" | "schultern" | "beine"
    schwachstelle: Optional[Literal["arme", "brust", "ruecken", "schultern", "beine"]] = None

    # ── Gesundheit & Recovery ──────────────────────────────────────────────
    # Typeform ref: stress_level
    # Typeform: Skala 1–10
    stress_level: int = Field(..., ge=1, le=10, description="1=sehr niedrig, 10=extrem hoch")

    # Typeform ref: schlaf_stunden
    # Typeform Choice-Labels: "4" | "5" | "6" | "7" | "8" | "9" | "10"
    schlaf_stunden: float = Field(..., ge=4.0, le=10.0)

    # Typeform ref: verletzungen
    # Typeform: Multiple Choice
    # Typeform Choice-Labels: "knie" | "schulter" | "wirbelsäule" | "hüfte" | "ellenbogen" | "handgelenk" | "hals" | "knöchel"
    verletzungen: list[VerletzungsBereich] = Field(default_factory=list)

    # Typeform ref: medizinische_diagnosen
    # Typeform: Open text (optional)
    medizinische_diagnosen: Optional[str] = Field(None, max_length=500)

    # ── Alltag & Kontext (für Claude-Personalisierung) ─────────────────────
    # Typeform ref: motivation
    # Typeform: Open text (optional) — "Was ist dein größter Antrieb?"
    motivation: Optional[str] = Field(None, max_length=500)

    # Typeform ref: aktuelles_training
    # Typeform: Open text (optional) — "Was machst du aktuell sportlich?"
    aktuelles_training: Optional[str] = Field(None, max_length=300)

    # Typeform refs: home_gym_items | travel_items | kettlebell_items | hybrid_items
    # Spezifische Geräte aus dem Follow-Up zur equipment-Frage
    # Beispiele: "barbell", "dumbbells", "pull_up_bar", "cables", "resistance_bands", "trx", ...
    equipment_items: list[str] = Field(default_factory=list)

    # ── PST — Physical Screening Test ─────────────────────────────────────
    # Durchgeführt bevor das Formular ausgefüllt wird (oder am selben Tag)
    # Typeform ref: kniebeugen_wdh
    kniebeugen_wdh: int = Field(..., ge=0, le=100, description="Max Kniebeugen in 60 Sek.")

    # Typeform ref: pushups_wdh
    pushups_wdh: int = Field(..., ge=0, le=100, description="Max Push-Ups in 60 Sek.")

    # Typeform ref: situps_wdh
    situps_wdh: int = Field(..., ge=0, le=100, description="Max Sit-Ups in 60 Sek.")

    # Typeform ref: burpees_wdh
    burpees_wdh: int = Field(..., ge=0, le=50, description="Max Burpees in 60 Sek.")

    # Typeform ref: plank_sek
    plank_sek: int = Field(..., ge=0, le=600, description="Plank-Haltezeit in Sekunden")


# ═══════════════════════════════════════════════════════════════════════════════
# CLAUDE OUTPUT — minimales Schema was Claude zurückgeben MUSS
# Python ergänzt danach sets/reps/rir/coaching_cues aus exercises.json
# ═══════════════════════════════════════════════════════════════════════════════

class UebungAuswahl(BaseModel):
    reihenfolge: int = Field(..., ge=1, le=10)
    exercise_id: str = Field(..., description="Muss in exercises.json existieren — wird validiert")
    notiz: str = Field(default="", max_length=300, description="Klient-spezifische Coaching-Notiz von Claude")


class SessionAuswahl(BaseModel):
    session_id: str
    uebungen: list[UebungAuswahl]


class ClaudeOutput(BaseModel):
    sessions: list[SessionAuswahl]

    @model_validator(mode="after")
    def validate_exercise_ids(self) -> ClaudeOutput:
        import json, pathlib
        exercises_path = pathlib.Path(__file__).parent / "data" / "exercises.json"
        if not exercises_path.exists():
            return self  # Skip in Tests ohne exercises.json
        data = json.loads(exercises_path.read_text())
        valid_ids = {ex["id"] for ex in data["exercises"]}
        for session in self.sessions:
            for uebung in session.uebungen:
                if uebung.exercise_id not in valid_ids:
                    raise ValueError(
                        f"Claude hat eine unbekannte exercise_id zurückgegeben: '{uebung.exercise_id}'. "
                        f"Nur IDs aus exercises.json sind erlaubt."
                    )
        return self


# ═══════════════════════════════════════════════════════════════════════════════
# PLAN MODELS — vollständiger Plan der in Supabase gespeichert wird
# ═══════════════════════════════════════════════════════════════════════════════

class WarmUpUebung(BaseModel):
    name: str
    saetze: Optional[int] = None
    wdh: Optional[int] = None
    dauer_sek: Optional[int] = None
    seiten: Optional[int] = None


class WarmUp(BaseModel):
    protokoll: Literal["kraft", "mobility", "kettlebell", "calisthenics"]
    dauer_min: int = Field(..., ge=3, le=30)
    uebungen: list[WarmUpUebung]


class HauptUebung(BaseModel):
    reihenfolge: int = Field(..., ge=1, le=10)
    exercise_id: str
    name: str
    saetze: int = Field(..., ge=1, le=15)
    saetze_typ: Literal["saetze", "runden"] = "saetze"   # Conditioning zählt Runden, Kraft Sätze
    wert: str = Field(..., description="'8-12' (Bereich) · '10' (Einzelwert) · Prosa (bei einheit=format)")
    einheit: Literal["wiederholungen", "sekunden", "meter", "format"]
    rir: Optional[float] = Field(default=None, ge=0, le=6, description="RIR (Reps in Reserve, 0.5-Raster) für Kraftsätze; None für Conditioning/Metcon und Zeit-Holds (Thema 6/Befund 7). Intern rechnet die Logik in RPE; RIR = 10 − RPE.")
    tempo: str = Field(..., description="z.B. '2-1-1-0' oder 'halten'")
    pausenzeit_sek: int = Field(..., ge=0, le=300)
    coaching_cues: list[str] = Field(..., min_length=1, max_length=5)
    notiz: str = Field(default="", max_length=300)


class Cardio(BaseModel):
    typ: Literal["liss", "hiit"]
    dauer_min: int = Field(..., ge=10, le=60)
    beschreibung: str


class CoolDownUebung(BaseModel):
    name: str
    dauer_sek: Optional[int] = None
    seiten: Optional[int] = None


class CoolDown(BaseModel):
    dauer_min: int = Field(..., ge=3, le=15)
    uebungen: list[CoolDownUebung]


class PSTTest(BaseModel):
    test: Literal["kniebeugen", "pushups", "situps", "burpees", "plank"]
    einheit: Literal["wiederholungen", "sekunden"]
    ergebnis: Optional[int] = None  # wird nach Re-Test gefüllt


class MetconBlock(BaseModel):
    """Konditionierungs-Finisher innerhalb einer Recomp-Session (nach dem Kraftteil)."""
    typ: Literal[
        "amrap", "intervalle", "zirkel",                          # Session-füllend
        "tabata", "density", "komplexe", "ladders",               # Block-Formate (Spec Thema 6)
    ]
    format_notiz: str
    uebungen: list[HauptUebung]


class Session(BaseModel):
    session_id: str
    tag: Literal["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"]
    session_typ: Literal[
        "kraft",
        "amrap", "zirkel", "intervalle",                          # Conditioning Session-füllend
        "tabata", "density", "komplexe", "ladders",               # Conditioning Block-Formate (Thema 6)
        "zone2", "athletik",                                      # Longevity (Thema 4/6)
    ] = "kraft"
    fokus: str                       # interner Routing-Key (warm_up/cool_down/cardio/zone-Parsing)
    fokus_anzeige: str               # kundenseitiges Label (logic.fokus_labels) — fokus bleibt intern
    format_notiz: Optional[str] = None
    dauer_min_geschaetzt: int = Field(..., ge=20, le=120)
    warm_up: WarmUp
    haupt_uebungen: list[HauptUebung]
    metcon_block: Optional[MetconBlock] = None   # Recomp: Finisher nach Kraftteil
    conditioning_block_2: Optional[MetconBlock] = None   # Naht 4d: 2. Format-Segment langer reiner C-Tage
    cardio: Optional[Cardio] = None
    cool_down: CoolDown
    pst_tests: Optional[list[PSTTest]] = None


class Woche(BaseModel):
    woche_nummer: int = Field(..., ge=1, le=4)
    block_typ: Literal["akkumulation", "progression", "intensivierung", "deload"]
    volumen_stufe: Literal["sehr_niedrig", "niedrig", "mittel", "hoch"]
    ziel_saetze: int = Field(..., ge=1, le=20)
    ziel_rir: float = Field(..., ge=0, le=6)
    sessions: list[Session]


class KlientenSnapshot(BaseModel):
    """Eingefroren bei Plan-Erstellung — damit der Plan auch nach Updates lesbar bleibt."""
    level: int = Field(..., ge=1, le=4)
    ziel: Hauptziel
    equipment: Equipment
    split_typ: str
    tage_pro_woche: int
    session_dauer_min: int
    verletzungen: list[VerletzungsBereich] = Field(default_factory=list)
    # stress/schlaf_stunden: aus dem Kunden-Snapshot ENTFERNT (Blocker 4) — totes Signal (Recovery
    # entkoppelt), im Contract irreführend. KlientenInput behält sie (Intake) bis zur Fillout-Karte.


class Plan(BaseModel):
    plan_id: str
    client_id: str
    erstellt_am: str  # ISO 8601: "2026-05-28T10:00:00Z"
    block_nummer: int = Field(..., ge=1)
    klient_snapshot: KlientenSnapshot
    wochen: list[Woche] = Field(..., min_length=4, max_length=4)

    @field_validator("wochen")
    @classmethod
    def validate_wochen_typen(cls, v: list[Woche]) -> list[Woche]:
        expected = ["akkumulation", "progression", "intensivierung", "deload"]
        typen = [w.block_typ for w in v]
        if typen != expected:
            raise ValueError(
                f"Wochen-Reihenfolge falsch. Erwartet: {expected}, erhalten: {typen}"
            )
        return v
