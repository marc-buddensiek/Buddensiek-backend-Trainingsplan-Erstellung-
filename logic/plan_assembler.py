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
    KlientenInput, ClaudeOutput, Hauptziel, Equipment, UebungAuswahl,
    Plan, Woche, Session, KlientenSnapshot, MetconBlock,
    WarmUp, WarmUpUebung, HauptUebung, Cardio, CoolDown, CoolDownUebung, PSTTest,
)
from logic.volume_calculator import (
    berechne_volumen, WARMUP_MIN, ZEIT_PRO_SATZ_KRAFT, ZEIT_PRO_SATZ_COND,
    FINISHER_MIN_RECOMP, tier_floor, rir_hinweis,
)
from logic.conditioning_formats import (
    is_conditioning, is_block_format, conditioning_target_min, block_count,
    block_params, REST_BETWEEN_BLOCKS_SEK, conditioning_pool, split_conditioning_segments,
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


# ── Metabolic-Config: Sätze + WDH + Pause je Session-Typ × Woche (keine RPE, Thema 6) ───────

_METABOLIC_CONFIG: dict[str, dict[str, dict]] = {
    # Conditioning trägt KEINE RPE (Spec Thema 6) — kein rpe-Key mehr.
    "amrap": {   # dauer_min entfernt (war Festwert in der Notiz; echte Dauer kommt jetzt als Param)
        "akkumulation":   {"saetze": 1, "wdh": "10 Wdh", "pause": 0},
        "progression":    {"saetze": 1, "wdh": "10 Wdh", "pause": 0},
        "intensivierung": {"saetze": 1, "wdh": "10 Wdh", "pause": 0},
        "deload":         {"saetze": 1, "wdh": "10 Wdh", "pause": 0},
    },
    "zirkel": {
        "akkumulation":   {"saetze": 3, "wdh": "12 Wdh", "pause": 0},
        "progression":    {"saetze": 3, "wdh": "12 Wdh", "pause": 0},
        "intensivierung": {"saetze": 4, "wdh": "12 Wdh", "pause": 0},
        "deload":         {"saetze": 2, "wdh": "12 Wdh", "pause": 0},
    },
    "intervalle": {
        "akkumulation":   {"saetze": 4, "wdh": "30 Sek", "pause": 20},
        "progression":    {"saetze": 5, "wdh": "35 Sek", "pause": 20},
        "intensivierung": {"saetze": 6, "wdh": "40 Sek", "pause": 20},
        "deload":         {"saetze": 3, "wdh": "30 Sek", "pause": 30},
    },
}


def _metabolic_wdh(session_typ: str, pattern: str, woche_typ: str) -> str:
    cfg = _METABOLIC_CONFIG.get(session_typ, {}).get(woche_typ, {})
    if pattern == "core":
        return "45 Sek"
    return cfg.get("wdh", "10 Wdh")


# ── Format-Notiz je Session-Typ × Woche ───────────────────────────────────────

def _format_notiz(session_typ: str, n_uebungen: int, woche_typ: str, dauer_min: int | None = None) -> str | None:
    # dauer_min = echte/effektive Conditioning-Dauer (Finisher: ≤10 Min; reine Session: session_min−Warmup).
    cfg = _METABOLIC_CONFIG.get(session_typ, {}).get(woche_typ, {})
    if session_typ == "tabata":
        return (f"Tabata — {n_uebungen} Blöcke à 8 Runden 20 s Arbeit / 10 s Pause (4 Min/Block), "
                f"je Block eine andere Übung, 60 Sek. Pause zwischen den Blöcken.")
    if session_typ == "density":
        return (f"Density — {n_uebungen} Blöcke à 5 Min: max. Wiederholungen bei festem Gewicht, "
                f"60 Sek. Pause zwischen den Blöcken.")
    if session_typ == "ladders":
        return (f"Ladders — {n_uebungen} Blöcke à 5 Min: Wiederholungen aufsteigend (1-2-3-…), "
                f"je Block eine andere Übung, 60 Sek. Pause zwischen den Blöcken.")
    if session_typ == "zirkel":
        r = cfg.get("saetze", 3)
        return (f"{r} Runden Zirkel — alle {n_uebungen} Übungen nacheinander ohne Pause. "
                f"60 Sek. Pause nach jeder Runde. Runden notieren.")
    if session_typ == "amrap":
        d = dauer_min if dauer_min is not None else 10   # echte Dauer, kein _METABOLIC_CONFIG-Festwert mehr
        return (f"{d} Min. AMRAP — so viele Runden wie möglich mit allen {n_uebungen} Übungen. "
                f"Kein Stop zwischen Übungen. Runden am Ende notieren.")
    if session_typ == "intervalle":
        r = cfg.get("saetze", 4)
        w = cfg.get("wdh", "30 Sek")
        # TODO(mvp7-cleanup): Work:Rest hier hardcodiert ("20 Sek. Pause") statt aus
        # conditioning_formats.level_work_rest — Spec sagt Level-Work:Rest. Naht-4-Gebiet.
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
    ist_conditioning = any(w in fokus.lower() for w in ("kondition", "conditioning", "hiit", "zone", "amrap", "intervalle"))

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

def _pick_finisher_uebungen(pool: list[dict], n: int, offset: int = 0) -> list[dict]:
    """Bis zu n Conditioning-Übungen mit Pattern-Vielfalt (nicht 3× dasselbe Pattern).
    `offset` rotiert je Pattern, WELCHE Übung gewählt wird (Naht 4e: Übungs-Rotation über C-Tage/
    Wochen) — die Pattern-Reihenfolge (BW-first) bleibt erhalten, nur die konkrete Übung je Pattern
    variiert; `offset=0` reproduziert exakt das Verhalten vor 4e."""
    by_pattern: dict[str, list[dict]] = {}
    for ex in pool:
        by_pattern.setdefault(ex["pattern"], []).append(ex)
    picked: list[dict] = []
    used: set[str] = set()
    for pat in dict.fromkeys(ex["pattern"] for ex in pool):   # Pattern in Pool-Reihenfolge (BW-first)
        cands = by_pattern[pat]
        ex = cands[offset % len(cands)]                       # Übung je Pattern offset-rotiert
        picked.append(ex)
        used.add(ex["id"])
        if len(picked) == n:
            return picked
    rest = [ex for ex in pool if ex["id"] not in used]        # auffüllen, falls mehr Slots als Pattern
    for i in range(len(rest)):
        if len(picked) == n:
            break
        picked.append(rest[(offset + i) % len(rest)])
    return picked


def _build_metcon_block(
    metcon_typ: str,
    woche_typ: str,
    uebungen_gefiltert: dict,
) -> MetconBlock | None:
    if not metcon_typ:
        return None
    cfg = _METABOLIC_CONFIG.get(metcon_typ, {}).get(woche_typ, {})
    # Naht 4b: Finisher zieht aus dem Conditioning-Pool (pattern=="conditioning" ODER
    # conditioning_friendly) statt aus Kraft-Pattern. Equipment-korrekt, weil uebungen_gefiltert
    # schon equipment-gefiltert ist (Bodyweight als Obergrenze immer dabei). Pool ist global/
    # Ganzkörper — cf-Übungen sind keine Isolationsübungen.
    # Bodyweight bleibt der Hauptteil (stabil zuerst); equipment-spezifische Übungen (z.B. KB)
    # kommen nur als Zusatz dazu — und nur dort, wo es keine Bodyweight-Variante gibt (z.B. Hinge/Swing).
    pool = sorted(conditioning_pool(uebungen_gefiltert),
                  key=lambda e: 0 if "bodyweight" in e["equipment"] else 1)
    selected: list[HauptUebung] = []
    for i, ex in enumerate(_pick_finisher_uebungen(pool, 3)):
        selected.append(HauptUebung(
            reihenfolge=i + 1,
            exercise_id=ex["id"],
            name=ex["name"],
            saetze=cfg.get("saetze", 1),
            wdh=_metabolic_wdh(metcon_typ, ex["pattern"], woche_typ),
            rpe=None,   # Conditioning-Finisher trägt keine RPE (Spec Thema 6)
            tempo=_tempo(ex["pattern"], metcon_typ),
            pausenzeit_sek=cfg.get("pause", 0),
            coaching_cues=ex["coaching_cues"][:2],
            notiz="",
        ))

    if not selected:
        return None

    return MetconBlock(
        typ=metcon_typ,
        format_notiz=_format_notiz(metcon_typ, len(selected), woche_typ, dauer_min=FINISHER_MIN_RECOMP) or "",
        uebungen=selected,
    )


_CONDITIONING_SLOTS_N = 4   # session-füllende C-Segmente: feste Übungszahl (Zirkel/AMRAP üblich 3–5)


def _build_conditioning_segment(fmt: str, seg_dauer: int, pool_sorted: list[dict],
                                woche_typ: str, offset: int = 0) -> list[HauptUebung]:
    """HauptUebung-Liste für EIN Conditioning-Segment (Naht 4c/4d), deterministisch aus dem
    (BW-first sortierten, equipment-gefilterten) Conditioning-Pool. Block-Format → Block-Stapelung
    (n Blöcke je seg_dauer, je Block eine andere Übung, festes Timing, 60 s Pause, keine RPE);
    session-füllend → feste Slot-Anzahl mit _METABOLIC_CONFIG-Dosierung. `offset` rotiert die
    Übungs-Auswahl (Naht 4e: pro Woche × C-Tag); `offset=0` = Verhalten vor 4e."""
    is_blk = is_block_format(fmt)
    n = block_count(fmt, seg_dauer) if is_blk else _CONDITIONING_SLOTS_N
    picks = _pick_finisher_uebungen(pool_sorted, n, offset)
    if not picks:
        return []
    out: list[HauptUebung] = []
    if is_blk:
        bp = block_params(fmt)
        for i in range(n):
            ex = picks[i % len(picks)]
            out.append(HauptUebung(
                reihenfolge=i + 1, exercise_id=ex["id"], name=ex["name"],
                saetze=bp["saetze"], wdh=bp["wdh"], rpe=None,
                tempo=_tempo(ex["pattern"], fmt), pausenzeit_sek=REST_BETWEEN_BLOCKS_SEK,
                coaching_cues=ex["coaching_cues"][:3], notiz="",
            ))
    else:
        m_cfg = _METABOLIC_CONFIG.get(fmt, {}).get(woche_typ, {})
        for i, ex in enumerate(picks):
            out.append(HauptUebung(
                reihenfolge=i + 1, exercise_id=ex["id"], name=ex["name"],
                saetze=m_cfg.get("saetze", 3), wdh=_metabolic_wdh(fmt, ex["pattern"], woche_typ),
                rpe=None, tempo=_tempo(ex["pattern"], fmt), pausenzeit_sek=m_cfg.get("pause", 0),
                coaching_cues=ex["coaching_cues"][:3], notiz="",
            ))
    return out


# ── Session-Dauer schätzen (flaches Modell, Spec Thema 3 Zeit-Parameter) ────────
# Konstanten/Helper aus volume_calculator (Single Source of Truth: Modell-A-Zeitparameter).
# Cooldown ist in die Warmup-Pauschale gefaltet; Cardio additiv (Block bleibt sichtbar).

def _schaetze_dauer(haupt_uebungen: list, zeit_pro_satz: float, finisher_min_val: int = 0, cardio_min: int = 0) -> int:
    # finisher_min_val = interne Finisher-Minuten gemischter Tage (C3) — fließt NUR in die
    # Dauer-Rechnung; der Finisher hat KEINE eigene Tagesdauer (MetconBlock ohne dauer-Feld).
    sets_total = sum(u.saetze for u in haupt_uebungen)
    total = WARMUP_MIN + sets_total * zeit_pro_satz + finisher_min_val + cardio_min
    return min(120, max(20, round(total / 5) * 5))


def _trim_auf_dauer(uebungen: list, tiers: list, wunschdauer: int,
                    zeit_pro_satz: float, finisher_min_val: int, cardio_min: int) -> None:
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

    while _schaetze_dauer(uebungen, zeit_pro_satz, finisher_min_val, cardio_min) > wunschdauer:
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

            is_metabolic = is_conditioning(session_typ)
            is_block     = is_block_format(session_typ)
            m_cfg = _METABOLIC_CONFIG.get(session_typ, {}).get(woche_typ, {}) if (is_metabolic and not is_block) else {}

            haupt_uebungen: list[HauptUebung] = []
            slot_tiers: list[str] = []            # Tier je HauptUebung (aligned) für den Trim
            slot_templates = session_template.get("slots", [])
            is_pool = any(s.get("pool") == "conditioning" for s in slot_templates)
            cond_block_2 = None                   # Naht 4d: zweites Format-Segment langer C-Tage
            session_typ_eff = session_typ         # kann sich bei langer Session ändern (Kapazitäts-Erstformat)
            dauer0 = 0

            if is_pool:
                # Naht 4c/4d: reine C-Tage ziehen deterministisch aus dem Conditioning-Pool (BW-first,
                # equipment-gefiltert) und werden bei langen Sessions auf 2 Format-Segmente aufgeteilt
                # (split_conditioning_segments: Maxima + kapazitätsbewusstes Erstformat). Dauer ohne
                # Level-Deckelung. Single-Segment = identisch zu Naht 4c-2.
                pool_sorted = sorted(conditioning_pool(uebungen_gefiltert),
                                     key=lambda e: 0 if "bodyweight" in e["equipment"] else 1)
                cond_target = conditioning_target_min(klient.session_dauer_min)
                segments = split_conditioning_segments(cond_target, session_typ, level, klient.equipment.value)
                # Naht 4e: Übungs-Rotation pro Woche × C-Tag (räumlich session_idx, zeitlich woche_idx);
                # Segment 2 versetzt (+1), damit die 2 Segmente eines Tages nicht dieselben Übungen ziehen.
                rot = woche_idx * 3 + session_idx
                session_typ_eff, dauer0 = segments[0]
                haupt_uebungen = _build_conditioning_segment(session_typ_eff, dauer0, pool_sorted, woche_typ, rot)
                slot_tiers = ["compound"] * len(haupt_uebungen)
                if len(segments) == 2:
                    fmt1, dauer1 = segments[1]
                    seg2 = _build_conditioning_segment(fmt1, dauer1, pool_sorted, woche_typ, rot + 1)
                    cond_block_2 = MetconBlock(
                        typ=fmt1,
                        format_notiz=_format_notiz(fmt1, len(seg2), woche_typ, dauer_min=dauer1) or fmt1,
                        uebungen=seg2,
                    )
            else:
                uebungen_auswahl = claude_sessions.get(original_id, [])
                valid_auswahl = [u for u in uebungen_auswahl if ex_by_id.get(u.exercise_id)]
                cond_target = conditioning_target_min(klient.session_dauer_min) if is_block else 0
                if is_block and valid_auswahl:
                    # ── Block-Stapelung (Spec Thema 6): n Blöcke füllen die Ziel-Dauer, je Block
                    #    EINE Übung (zyklisch durch die gezogenen), festes Block-Timing (schlägt
                    #    Level-Work:Rest), 60 s Pause zwischen den Blöcken, keine RPE. ──
                    n  = block_count(session_typ, cond_target)
                    bp = block_params(session_typ)
                    for i in range(n):
                        u  = valid_auswahl[i % len(valid_auswahl)]
                        ex = ex_by_id[u.exercise_id]
                        haupt_uebungen.append(
                            HauptUebung(
                                reihenfolge=i + 1,
                                exercise_id=u.exercise_id,
                                name=ex["name"],
                                saetze=bp["saetze"],
                                wdh=bp["wdh"],
                                rpe=None,
                                tempo=_tempo(ex["pattern"], session_typ),
                                pausenzeit_sek=REST_BETWEEN_BLOCKS_SEK,
                                coaching_cues=ex["coaching_cues"][:3],
                                notiz=u.notiz,
                            )
                        )
                        slot_tiers.append("compound")
                else:
                    for u in valid_auswahl:
                        ex = ex_by_id[u.exercise_id]
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
                            u_rpe        = None   # Conditioning trägt keine RPE (Spec Thema 6)
                            u_pausenzeit = m_cfg.get("pause", 0)
                        else:
                            u_saetze     = volumen.get(f"{slot_tier}_saetze", saetze)
                            u_wdh        = _wdh(klient.hauptziel, pattern, slot_tier, level)
                            u_rpe        = volumen.get(f"{slot_tier}_rpe", rpe)
                            u_pausenzeit = _pausenzeit(slot_tier, pattern)

                        # L1-RIR-Hilfe: nur Kraftsätze (nicht-metabolic); rir_hinweis liefert für Level ≥ 2 None
                        u_rpe_hinweis = None if is_metabolic else rir_hinweis(level, u_rpe)

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
                                rpe_hinweis=u_rpe_hinweis,
                            )
                        )
                        slot_tiers.append(slot_tier)

            warm_up    = _warm_up(klient.equipment, fokus)
            cardio     = _cardio(klient.hauptziel, fokus)
            cool_down  = _cool_down(fokus)
            # Reine C-Tage: Notiz für das (ggf. kapazitäts-überschriebene) Erstformat-Segment mit dessen
            # echter Segment-Dauer (4d); das 2. Segment trägt seine eigene Notiz im cond_block_2.
            fmt_notiz  = _format_notiz(session_typ_eff, len(haupt_uebungen), woche_typ,
                                       dauer_min=dauer0 if is_pool else None)
            metcon_typ = session_template.get("metcon_typ")
            metcon_blk = _build_metcon_block(metcon_typ, woche_typ, uebungen_gefiltert) if metcon_typ else None

            # PST Re-Test in letzter Kraft-Session der Deload-Woche
            pst_tests = None
            if ist_deload and session_idx == pst_session_idx:
                pst_tests = _PST_TESTS

            cardio_min = cardio.dauer_min if cardio else 0
            # C3: gemischte Tage (Kraft + Finisher) zählen die Finisher-Minuten in die interne
            # Dauer-Rechnung — egal welches Ziel (vorher nur Recomp via finisher_min). Reine
            # interne Rechnung: der Finisher hat keine eigene Tagesdauer (MetconBlock ohne dauer).
            finisher_dauer = FINISHER_MIN_RECOMP if metcon_blk else 0
            # TODO(mvp7-cleanup): ZEIT_PRO_SATZ_COND ist für is_metabolic toter Pfad — reine
            # Conditioning-Tage nutzen die Dauer aus session_dauer_min (unten), nicht _schaetze_dauer.
            zeit_pro_satz = ZEIT_PRO_SATZ_COND if is_metabolic else ZEIT_PRO_SATZ_KRAFT
            if not is_metabolic and haupt_uebungen:   # Dauer gewinnt: Kraft-Sätze auf Wunschdauer trimmen
                _trim_auf_dauer(haupt_uebungen, slot_tiers, klient.session_dauer_min,
                                zeit_pro_satz, finisher_dauer, cardio_min)
            if is_metabolic:   # reine Conditioning-Tage füllen die gewählte Session-Dauer — KEINE
                dauer = min(120, max(20, klient.session_dauer_min))   # Level-Deckelung (Block stapelt dazu)
            else:
                dauer = _schaetze_dauer(haupt_uebungen, zeit_pro_satz, finisher_dauer, cardio_min)

            sessions.append(
                Session(
                    session_id=session_id,
                    tag=tag,
                    session_typ=session_typ_eff,
                    fokus=fokus,
                    format_notiz=fmt_notiz,
                    dauer_min_geschaetzt=dauer,
                    warm_up=warm_up,
                    haupt_uebungen=haupt_uebungen,
                    metcon_block=metcon_blk,
                    conditioning_block_2=cond_block_2,
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
