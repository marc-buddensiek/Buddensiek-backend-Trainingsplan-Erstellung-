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
    berechne_volumen, ZEIT_PRO_SATZ_KRAFT,
    FINISHER_MIN_RECOMP, tier_floor,
)
from logic.conditioning_formats import (
    is_conditioning, is_block_format, conditioning_target_min, block_count,
    block_params, REST_BETWEEN_BLOCKS_SEK, conditioning_pool, split_conditioning_segments,
)
from logic.athletik import athletik_pool, athletik_dosierung
from logic.equipment_filter import verletzungs_rpe_cap
from logic.fokus_labels import anzeige_fokus, label_fuer_session_typ


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

_CORE_WDH = {1: "20", 2: "30", 3: "45", 4: "60"}   # Sekunden (bare; Einheit getrennt, Blocker 2a)


def _wdh(hauptziel: Hauptziel, pattern: str, tier: str, level: int, unit: str = "reps") -> tuple[str, str]:
    """(wert, einheit) — Einheit (unit) bestimmt beides: distanz→Meter, zeit→Sekunden, sonst Reps-Bereich."""
    if unit == "distanz" or pattern == "carry":
        return ("20", "meter")
    if unit == "zeit" or tier == "core" or pattern == "core":
        return (_CORE_WDH.get(level, "30"), "sekunden")
    return (_WDH_MAP.get(hauptziel, {}).get(tier, "8-12"), "wiederholungen")


# ── Tempo je Pattern + Session-Typ ────────────────────────────────────────────

def _tempo(pattern: str, session_typ: str = "kraft", unit: str = "reps") -> str:
    if session_typ in ("amrap", "zirkel"):
        return "zügig"
    if session_typ == "intervalle":
        return "explosiv"
    if unit == "zeit":          # Zeit-Holds (auch pattern≠core, z.B. wall_sit) → halten
        return "halten"
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
    # Conditioning trägt KEINE RPE (Spec Thema 6). "wert" bare; Einheit via _METABOLIC_EINHEIT (Blocker 2a).
    "amrap": {   # dauer_min entfernt (war Festwert in der Notiz; echte Dauer kommt jetzt als Param)
        "akkumulation":   {"saetze": 1, "wert": "10", "pause": 0},
        "progression":    {"saetze": 1, "wert": "10", "pause": 0},
        "intensivierung": {"saetze": 1, "wert": "10", "pause": 0},
        "deload":         {"saetze": 1, "wert": "10", "pause": 0},
    },
    "zirkel": {
        "akkumulation":   {"saetze": 3, "wert": "12", "pause": 0},
        "progression":    {"saetze": 3, "wert": "12", "pause": 0},
        "intensivierung": {"saetze": 4, "wert": "12", "pause": 0},
        "deload":         {"saetze": 2, "wert": "12", "pause": 0},
    },
    "intervalle": {
        "akkumulation":   {"saetze": 4, "wert": "30", "pause": 20},
        "progression":    {"saetze": 5, "wert": "35", "pause": 20},
        "intensivierung": {"saetze": 6, "wert": "40", "pause": 20},
        "deload":         {"saetze": 3, "wert": "30", "pause": 30},
    },
}

# Format-Einheit je session_typ: amrap/zirkel zählen Reps, intervalle Zeit (cfg["wert"] ist dort Sekunden).
_METABOLIC_EINHEIT = {"amrap": "wiederholungen", "zirkel": "wiederholungen", "intervalle": "sekunden"}

# Cardio-Wert für rep-zählende Formate (amrap/zirkel): Maschinen (unit=zeit) zeigen Zeit statt Reps.
# kalorien vertagt (kein Datum). Bare Sekunden (Einheit getrennt).
_CARDIO_WERT_ZEIT = {"amrap": "40", "zirkel": "40"}


def _metabolic_wdh(session_typ: str, pattern: str, woche_typ: str, unit: str = "reps") -> tuple[str, str]:
    """(wert, einheit) — Conditioning-Dosierung. core/zeit→Sekunden, distanz→Meter, sonst Format-Einheit."""
    cfg = _METABOLIC_CONFIG.get(session_typ, {}).get(woche_typ, {})
    if pattern == "core":
        return ("45", "sekunden")
    if unit == "zeit":
        return (_CARDIO_WERT_ZEIT.get(session_typ, cfg.get("wert", "40")), "sekunden")
    if unit == "distanz":
        return ("15", "meter")
    return (cfg.get("wert", "10"), _METABOLIC_EINHEIT.get(session_typ, "wiederholungen"))


