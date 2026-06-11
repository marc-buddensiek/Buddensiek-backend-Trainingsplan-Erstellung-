"""
ClaudeOutput + berechnete Parameter → vollständiger Plan (4 Wochen)

Claude wählt die Übungen für Block 1 einmal aus.
Dieselben Übungen laufen durch alle 4 Wochen — nur Sätze/RPE ändern sich.
Python ergänzt: name, coaching_cues, wdh, tempo, pausenzeit, warm_up, cardio, cool_down.
"""

from __future__ import annotations
import json
import pathlib
import uuid
from datetime import datetime, timezone

from models import (
    KlientenInput, ClaudeOutput, Hauptziel, Equipment,
    Plan, Woche, Session, KlientenSnapshot, MetconBlock,
    WarmUp, WarmUpUebung, HauptUebung, Cardio, CoolDown, CoolDownUebung, PSTTest,
)
from logic.volume_calculator import (
    berechne_volumen, WARMUP_MIN, ZEIT_PRO_SATZ_KRAFT, ZEIT_PRO_SATZ_COND, finisher_min, tier_floor,
)


_EXERCISES_PATH = pathlib.Path(__file__).parent.parent / "data" / "exercises.json"

_WOCHEN_TYPEN = ["akkumulation", "progression", "intensivierung", "deload"]

_TAGE_VERTEILUNG = {
    2: ["montag", "donnerstag"],
    3: ["montag", "mittwoch", "freitag"],
    4: ["montag", "dienstag", "donnerstag", "freitag"],
    5: ["montag", "dienstag", "mittwoch", "freitag", "samstag"],
    6: ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag"],
}


# ── Wdh-Strings je Ziel + Tier ────────────────────────────────────────────────

_WDH_MAP: dict[Hauptziel, dict[str, str]] = {
    Hauptziel.muskelaufbau: {"compound": "6-10",  "accessory": "8-12",  "isolation": "12-20"},
    Hauptziel.recomp:       {"compound": "6-10",  "accessory": "10-15", "isolation": "12-20"},
    Hauptziel.fettabbau:    {"compound": "8-12",  "accessory": "12-15", "isolation": "15-20"},
    # TODO(longevity-volume): Platzhalter = alte gesundheit-Werte, final mit MVP-3 / Thema 4-6
    Hauptziel.longevity:    {"compound": "8-12",  "accessory": "10-15", "isolation": "12-20"},
}

_CORE_WDH = {1: "20sec", 2: "30sec", 3: "45sec", 4: "60sec"}


def _wdh(hauptziel: Hauptziel, pattern: str, tier: str, level: int) -> str:
    if pattern == "carry":
        return "20m"
    if tier == "core" or pattern == "core":
        return _CORE_WDH.get(level, "30sec")
    return _WDH_MAP.get(hauptziel, {}).get(tier, "8-12")


# ── Tempo je Pattern + Session-Typ ────────────────────────────────────────────

def _tempo(pattern: str, session_typ: str = "kraft") -> str:
    if session_typ in ("amrap", "zirkel"):
        return "zügig"
    if session_typ == "emom":
        return "kontrolliert"
    if session_typ == "intervalle":
        return "explosiv"
    if pattern in ("squat", "hinge", "push_horizontal", "push_vertical"):
        return "3-1-1-0"
    if pattern in ("pull_horizontal", "pull_vertical"):
        return "2-0-1-1"
    if pattern == "single_leg":
        return "2-1-1-0"
    if pattern == "core":
        return "halten"
    if pattern == "carry":
        return "gleichmäßig"
    return "2-1-1-0"


# ── Pausenzeit je Tier (nur Kraft) ────────────────────────────────────────────

_TIER_PAUSENZEIT = {"compound": 180, "accessory": 90, "isolation": 60, "core": 45}


def _pausenzeit(tier: str, pattern: str) -> int:
    if pattern == "carry":
        return 90
    return _TIER_PAUSENZEIT.get(tier, 60)


# ── Metabolic-Config: Sätze + WDH + RPE + Pause je Session-Typ × Woche ───────

