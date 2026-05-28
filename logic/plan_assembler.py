"""
ClaudeOutput + berechnete Parameter → vollständiger Plan (4 Wochen)

Claude wählt die Übungen für Block 1 einmal aus.
Dieselben Übungen laufen durch alle 4 Wochen — nur Sätze/RPE ändern sich (3:1-Wave).
Python ergänzt: name, coaching_cues, wdh, tempo, pausenzeit, warm_up, cardio, cool_down.
"""

from __future__ import annotations
import json
import pathlib
import uuid
from datetime import datetime, timezone

from models import (
    KlientenInput, ClaudeOutput, Hauptziel, Equipment,
    Plan, Woche, Session, KlientenSnapshot,
    WarmUp, WarmUpUebung, HauptUebung, Cardio, CoolDown, CoolDownUebung, PSTTest,
)
from logic.volume_calculator import berechne_volumen


_EXERCISES_PATH = pathlib.Path(__file__).parent.parent / "data" / "exercises.json"

_WOCHEN_TYPEN = ["akkumulation", "progression", "intensivierung", "deload"]

# Trainingstage je nach Tagesanzahl
_TAGE_VERTEILUNG = {
    2: ["montag", "donnerstag"],
    3: ["montag", "mittwoch", "freitag"],
    4: ["montag", "dienstag", "donnerstag", "freitag"],
    5: ["montag", "dienstag", "mittwoch", "freitag", "samstag"],
    6: ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag"],
}


# ── Wdh-Strings je Ziel + Pattern ─────────────────────────────────────────────

def _wdh(hauptziel: Hauptziel, pattern: str, reihenfolge: int) -> str:
    is_compound = reihenfolge == 1
    is_core = pattern == "core"
    is_carry = pattern == "carry"

    if is_carry:
        return "20m"
    if is_core:
        return "45sec"

    if hauptziel == Hauptziel.muskelaufbau:
        return "6-8" if is_compound else "10-12"
    elif hauptziel == Hauptziel.fettabbau:
        return "12-15"
    elif hauptziel == Hauptziel.ausdauer:
        return "15-20"
    else:  # gesundheit
        return "10-12"


# ── Tempo je Pattern ───────────────────────────────────────────────────────────

def _tempo(pattern: str) -> str:
    if pattern in ("squat", "hinge"):
        return "3-1-1-0"
    elif pattern in ("push_horizontal", "push_vertical"):
        return "3-1-1-0"
    elif pattern in ("pull_horizontal", "pull_vertical"):
        return "2-0-1-1"
    elif pattern == "single_leg":
        return "2-1-1-0"
    elif pattern == "core":
        return "halten"
    elif pattern == "carry":
        return "gleichmäßig"
    return "2-1-1-0"


# ── Pausenzeit je Position + Pattern ─────────────────────────────────────────

def _pausenzeit(reihenfolge: int, pattern: str) -> int:
    if pattern in ("core", "carry"):
        return 45
    if reihenfolge == 1:
        return 180  # Hauptübung braucht mehr Pause
    if reihenfolge == 2:
        return 120
    return 60


# ── Warm-Up je Equipment ──────────────────────────────────────────────────────

def _warm_up(equipment: Equipment, fokus: str) -> WarmUp:
    if equipment == Equipment.kettlebell:
        return WarmUp(
            protokoll="kettlebell",
            dauer_min=8,
            uebungen=[
                WarmUpUebung(name="Halo", saetze=2, wdh=8, seiten=None),
                WarmUpUebung(name="Goblet Squat (leicht)", saetze=2, wdh=10),
                WarmUpUebung(name="Hip Hinge Pattern (ohne Gewicht)", saetze=2, wdh=10),
                WarmUpUebung(name="Light Swing", saetze=2, wdh=10),
            ],
        )
    elif equipment in (Equipment.bodyweight, Equipment.travel):
        return WarmUp(
            protokoll="calisthenics",
            dauer_min=5,
            uebungen=[
                WarmUpUebung(name="Squat-to-Stand", saetze=2, wdh=8),
                WarmUpUebung(name="World's Greatest Stretch", dauer_sek=30, seiten=2),
                WarmUpUebung(name="Push-Up Activation (langsam)", saetze=2, wdh=5),
                WarmUpUebung(name="Hip Circle", dauer_sek=20, seiten=2),
            ],
        )
    elif equipment == Equipment.hybrid:
        return WarmUp(
            protokoll="kettlebell",
            dauer_min=7,
            uebungen=[
                WarmUpUebung(name="Halo", saetze=2, wdh=6),
                WarmUpUebung(name="Goblet Squat (leicht)", saetze=2, wdh=8),
                WarmUpUebung(name="World's Greatest Stretch", dauer_sek=30, seiten=2),
                WarmUpUebung(name="Light Swing", saetze=2, wdh=8),
            ],
        )
    else:  # gym, home_gym
        ist_upper = any(w in fokus.lower() for w in ("upper", "push", "pull", "oberkörper"))
        if ist_upper:
            return WarmUp(
                protokoll="kraft",
                dauer_min=8,
                uebungen=[
                    WarmUpUebung(name="Band Pull-Apart", saetze=2, wdh=15),
                    WarmUpUebung(name="Scapula Push-Up", saetze=2, wdh=10),
                    WarmUpUebung(name="Face Pull (leicht)", saetze=2, wdh=12),
                    WarmUpUebung(name="Arm Circles", dauer_sek=30, seiten=2),
                ],
            )
        else:
            return WarmUp(
                protokoll="kraft",
                dauer_min=8,
                uebungen=[
                    WarmUpUebung(name="Hip Circle", dauer_sek=20, seiten=2),
                    WarmUpUebung(name="Glute Bridge (Aktivierung)", saetze=2, wdh=15),
                    WarmUpUebung(name="Leg Swing", dauer_sek=30, seiten=2),
                    WarmUpUebung(name="Goblet Squat (leicht)", saetze=2, wdh=8),
                ],
            )