# ── Format-Notiz je Session-Typ × Woche ───────────────────────────────────────

def _format_notiz(session_typ: str, n_uebungen: int, woche_typ: str, level: int, dauer_min: int | None = None) -> str | None:
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
        # Header modell-agnostisch (Befund E): KEINE konkrete Work:Rest-Zahl mehr — die per-Übung-Zeilen
        # tragen die echten (gerampten) Arbeit/Pause-Werte. Vermeidet den Widerspruch level-fest (45/15)
        # vs wochen-rampt (30→40). Timing-Modell-Entscheid: s. TODO(conditioning-timing-model).
        return (f"Intervalle: {r} Runden je Übung — Arbeit/Pause pro Übung angegeben. "
                f"2 Min. Pause zwischen Übungen. Ziel: 85-90% HF-Max.")
    return None


# ── Warm-Up je Equipment ──────────────────────────────────────────────────────

def _warmup_dauer(session_dauer_min: int) -> int:
    """Warm-up-Dauer proportional zur Session (≈ Session/6, gedeckelt 5–10): 20→5 · 30→5 ·
    45→8 · 60→10. Gemeinsame Quelle für _warm_up (gerendert) UND _schaetze_dauer (intern)."""
    return max(5, min(10, round(session_dauer_min / 6)))