_METABOLIC_CONFIG: dict[str, dict[str, dict]] = {
    "amrap": {
        "akkumulation":   {"saetze": 1, "dauer_min": 10, "wdh": "10 Wdh", "rpe": 7, "pause": 0},
        "progression":    {"saetze": 1, "dauer_min": 12, "wdh": "10 Wdh", "rpe": 7, "pause": 0},
        "intensivierung": {"saetze": 1, "dauer_min": 15, "wdh": "10 Wdh", "rpe": 8, "pause": 0},
        "deload":         {"saetze": 1, "dauer_min":  8, "wdh": "10 Wdh", "rpe": 6, "pause": 0},
    },
    "emom": {
        "akkumulation":   {"saetze": 1, "dauer_min": 15, "wdh": "8 Wdh",  "rpe": 6, "pause": 0},
        "progression":    {"saetze": 1, "dauer_min": 18, "wdh": "8 Wdh",  "rpe": 7, "pause": 0},
        "intensivierung": {"saetze": 1, "dauer_min": 20, "wdh": "8 Wdh",  "rpe": 7, "pause": 0},
        "deload":         {"saetze": 1, "dauer_min": 12, "wdh": "8 Wdh",  "rpe": 5, "pause": 0},
    },
    "zirkel": {
        "akkumulation":   {"saetze": 3, "wdh": "12 Wdh", "rpe": 7, "pause": 0},
        "progression":    {"saetze": 3, "wdh": "12 Wdh", "rpe": 8, "pause": 0},
        "intensivierung": {"saetze": 4, "wdh": "12 Wdh", "rpe": 8, "pause": 0},
        "deload":         {"saetze": 2, "wdh": "12 Wdh", "rpe": 6, "pause": 0},
    },
    "intervalle": {
        "akkumulation":   {"saetze": 4, "wdh": "30 Sek", "rpe": 8, "pause": 20},
        "progression":    {"saetze": 5, "wdh": "35 Sek", "rpe": 9, "pause": 20},
        "intensivierung": {"saetze": 6, "wdh": "40 Sek", "rpe": 9, "pause": 20},
        "deload":         {"saetze": 3, "wdh": "30 Sek", "rpe": 7, "pause": 30},
    },
}


def _metabolic_wdh(session_typ: str, pattern: str, woche_typ: str) -> str:
    cfg = _METABOLIC_CONFIG.get(session_typ, {}).get(woche_typ, {})
    if pattern == "core":
        return "45 Sek" if session_typ != "emom" else "30 Sek / Min"
    return cfg.get("wdh", "10 Wdh")


# ── Format-Notiz je Session-Typ × Woche ───────────────────────────────────────

def _format_notiz(session_typ: str, n_uebungen: int, woche_typ: str) -> str | None:
    cfg = _METABOLIC_CONFIG.get(session_typ, {}).get(woche_typ, {})
    if session_typ == "zirkel":
        r = cfg.get("saetze", 3)
        return (f"{r} Runden Zirkel — alle {n_uebungen} Übungen nacheinander ohne Pause. "
                f"60 Sek. Pause nach jeder Runde. Runden notieren.")
    if session_typ == "amrap":
        d = cfg.get("dauer_min", 12)
        return (f"{d} Min. AMRAP — so viele Runden wie möglich mit allen {n_uebungen} Übungen. "
                f"Kein Stop zwischen Übungen. Runden am Ende notieren.")
    if session_typ == "emom":
        d = cfg.get("dauer_min", 20)
        return (f"{d} Min. EMOM — jede Minute eine Übung, Übungen rotieren. "
                f"Was in der Minute übrig ist = Pause. Technik vor Tempo.")
    if session_typ == "intervalle":
        r = cfg.get("saetze", 4)
        w = cfg.get("wdh", "30 Sek")
        return (f"Intervalle: {r} Runden je Übung — {w} Arbeit / 20 Sek. Pause. "
                f"2 Min. Pause zwischen Übungen. Ziel: 85-90% HF-Max.")
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
    if hauptziel in (Hauptziel.fettabbau, Hauptziel.recomp):
        return Cardio(
            typ="liss",
            dauer_min=15,
            beschreibung="10 Min ruhiges Gehen oder Bike als aktive Erholung nach der Session",
        )
    return None


# ── PST Re-Test ───────────────────────────────────────────────────────────────

_PST_TESTS = [
    PSTTest(test="kniebeugen", einheit="wiederholungen"),
    PSTTest(test="pushups",    einheit="wiederholungen"),
    PSTTest(test="situps",     einheit="wiederholungen"),
    PSTTest(test="burpees",    einheit="wiederholungen"),
    PSTTest(test="plank",      einheit="sekunden"),
]