# ── Cool-Down je Session-Fokus ────────────────────────────────────────────────

def _cool_down(fokus: str) -> CoolDown:
    ist_upper = any(w in fokus.lower() for w in ("upper", "push", "pull", "oberkörper"))
    ist_conditioning = any(w in fokus.lower() for w in ("conditioning", "hiit", "zone"))

    if ist_upper:
        return CoolDown(
            dauer_min=5,
            uebungen=[
                CoolDownUebung(name="Brust-Stretch an der Wand", dauer_sek=30, seiten=2),
                CoolDownUebung(name="Lat-Stretch (Arme über Kopf)", dauer_sek=30, seiten=2),
                CoolDownUebung(name="Schulter Cross-Body Stretch", dauer_sek=30, seiten=2),
            ],
        )
    elif ist_conditioning:
        return CoolDown(
            dauer_min=5,
            uebungen=[
                CoolDownUebung(name="Ruhiges Gehen (Atemkontrolle)", dauer_sek=60),
                CoolDownUebung(name="Hip Flexor Stretch", dauer_sek=30, seiten=2),
                CoolDownUebung(name="Child's Pose", dauer_sek=45),
            ],
        )
    else:  # lower body
        return CoolDown(
            dauer_min=5,
            uebungen=[
                CoolDownUebung(name="Hip Flexor Stretch", dauer_sek=45, seiten=2),
                CoolDownUebung(name="Hamstring Stretch", dauer_sek=30, seiten=2),
                CoolDownUebung(name="Pigeon Pose", dauer_sek=30, seiten=2),
            ],
        )


# ── Cardio je Session-Fokus + Ziel ───────────────────────────────────────────

def _cardio(hauptziel: Hauptziel, fokus: str) -> Cardio | None:
    ist_conditioning = any(w in fokus.lower() for w in ("conditioning", "hiit"))
    ist_zone2 = "zone" in fokus.lower()

    if ist_conditioning:
        return Cardio(
            typ="hiit",
            dauer_min=12,
            beschreibung="4 Runden: 20 Sek. All-out / 40 Sek. Pause — Burpees, Kettlebell Swings oder Sprints",
        )
    if ist_zone2:
        return Cardio(
            typ="liss",
            dauer_min=30,
            beschreibung="Zone 2 — Tempo halten bei dem du dich noch unterhalten könntest (ca. 120-135 bpm)",
        )
    if hauptziel == Hauptziel.fettabbau:
        return Cardio(
            typ="liss",
            dauer_min=15,
            beschreibung="10 Min ruhiges Gehen oder Bike als aktive Erholung nach der Session",
        )
    return None  # muskelaufbau / ausdauer: kein Cardio im Kraft-Block


# ── PST Re-Test (nur Deload-Woche) ────────────────────────────────────────────

_PST_TESTS = [
    PSTTest(test="kniebeugen", einheit="wiederholungen"),
    PSTTest(test="pushups",    einheit="wiederholungen"),
    PSTTest(test="situps",     einheit="wiederholungen"),
    PSTTest(test="burpees",    einheit="wiederholungen"),
    PSTTest(test="plank",      einheit="sekunden"),
]


# ── Session-Dauer schätzen ─────────────────────────────────────────────────────

def _schaetze_dauer(n_uebungen: int, saetze: int, warm_up_min: int, cool_down_min: int, cardio_min: int) -> int:
    # ~1.5 min Arbeit + Pause pro Satz
    haupt_min = n_uebungen * saetze * 2
    total = warm_up_min + haupt_min + cool_down_min + cardio_min
    # Runden auf nächste 5 Minuten
    return min(120, max(20, round(total / 5) * 5))