def _warm_up(equipment: Equipment, fokus: str, session_dauer_min: int) -> WarmUp:
    wu = _warmup_dauer(session_dauer_min)   # proportional, ersetzt die früheren Protokoll-Fixwerte
    if equipment == Equipment.kettlebell:
        return WarmUp(
            protokoll="kettlebell",
            dauer_min=wu,
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
            dauer_min=wu,
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
            dauer_min=wu,
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
                dauer_min=wu,
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
                dauer_min=wu,
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
    # hauptziel aktuell ungenutzt – Cardio nur noch Zone-2/Longevity (Spec Thema 4: Cardio
    # ausschließlich Longevity-Pfad; fettabbau/recomp bekommen KEIN angehängtes Cardio).
    if "zone" in fokus.lower():
        return Cardio(
            typ="liss",
            dauer_min=30,
            beschreibung="Zone 2 — Tempo halten bei dem du dich noch unterhalten könntest (ca. 120-135 bpm)",
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


# Naht 4e-2: kurz-kompatible Finisher-Formate (F3a) — Tabata/Density vertagt (Block-Count im
# Finisher; sprengt das ~8-Min-Budget). Format rotiert über Wochen × Mischtag (nie 2× hintereinander).
_FINISHER_FORMATS = ["amrap", "zirkel"]


def _build_metcon_block(
    metcon_typ: str,
    woche_typ: str,
    uebungen_gefiltert: dict,
    level: int,
    offset: int = 0,
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
    # Naht 4e-2: `offset` rotiert die Finisher-Übungen (immer anderer AMRAP/Zirkel, auch bei
    # wiederkehrendem Format) — gleicher Mechanismus wie die C-Tage.
    pool = sorted(conditioning_pool(uebungen_gefiltert),
                  key=lambda e: 0 if "bodyweight" in e["equipment"] else 1)
    selected: list[HauptUebung] = []
    for i, ex in enumerate(_pick_finisher_uebungen(pool, 3, offset)):
        _wert, _einheit = _metabolic_wdh(metcon_typ, ex["pattern"], woche_typ, ex.get("unit", "reps"))
        selected.append(HauptUebung(
            reihenfolge=i + 1,
            exercise_id=ex["id"],
            name=ex["name"],
            saetze=cfg.get("saetze", 1),
            saetze_typ="runden",
            wert=_wert,
            einheit=_einheit,
            rir=None,   # Conditioning-Finisher trägt kein RIR (Spec Thema 6)
            tempo=_tempo(ex["pattern"], metcon_typ),
            pausenzeit_sek=cfg.get("pause", 0),
            coaching_cues=ex["coaching_cues"][:2],
            notiz="",
        ))

    if not selected:
        return None

    return MetconBlock(
        typ=metcon_typ,
        format_notiz=_format_notiz(metcon_typ, len(selected), woche_typ, level, dauer_min=FINISHER_MIN_RECOMP) or "",
        uebungen=selected,
    )


_CONDITIONING_SLOTS_N = 4   # session-füllende C-Segmente: feste Übungszahl (Zirkel/AMRAP üblich 3–5)
_ATHLETIK_N = 5             # Naht 5-2: Übungen je Athletik-Tag (4–5), durch Pool-Größe gedeckelt


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
                saetze=bp["saetze"], saetze_typ="runden", wert=bp["wdh"], einheit="format", rir=None,
                tempo=_tempo(ex["pattern"], fmt), pausenzeit_sek=REST_BETWEEN_BLOCKS_SEK,
                coaching_cues=ex["coaching_cues"][:3], notiz="",
            ))
    else:
        m_cfg = _METABOLIC_CONFIG.get(fmt, {}).get(woche_typ, {})
        for i, ex in enumerate(picks):
            _wert, _einheit = _metabolic_wdh(fmt, ex["pattern"], woche_typ, ex.get("unit", "reps"))
            out.append(HauptUebung(
                reihenfolge=i + 1, exercise_id=ex["id"], name=ex["name"],
                saetze=m_cfg.get("saetze", 3), saetze_typ="runden", wert=_wert, einheit=_einheit,
                rir=None, tempo=_tempo(ex["pattern"], fmt), pausenzeit_sek=m_cfg.get("pause", 0),
                coaching_cues=ex["coaching_cues"][:3], notiz="",
            ))
    return out


# ── Session-Dauer schätzen (flaches Modell, Spec Thema 3 Zeit-Parameter) ────────
# Konstanten/Helper aus volume_calculator (Single Source of Truth: Modell-A-Zeitparameter).
# Cooldown ist in die Warmup-Pauschale gefaltet; Cardio additiv (Block bleibt sichtbar).

def _schaetze_dauer(haupt_uebungen: list, zeit_pro_satz: float, session_dauer_min: int,
                    finisher_min_val: int = 0, cardio_min: int = 0) -> int:
    # finisher_min_val = interne Finisher-Minuten gemischter Tage (C3) — fließt NUR in die
    # Dauer-Rechnung; der Finisher hat KEINE eigene Tagesdauer (MetconBlock ohne dauer-Feld).
    sets_total = sum(u.saetze for u in haupt_uebungen)
    total = _warmup_dauer(session_dauer_min) + sets_total * zeit_pro_satz + finisher_min_val + cardio_min
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

    # Trim-Puffer (Befund 3): erst kürzen bei > Budget + 5 min — schützt die Muskelaufbau-W3-Rampe.
    while _schaetze_dauer(uebungen, zeit_pro_satz, wunschdauer, finisher_min_val, cardio_min) > wunschdauer + 5:
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
            is_ath_pool = any(s.get("pool") == "athletik" for s in slot_templates)
            # Naht 5-3: 1-Tage-Longevity-Cardio (rotate_cardio) alterniert Z2/Athletik über die Wochen —
            # woche_idx-Parität, W1=Zone-2 → gerade Wochen (W2/W4) = Athletik (W4 = Athletik im Deload).
            ist_athletik_woche = bool(session_template.get("rotate_cardio")) and woche_idx % 2 == 0
            build_athletik = is_ath_pool or ist_athletik_woche
            cond_block_2 = None                   # Naht 4d: zweites Format-Segment langer C-Tage
            session_typ_eff = session_typ         # kann sich bei langer Session ändern (Kapazitäts-Erstformat)
            dauer0 = 0
            ath_fallback_zone2 = False            # Naht 5-2: leerer Athletik-Pool → Zone-2-Cardio-Tag (DQ6)

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
                        format_notiz=_format_notiz(fmt1, len(seg2), woche_typ, level, dauer_min=dauer1) or fmt1,
                        uebungen=seg2,
                    )
            elif build_athletik:
                # Naht 5-2/5-3: Longevity-Athletik — deterministisch aus dem Athletik-Pool (A1), skill-
                # gestaffelte Dosierung (DQ2), KEINE RPE (DQ3), KEIN Cardio (DQ4), 4e-Übungs-Rotation,
                # Deload-Volumen runter (DQ5). Leerer Pool (z.B. L1-Bodyweight) → Zone-2-Fallback (DQ6).
                pool_ath = athletik_pool(uebungen_gefiltert)
                if not pool_ath:
                    session_typ_eff = "zone2"
                    ath_fallback_zone2 = True
                else:
                    session_typ_eff = "athletik"   # 5-3: Rotations-Tag zeigt in Athletik-Wochen den Athletik-Typ
                    rot = woche_idx * 3 + session_idx
                    for i, ex in enumerate(_pick_finisher_uebungen(pool_ath, _ATHLETIK_N, rot)):
                        a_saetze, a_wdh, a_pause = athletik_dosierung(ex["skill_level"], deload=ist_deload)
                        haupt_uebungen.append(HauptUebung(
                            reihenfolge=i + 1, exercise_id=ex["id"], name=ex["name"],
                            saetze=a_saetze, saetze_typ="saetze", wert=str(a_wdh), einheit="wiederholungen",
                            rir=None, tempo="explosiv",
                            pausenzeit_sek=a_pause, coaching_cues=ex["coaching_cues"][:3], notiz="",
                        ))
                    slot_tiers = ["compound"] * len(haupt_uebungen)
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
                                saetze_typ="runden",
                                wert=bp["wdh"],
                                einheit="format",
                                rir=None,
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
                        u_unit  = ex.get("unit", "reps")   # Bewegungs-Einheit (Naht 1)
                        slot_idx = u.reihenfolge - 1
                        slot_tier = (
                            slot_templates[slot_idx]["tier"]
                            if slot_idx < len(slot_templates)
                            else "compound"
                        )

                        if is_metabolic:
                            u_saetze     = m_cfg.get("saetze", 3)
                            u_wert, u_einheit = _metabolic_wdh(session_typ, pattern, woche_typ, u_unit)
                            u_saetze_typ = "runden"
                            u_rpe        = None   # Conditioning trägt keine RPE (Spec Thema 6)
                            u_pausenzeit = m_cfg.get("pause", 0)
                        else:
                            u_saetze     = volumen.get(f"{slot_tier}_saetze", saetze)
                            u_wert, u_einheit = _wdh(klient.hauptziel, pattern, slot_tier, level, u_unit)
                            u_saetze_typ = "saetze"
                            u_rpe        = volumen.get(f"{slot_tier}_rpe", rpe)
                            u_pausenzeit = _pausenzeit(slot_tier, pattern)

                        # RPE→RIR-Transform am Ausgang (intern bleibt RPE): RIR = 10 − RPE (0.5-Raster).
                        # RIR gilt NUR bei unit=="reps" — Zeit-Holds/Carry/Cardio (zeit/distanz/kalorien)
                        # tragen kein RIR (eine Regel statt der alten tempo=="halten"-/Carry-Marker, Naht 1).
                        u_tempo = _tempo(pattern, session_typ, u_unit)
                        # Verletzungs-Intensitäts-Deckel (PRIO 2): sichere Übung wird nicht near-failure
                        # geladen (z.B. Wirbelsäule × hinge/squat → RPE ≤ 7 / RIR ≥ 3). Single Source:
                        # derselbe Helper deckelt die Regel-4-Soll-Erwartung im plan_checker.
                        u_rpe   = verletzungs_rpe_cap(klient.verletzungen, pattern, u_rpe)
                        u_rir   = round((10 - u_rpe) * 2) / 2 if (u_rpe is not None and u_unit == "reps") else None

                        haupt_uebungen.append(
                            HauptUebung(
                                reihenfolge=u.reihenfolge,
                                exercise_id=u.exercise_id,
                                name=ex["name"],
                                saetze=u_saetze,
                                saetze_typ=u_saetze_typ,
                                wert=u_wert,
                                einheit=u_einheit,
                                rir=u_rir,
                                tempo=u_tempo,
                                pausenzeit_sek=u_pausenzeit,
                                coaching_cues=ex["coaching_cues"][:3],
                                notiz=u.notiz,
                            )
                        )
                        slot_tiers.append(slot_tier)

            warm_up    = _warm_up(klient.equipment, fokus, klient.session_dauer_min)
            is_athletik = build_athletik and not ath_fallback_zone2
            # Naht 5-2/5-3: echter Athletik-Tag trägt KEIN Cardio (DQ4); im Leer-Pool-Fallback wird der
            # Tag zum Zone-2-Cardio-Tag (DQ6); sonst Cardio je Fokus/Ziel (unverändert).
            if is_athletik:
                cardio = None
            elif ath_fallback_zone2:
                cardio = _cardio(klient.hauptziel, "Zone 2")
            else:
                cardio = _cardio(klient.hauptziel, fokus)
            cool_down  = _cool_down(fokus)
            # Reine C-Tage: Notiz für das (ggf. kapazitäts-überschriebene) Erstformat-Segment mit dessen
            # echter Segment-Dauer (4d); das 2. Segment trägt seine eigene Notiz im cond_block_2.
            fmt_notiz  = _format_notiz(session_typ_eff, len(haupt_uebungen), woche_typ, level,
                                       dauer_min=dauer0 if is_pool else None)
            # Naht 4e-2 (F3a/F4): der Template-`metcon_typ` ist nur das „hat Finisher"-Signal; das echte
            # Finisher-Format rotiert hier über Wochen × Mischtag aus {amrap, zirkel} (nie 2× hintereinander,
            # weil (woche_idx+session_idx) je Schritt die Parität wechselt), und die Finisher-Übungen
            # rotieren mit demselben Offset wie die C-Tage (immer anderer AMRAP/Zirkel).
            if session_template.get("metcon_typ"):
                fin_rot = woche_idx * 3 + session_idx
                fin_typ = _FINISHER_FORMATS[fin_rot % len(_FINISHER_FORMATS)]
                metcon_blk = _build_metcon_block(fin_typ, woche_typ, uebungen_gefiltert, level, fin_rot)
            else:
                metcon_blk = None

            # PST Re-Test in letzter Kraft-Session der Deload-Woche
            pst_tests = None
            if ist_deload and session_idx == pst_session_idx:
                pst_tests = _PST_TESTS

            cardio_min = cardio.dauer_min if cardio else 0
            # C3: gemischte Tage (Kraft + Finisher) zählen die Finisher-Minuten in die interne
            # Dauer-Rechnung — egal welches Ziel (vorher nur Recomp via finisher_min). Reine
            # interne Rechnung: der Finisher hat keine eigene Tagesdauer (MetconBlock ohne dauer).
            finisher_dauer = FINISHER_MIN_RECOMP if metcon_blk else 0
            # Conditioning-/Athletik-Tage nehmen die Dauer aus session_dauer_min (unten); nur Kraft
            # wird auf die Dauer getrimmt → zeit_pro_satz ist immer der Kraft-Faktor.
            zeit_pro_satz = ZEIT_PRO_SATZ_KRAFT
            # Naht 5-2: Athletik-Tage NICHT trimmen — die skill-gestaffelte Quality-Dosierung (inkl.
            # Deload) ist bewusst fix (wie Conditioning), „Dauer gewinnt" gilt nur für Kraft.
            if not is_metabolic and not is_athletik and haupt_uebungen:   # Dauer gewinnt: Kraft trimmen
                _trim_auf_dauer(haupt_uebungen, slot_tiers, klient.session_dauer_min,
                                zeit_pro_satz, finisher_dauer, cardio_min)
            # Display kosmetisch (Befund 2): ALLE Tage zeigen die angefragte Session-Dauer.
            # Die interne Schätzung dient nur dem Trim (in _trim_auf_dauer), nicht der Anzeige.
            dauer = min(120, max(20, klient.session_dauer_min))

            # Label-Sync: hat der Assembler den Typ NACH der Split-fokus-Vergabe geändert
            # (Conditioning-Erstformat-Tausch · Athletik→zone2-Fallback)? → fokus aus dem finalen
            # session_typ_eff neu ableiten. `fokus` oben (warm_up/cool_down/cardio-Routing) bleibt
            # unangetastet — nur das emittierte Label wird konsistent. Carry-Strip (split) NICHT berührt.
            fokus_emit = label_fuer_session_typ(session_typ_eff) if session_typ_eff != session_typ else fokus

            sessions.append(
                Session(
                    session_id=session_id,
                    tag=tag,
                    session_typ=session_typ_eff,
                    fokus=fokus_emit,
                    fokus_anzeige=anzeige_fokus(fokus_emit),
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
                ziel_rir=round((10 - rpe) * 2) / 2,
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
    )

    return Plan(
        plan_id=str(uuid.uuid4()),
        client_id=klient.client_id,
        erstellt_am=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        block_nummer=block_nummer,
        klient_snapshot=snapshot,
        wochen=wochen,
    )