# ── Metcon-Block Builder (Recomp-Finisher) ────────────────────────────────────

# Muster-Sequenz für Metcon-Übungen: abwechseln damit nicht dieselbe wie Kraftteil
_METCON_PATTERNS = ["squat", "hinge", "push_horizontal", "core"]


def _build_metcon_block(
    metcon_typ: str,
    woche_typ: str,
    uebungen_gefiltert: dict,
) -> MetconBlock | None:
    if not metcon_typ:
        return None
    cfg = _METABOLIC_CONFIG.get(metcon_typ, {}).get(woche_typ, {})
    selected: list[HauptUebung] = []

    for i, pattern in enumerate(_METCON_PATTERNS[:3]):
        candidates = uebungen_gefiltert.get(pattern, [])
        if not candidates:
            continue
        # Nimm zweite Übung wenn verfügbar (erste gehört meist zum Kraftteil)
        ex = candidates[min(1, len(candidates) - 1)]
        selected.append(HauptUebung(
            reihenfolge=i + 1,
            exercise_id=ex["id"],
            name=ex["name"],
            saetze=cfg.get("saetze", 1),
            wdh=_metabolic_wdh(metcon_typ, pattern, woche_typ),
            rpe=cfg.get("rpe", 7),
            tempo=_tempo(pattern, metcon_typ),
            pausenzeit_sek=cfg.get("pause", 0),
            coaching_cues=ex["coaching_cues"][:2],
            notiz="",
        ))

    if not selected:
        return None

    return MetconBlock(
        typ=metcon_typ,
        format_notiz=_format_notiz(metcon_typ, len(selected), woche_typ) or "",
        uebungen=selected,
    )


# ── Session-Dauer schätzen (flaches Modell, Spec Thema 3 Zeit-Parameter) ────────
# Konstanten/Helper aus volume_calculator (Single Source of Truth: Modell-A-Zeitparameter).
# Cooldown ist in die Warmup-Pauschale gefaltet; Cardio additiv (Block bleibt sichtbar).

def _schaetze_dauer(haupt_uebungen: list, zeit_pro_satz: float, ziel: Hauptziel, cardio_min: int = 0) -> int:
    sets_total = sum(u.saetze for u in haupt_uebungen)
    total = WARMUP_MIN + sets_total * zeit_pro_satz + finisher_min(ziel) + cardio_min
    return min(120, max(20, round(total / 5) * 5))


def _trim_auf_dauer(uebungen: list, tiers: list, wunschdauer: int,
                    zeit_pro_satz: float, ziel: Hauptziel, cardio_min: int) -> None:
    """Kürzt Sätze (nicht Übungen), bis die geschätzte Dauer in die Wunschdauer passt.
    Reihenfolge: core → isolation → accessory → Zweit-Compound → Haupt-Compound (zuletzt,
    nie unter Cap-Unterkante). Sind alle Slots auf ihrem Floor, bleibt die Session minimal
    über der Dauer — KEIN Pflicht-Pattern fällt weg (Spec Thema 3 Z. 286-290 / Z. 290)."""
    haupt_comp = next((i for i, t in enumerate(tiers) if t == "compound"), None)  # Schwerpunkt

    def _kandidat():
        for tier in ("core", "isolation", "accessory"):
            for i, t in enumerate(tiers):
                if t == tier and uebungen[i].saetze > tier_floor(tier):
                    return i
        for i, t in enumerate(tiers):                       # Zweit-Compounds vor Schwerpunkt
            if t == "compound" and i != haupt_comp and uebungen[i].saetze > tier_floor("compound"):
                return i
        if haupt_comp is not None and uebungen[haupt_comp].saetze > tier_floor("compound"):
            return haupt_comp                               # Haupt-Compound zuletzt
        return None

    while _schaetze_dauer(uebungen, zeit_pro_satz, ziel, cardio_min) > wunschdauer:
        i = _kandidat()
        if i is None:
            # TODO(short-session-pattern-drop): V1 entfernt kein Pflicht-Pattern. An der
            # Untergrenze (z.B. 20min, 30min-Recomp) bleibt die Session minimal über der Dauer.
            break
        uebungen[i].saetze -= 1


