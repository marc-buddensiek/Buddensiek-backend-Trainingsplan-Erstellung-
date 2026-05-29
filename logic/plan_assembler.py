"""
ClaudeOutput + berechnete Parameter → vollständiger Plan (4 Wochen)

Claude wählt die Übungen für Block 1 einmal aus.
Dieselben Übungen laufen durch alle 4 Wochen — nur Sätze/RPE ändern sich.
Python ergänzt: name, coaching_cues, wdh, tempo, pausenzeit, warm_up, cardio, cool_down.
Mobility-Sessions werden hardcodiert ohne Claude-Input zusammengebaut.
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

_WOCHEN_TYPEN = ["akkumulation", "progression", "intensivierung", "peak"]

_TAGE_VERTEILUNG = {
    2: ["montag", "donnerstag"],
    3: ["montag", "mittwoch", "freitag"],
    4: ["montag", "dienstag", "donnerstag", "freitag"],
    5: ["montag", "dienstag", "mittwoch", "freitag", "samstag"],
    6: ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag"],
}


# ── Wdh-Strings je Ziel + Pattern ─────────────────────────────────────────────

def _wdh(hauptziel: Hauptziel, pattern: str, reihenfolge: int, session_typ: str = "kraft") -> str:
    if pattern == "carry":
        return "20m"
    if pattern == "core":
        return "45sec"

    if session_typ in ("zirkel", "amrap", "emom", "intervalle"):
        return "12-15"  # metabolisches Format → höheres Wdh-Spektrum

    is_compound = reihenfolge == 1
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

def _pausenzeit(reihenfolge: int, pattern: str, session_typ: str = "kraft") -> int:
    if session_typ in ("zirkel", "amrap", "emom"):
        return 30  # minimale Pause im Zirkel/Metabolischen Format
    if pattern in ("core", "carry"):
        return 45
    if reihenfolge == 1:
        return 180
    if reihenfolge == 2:
        return 120
    return 60


# ── Format-Notiz je Session-Typ ────────────────────────────────────────────────

def _format_notiz(session_typ: str, n_uebungen: int, saetze: int) -> str | None:
    if session_typ == "zirkel":
        return (
            f"{saetze} Runden Zirkel — alle {n_uebungen} Übungen nacheinander ohne Pause. "
            f"30 Sek. Pause nach jeder Runde. Anzahl der Runden notieren."
        )
    if session_typ == "amrap":
        return (
            f"12 Min. AMRAP — so viele Runden wie möglich mit allen {n_uebungen} Übungen. "
            f"Keine festgelegte Pause — eigenes Tempo. Runden am Ende notieren."
        )
    if session_typ == "emom":
        return (
            f"20 Min. EMOM — jede Minute eine Übung, Übungen rotieren. "
            f"Was in der Minute übrig ist = Pause. Saubere Technik vor Tempo."
        )
    if session_typ == "intervalle":
        return (
            "Intervalle: 30 Sek. Arbeit / 30 Sek. Pause — 5 Runden pro Übung. "
            "Intensität: 85-90% der maximalen Herzfrequenz."
        )
    return None


# ── Warm-Up je Equipment ──────────────────────────────────────────────────────

def _warm_up(equipment: Equipment, fokus: str) -> WarmUp:
    if equipment == Equipment.kettlebell:
        return WarmUp(
            protokoll="kettlebell",
            dauer_min=8,
            uebungen=[
                WarmUpUebung(name="Halo", saetze=2, wdh=8),
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


def _mobility_warm_up() -> WarmUp:
    return WarmUp(
        protokoll="mobility",
        dauer_min=10,
        uebungen=[
            WarmUpUebung(name="Cat-Cow (Wirbelsäulen-Aktivierung)", saetze=2, wdh=10),
            WarmUpUebung(name="Hip Circle", dauer_sek=30, seiten=2),
            WarmUpUebung(name="Arm Swings (vorwärts + rückwärts)", dauer_sek=30, seiten=2),
            WarmUpUebung(name="Neck Rolls (langsam)", dauer_sek=30),
        ],
    )


# ── Cool-Down je Session-Fokus ────────────────────────────────────────────────

def _cool_down(fokus: str) -> CoolDown:
    ist_upper = any(w in fokus.lower() for w in ("upper", "push", "pull", "oberkörper"))
    ist_conditioning = any(w in fokus.lower() for w in ("kondition", "conditioning", "hiit", "zone", "amrap", "emom", "intervalle"))

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
    else:  # lower body / full body
        return CoolDown(
            dauer_min=5,
            uebungen=[
                CoolDownUebung(name="Hip Flexor Stretch", dauer_sek=45, seiten=2),
                CoolDownUebung(name="Hamstring Stretch", dauer_sek=30, seiten=2),
                CoolDownUebung(name="Pigeon Pose", dauer_sek=30, seiten=2),
            ],
        )


def _mobility_cool_down() -> CoolDown:
    return CoolDown(
        dauer_min=8,
        uebungen=[
            CoolDownUebung(name="Supine Twist", dauer_sek=45, seiten=2),
            CoolDownUebung(name="Happy Baby Pose", dauer_sek=45),
            CoolDownUebung(name="Legs Up the Wall", dauer_sek=60),
        ],
    )


# ── Cardio je Session-Fokus + Ziel ───────────────────────────────────────────

def _cardio(hauptziel: Hauptziel, fokus: str) -> Cardio | None:
    ist_conditioning = any(w in fokus.lower() for w in ("conditioning", "hiit", "kondition"))
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
    return None


# ── Mobility-Session Übungen (hardcodiert — nicht über Claude) ────────────────

def _mobility_haupt_uebungen() -> list[HauptUebung]:
    return [
        HauptUebung(
            reihenfolge=1, exercise_id="mobility_hip_90_90",
            name="Hip 90/90 Stretch",
            saetze=3, wdh="45sec", rpe=3, tempo="halten", pausenzeit_sek=30,
            coaching_cues=["Becken aufrecht halten", "Beide Gesäßhälften gleichmäßig belasten"],
            notiz="",
        ),
        HauptUebung(
            reihenfolge=2, exercise_id="mobility_thoracic_rotation",
            name="Thorakale Rotation (Knie an Wand)",
            saetze=2, wdh="8 je Seite", rpe=3, tempo="langsam", pausenzeit_sek=30,
            coaching_cues=["Lendenwirbelsäule bleibt stabil", "Rotation kommt aus der BWS"],
            notiz="",
        ),
        HauptUebung(
            reihenfolge=3, exercise_id="mobility_worlds_greatest_stretch",
            name="World's Greatest Stretch",
            saetze=2, wdh="6 je Seite", rpe=3, tempo="langsam", pausenzeit_sek=30,
            coaching_cues=["Tief in die Dehnung sinken", "Auf gleichmäßige Atmung achten"],
            notiz="",
        ),
        HauptUebung(
            reihenfolge=4, exercise_id="mobility_deep_squat_hold",
            name="Tiefe Kniebeugen-Halteposition",
            saetze=3, wdh="30sec", rpe=3, tempo="halten", pausenzeit_sek=30,
            coaching_cues=["Fersen bleiben am Boden", "Brust aufrecht und offen"],
            notiz="",
        ),
        HauptUebung(
            reihenfolge=5, exercise_id="mobility_shoulder_cars",
            name="Schulter CARs (Controlled Articular Rotations)",
            saetze=2, wdh="5 je Seite", rpe=2, tempo="sehr langsam", pausenzeit_sek=30,
            coaching_cues=["Maximalen Bewegungsumfang ausschöpfen", "Restlicher Körper bleibt statisch"],
            notiz="",
        ),
        HauptUebung(
            reihenfolge=6, exercise_id="mobility_cat_cow",
            name="Cat-Cow — Wirbelsäulenmobilisation",
            saetze=2, wdh="10", rpe=2, tempo="atemgesteuert", pausenzeit_sek=30,
            coaching_cues=["Mit Atemrhythmus synchronisieren", "Jeden einzelnen Wirbel bewegen"],
            notiz="",
        ),
    ]


# ── PST Re-Test ───────────────────────────────────────────────────────────────

_PST_TESTS = [
    PSTTest(test="kniebeugen", einheit="wiederholungen"),
    PSTTest(test="pushups",    einheit="wiederholungen"),
    PSTTest(test="situps",     einheit="wiederholungen"),
    PSTTest(test="burpees",    einheit="wiederholungen"),
    PSTTest(test="plank",      einheit="sekunden"),
]


# ── Session-Dauer schätzen ─────────────────────────────────────────────────────

def _schaetze_dauer(n_uebungen: int, saetze: int, warm_up_min: int, cool_down_min: int, cardio_min: int) -> int:
    haupt_min = n_uebungen * saetze * 2
    total = warm_up_min + haupt_min + cool_down_min + cardio_min
    return min(120, max(20, round(total / 5) * 5))


# ── Hauptfunktion ─────────────────────────────────────────────────────────────

def assemble_plan(
    klient: KlientenInput,
    level: int,
    split: dict,           # {"split_typ": str, "sessions": list[dict]}
    claude_output: ClaudeOutput,
    block_nummer: int = 1,
) -> Plan:
    exercises_data = json.loads(_EXERCISES_PATH.read_text())
    ex_by_id = {e["id"]: e for e in exercises_data["exercises"]}

    claude_sessions = {s.session_id: s.uebungen for s in claude_output.sessions}

    tage = _TAGE_VERTEILUNG.get(klient.tage_pro_woche, list(_TAGE_VERTEILUNG[4]))
    wochen: list[Woche] = []

    for woche_idx, woche_typ in enumerate(_WOCHEN_TYPEN, start=1):
        volumen = berechne_volumen(klient, level, woche_typ)
        saetze = volumen["ziel_saetze"]
        rpe    = volumen["ziel_rpe"]
        stufe  = volumen["volumen_stufe"]

        sessions: list[Session] = []
        ist_peak = woche_typ == "peak"

        # Letzter Kraft-Session-Index für PST Re-Test (nicht Mobility/Metabolic)
        pst_session_idx = max(
            (i for i, s in enumerate(split["sessions"]) if s.get("session_typ") == "kraft"),
            default=len(split["sessions"]) - 1,
        )

        for session_idx, session_template in enumerate(split["sessions"]):
            original_id  = session_template["session_id"]
            session_id   = f"w{woche_idx}_s{session_idx + 1}"
            fokus        = session_template["fokus"]
            session_typ  = session_template.get("session_typ", "kraft")
            tag          = tage[session_idx] if session_idx < len(tage) else "samstag"

            if session_typ == "mobility":
                haupt_uebungen = _mobility_haupt_uebungen()
                warm_up        = _mobility_warm_up()
                cardio         = None
                cool_down      = _mobility_cool_down()
                fmt_notiz      = None
                pst_tests      = None
                dauer = _schaetze_dauer(
                    n_uebungen=len(haupt_uebungen),
                    saetze=1,
                    warm_up_min=warm_up.dauer_min,
                    cool_down_min=cool_down.dauer_min,
                    cardio_min=0,
                )
            else:
                is_metabolic = session_typ in ("zirkel", "amrap", "emom", "intervalle")
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
                            saetze=3 if is_metabolic else saetze,
                            wdh=_wdh(klient.hauptziel, pattern, u.reihenfolge, session_typ),
                            rpe=max(4, rpe - 1) if is_metabolic else rpe,
                            tempo=_tempo(pattern),
                            pausenzeit_sek=_pausenzeit(u.reihenfolge, pattern, session_typ),
                            coaching_cues=ex["coaching_cues"][:3],
                            notiz=u.notiz,
                        )
                    )

                warm_up   = _warm_up(klient.equipment, fokus)
                cardio    = _cardio(klient.hauptziel, fokus)
                cool_down = _cool_down(fokus)
                fmt_notiz = _format_notiz(session_typ, len(haupt_uebungen), 3 if is_metabolic else saetze)

                # PST Re-Test in letzter Kraft-Session der Peak-Woche
                pst_tests = None
                if ist_peak and session_idx == pst_session_idx:
                    pst_tests = _PST_TESTS

                cardio_min = cardio.dauer_min if cardio else 0
                dauer = _schaetze_dauer(
                    n_uebungen=len(haupt_uebungen),
                    saetze=3 if is_metabolic else saetze,
                    warm_up_min=warm_up.dauer_min,
                    cool_down_min=cool_down.dauer_min,
                    cardio_min=cardio_min,
                )

            sessions.append(
                Session(
                    session_id=session_id,
                    tag=tag,
                    session_typ=session_typ,
                    fokus=fokus,
                    format_notiz=fmt_notiz,
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