# ── Hauptfunktion ─────────────────────────────────────────────────────────────

def assemble_plan(
    klient: KlientenInput,
    level: int,
    split: dict,           # {"split_typ": str, "sessions": list[dict]}
    claude_output: ClaudeOutput,
    block_nummer: int = 1,
) -> Plan:
    """
    Baut den vollständigen 4-Wochen-Plan aus Claude's Übungsauswahl + berechneten Parametern.
    """
    exercises_data = json.loads(_EXERCISES_PATH.read_text())
    ex_by_id = {e["id"]: e for e in exercises_data["exercises"]}

    # Claude's Auswahl als Dict: session_id → list[UebungAuswahl]
    claude_sessions = {s.session_id: s.uebungen for s in claude_output.sessions}

    tage = _TAGE_VERTEILUNG.get(klient.tage_pro_woche, list(_TAGE_VERTEILUNG[4]))
    wochen: list[Woche] = []

    for woche_idx, woche_typ in enumerate(_WOCHEN_TYPEN, start=1):
        volumen = berechne_volumen(klient, level, woche_typ)
        saetze = volumen["ziel_saetze"]
        rpe    = volumen["ziel_rpe"]
        stufe  = volumen["volumen_stufe"]

        sessions: list[Session] = []
        ist_deload = woche_typ == "deload"

        for session_idx, session_template in enumerate(split["sessions"]):
            original_id = session_template["session_id"]  # "w1_s1"
            session_id  = f"w{woche_idx}_s{session_idx + 1}"
            fokus       = session_template["fokus"]
            tag         = tage[session_idx] if session_idx < len(tage) else "samstag"

            # Claude's Übungsauswahl für diese Session (aus Woche 1 — gilt für ganzen Block)
            uebungen_auswahl = claude_sessions.get(original_id, [])

            haupt_uebungen: list[HauptUebung] = []
            for u in uebungen_auswahl:
                ex = ex_by_id.get(u.exercise_id)
                if not ex:
                    continue

                pattern = ex["pattern"]
                haupt_uebungen.append(
                    HauptUebung(
                        reihenfolge=u.reihenfolge,
                        exercise_id=u.exercise_id,
                        name=ex["name"],
                        saetze=1 if ist_deload else saetze,
                        wdh=_wdh(klient.hauptziel, pattern, u.reihenfolge),
                        rpe=max(4, rpe - 2) if ist_deload else rpe,
                        tempo=_tempo(pattern),
                        pausenzeit_sek=_pausenzeit(u.reihenfolge, pattern),
                        coaching_cues=ex["coaching_cues"][:3],
                        notiz=u.notiz,
                    )
                )

            warm_up   = _warm_up(klient.equipment, fokus)
            cardio    = _cardio(klient.hauptziel, fokus)
            cool_down = _cool_down(fokus)
            cardio_min = cardio.dauer_min if cardio else 0

            dauer = _schaetze_dauer(
                n_uebungen=len(haupt_uebungen),
                saetze=saetze,
                warm_up_min=warm_up.dauer_min,
                cool_down_min=cool_down.dauer_min,
                cardio_min=cardio_min,
            )

            # PST Re-Test nur in letzter Session der Deload-Woche
            pst_tests = None
            if ist_deload and session_idx == len(split["sessions"]) - 1:
                pst_tests = _PST_TESTS

            sessions.append(
                Session(
                    session_id=session_id,
                    tag=tag,
                    fokus=fokus,
                    dauer_min_geschaetzt=dauer,
                    warm_up=warm_up,
                    haupt_uebungen=haupt_uebungen,
                    cardio=cardio,
                    cool_down=cool_down,
                    pst_tests=pst_tests,
                )
            )

        wochen.append(
            Woche(
                woche_nummer=woche_idx,
                block_typ=woche_typ,
                volumen_stufe=stufe,
                ziel_saetze=saetze,
                ziel_rpe=rpe,
                sessions=sessions,
            )
        )

    snapshot = KlientenSnapshot(
        level=level,
        ziel=klient.hauptziel,
        equipment=klient.equipment,
        split_typ=split["split_typ"],
        tage_pro_woche=klient.tage_pro_woche,
        verletzungen=klient.verletzungen,
        stress=klient.stress_level,
        schlaf_stunden=klient.schlaf_stunden,
    )

    return Plan(
        plan_id=str(uuid.uuid4()),
        client_id=klient.client_id,
        erstellt_am=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        block_nummer=block_nummer,
        klient_snapshot=snapshot,
        wochen=wochen,
    )