# ── Hauptfunktion ─────────────────────────────────────────────────────────────

def assemble_plan(
    klient: KlientenInput,
    level: int,
    split: dict,           # {"split_typ": str, "sessions": list[dict]}
    claude_output: ClaudeOutput,
    block_nummer: int = 1,
    uebungen_gefiltert: dict | None = None,
) -> Plan:
    exercises_data = json.loads(_EXERCISES_PATH.read_text())
    ex_by_id = {e["id"]: e for e in exercises_data["exercises"]}

    if uebungen_gefiltert is None:
        from logic.equipment_filter import filtere_uebungen
        uebungen_gefiltert = filtere_uebungen(klient, level)

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

        # Letzter Kraft-Session-Index für PST Re-Test (nicht Zone-2/Metabolic)
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
            metcon_blk   = None

            is_metabolic = session_typ in ("zirkel", "amrap", "emom", "intervalle")
            m_cfg = _METABOLIC_CONFIG.get(session_typ, {}).get(woche_typ, {}) if is_metabolic else {}

            uebungen_auswahl = claude_sessions.get(original_id, [])
            haupt_uebungen: list[HauptUebung] = []
            slot_tiers: list[str] = []            # Tier je HauptUebung (aligned) für den Trim

            slot_templates = session_template.get("slots", [])
            for u in uebungen_auswahl:
                ex = ex_by_id.get(u.exercise_id)
                if not ex:
                    continue
                pattern = ex["pattern"]
                slot_idx = u.reihenfolge - 1
                slot_tier = (
                    slot_templates[slot_idx]["tier"]
                    if slot_idx < len(slot_templates)
                    else "compound"
                )

                if is_metabolic:
                    u_saetze     = m_cfg.get("saetze", 3)
                    u_wdh        = _metabolic_wdh(session_typ, pattern, woche_typ)
                    u_rpe        = m_cfg.get("rpe", 7)
                    u_pausenzeit = m_cfg.get("pause", 0)
                else:
                    u_saetze     = volumen.get(f"{slot_tier}_saetze", saetze)
                    u_wdh        = _wdh(klient.hauptziel, pattern, slot_tier, level)
                    u_rpe        = volumen.get(f"{slot_tier}_rpe", rpe)
                    u_pausenzeit = _pausenzeit(slot_tier, pattern)

                haupt_uebungen.append(
                    HauptUebung(
                        reihenfolge=u.reihenfolge,
                        exercise_id=u.exercise_id,
                        name=ex["name"],
                        saetze=u_saetze,
                        wdh=u_wdh,
                        rpe=u_rpe,
                        tempo=_tempo(pattern, session_typ),
                        pausenzeit_sek=u_pausenzeit,
                        coaching_cues=ex["coaching_cues"][:3],
                        notiz=u.notiz,
                    )
                )
                slot_tiers.append(slot_tier)

            warm_up    = _warm_up(klient.equipment, fokus)
            cardio     = _cardio(klient.hauptziel, fokus)
            cool_down  = _cool_down(fokus)
            fmt_notiz  = _format_notiz(session_typ, len(haupt_uebungen), woche_typ)
            metcon_typ = session_template.get("metcon_typ")
            metcon_blk = _build_metcon_block(metcon_typ, woche_typ, uebungen_gefiltert) if metcon_typ else None

            # PST Re-Test in letzter Kraft-Session der Deload-Woche
            pst_tests = None
            if ist_deload and session_idx == pst_session_idx:
                pst_tests = _PST_TESTS

            cardio_min = cardio.dauer_min if cardio else 0
            zeit_pro_satz = ZEIT_PRO_SATZ_COND if is_metabolic else ZEIT_PRO_SATZ_KRAFT
            if not is_metabolic and haupt_uebungen:   # Dauer gewinnt: Kraft-Sätze auf Wunschdauer trimmen
                _trim_auf_dauer(haupt_uebungen, slot_tiers, klient.session_dauer_min,
                                zeit_pro_satz, klient.hauptziel, cardio_min)
            dauer = _schaetze_dauer(haupt_uebungen, zeit_pro_satz, klient.hauptziel, cardio_min)

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
                    metcon_block=metcon_blk,
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
        session_dauer_min=klient.session_dauer_min,
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
