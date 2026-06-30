# SCHEMA-REFERENZ — JSON-Vertrag (Feld-Definitionen)

Quelle: models.py, Stand 61a744d (post-Naht W2). Verbatim-Auszug der Pydantic-Klassen, die den
ausgelieferten Plan-JSON definieren (plan.model_dump()). Die Beispiel-JSONs in examples/ sind die
genaue Wahrheit fürs Feld-Set; diese Referenz erklärt Typen/Constraints.

```python
class WarmUpUebung(BaseModel):
    name: str
    saetze: Optional[int] = None
    wert: str                                                          # Naht A1: wie HauptUebung — '8' (Wdh) · '30' (Sek)
    einheit: Literal["wiederholungen", "sekunden", "meter", "format"]  # WU nutzt praktisch wiederholungen|sekunden
    seiten: Optional[int] = None


class WarmUp(BaseModel):
    protokoll: Literal["kraft", "mobility", "kettlebell", "calisthenics"]
    dauer_min: int = Field(..., ge=3, le=30)
    uebungen: list[WarmUpUebung]


class HauptUebung(BaseModel):
    reihenfolge: int = Field(..., ge=1, le=10)
    exercise_id: str
    name: str
    saetze: Optional[int] = Field(default=None, ge=1, le=15)   # Naht W2: Kraft/Athletik IMMER gesetzt; Conditioning None (Runden am Block)
    saetze_typ: Optional[Literal["saetze", "runden"]] = None   # "saetze" bei Kraft/Athletik; None bei Conditioning
    wert: str = Field(..., description="'8-12' (Bereich) · '10' (Einzelwert) · Prosa (bei einheit=format)")
    einheit: Literal["wiederholungen", "sekunden", "meter", "format"]
    rir: Optional[float] = Field(default=None, ge=0, le=6, description="RIR (Reps in Reserve, 0.5-Raster) für Kraftsätze; None für Conditioning/Metcon und Zeit-Holds (Thema 6/Befund 7). Intern rechnet die Logik in RPE; RIR = 10 − RPE.")
    tempo: str = Field(..., description="z.B. '2-1-1-0' oder 'halten'")
    pausenzeit_sek: int = Field(..., ge=0, le=300)
    coaching_cues: list[str] = Field(..., min_length=1, max_length=5)
    notiz: str = Field(default="", max_length=300)
    seiten: Optional[int] = Field(default=None, description="Naht A2 (W12): >1 = pro Seite (unilateral); None = beidseitig/n.a. Bleibt None bis einseitig-Tagging in exercises.json (Phase 4, Wert-Arbeit).")


class Cardio(BaseModel):
    typ: Literal["liss", "hiit"]
    dauer_min: int = Field(..., ge=10, le=60)
    beschreibung: str


class CoolDownUebung(BaseModel):
    name: str
    wert: str                                                          # Naht A1: wie HauptUebung — '30' (Sek)
    einheit: Literal["wiederholungen", "sekunden", "meter", "format"]  # CD nutzt praktisch sekunden
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
    runden: Optional[int] = None              # Naht W2: Runden am BLOCK (zirkel/intervalle/tabata); None bei zeit-Formaten (amrap/density/ladders)
    runden_pause_sek: Optional[int] = None    # Pause nach jeder Runde/zwischen Blöcken (strukturiert statt Prosa)
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
    runden: Optional[int] = None              # Naht W2: Runden am Session-Level für session-füllende Conditioning-Tage (zirkel/…); None bei Kraft/zeit-Formaten
    runden_pause_sek: Optional[int] = None    # Pause nach jeder Runde (strukturiert statt Prosa)
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
```
