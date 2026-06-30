"""
Hauptziel × Tage × session_dauer_min → Split-Name + Sessions mit Slots

Slot-Anzahl nach Session-Dauer:
  20 min → 3 Slots: [compound, accessory, core]
  30 min → 4 Slots: [compound, compound, accessory, core]
  45 min → 5 Slots: [compound, compound, accessory, isolation, core]
  60 min → 6 Slots: [compound, compound, accessory, accessory, isolation, core]

"""

from __future__ import annotations
from models import KlientenInput, Hauptziel
from logic.conditioning_formats import pick_conditioning_formats
from logic.equipment_filter import filtere_uebungen


def _slot(beschreibung: str, pattern: str, tier: str = "compound", max_level: int = 4,
          pool: str | None = None) -> dict:
    s = {"beschreibung": beschreibung, "pattern": pattern, "tier": tier, "max_level": max_level}
    if pool:
        s["pool"] = pool   # z.B. "conditioning" → Assembler zieht aus dem Conditioning-Pool (Naht 4c)
    return s


def _tag_session(session_id: str, fokus: str, slots: list[dict], session_typ: str = "kraft", metcon_typ: str | None = None) -> dict:
    s = {"session_id": session_id, "fokus": fokus, "session_typ": session_typ, "slots": slots}
    if metcon_typ:
        s["metcon_typ"] = metcon_typ
    return s


# ── Dauer-basierte Slot-Templates ─────────────────────────────────────────────

def _upper_a_slots(dauer: int, level: int) -> list[dict]:
    if dauer <= 20:
        return [
            _slot("Haupt-Horizontaldruck",        "push_horizontal", "compound",  level),
            _slot("Horizontales Ziehen (Balance)", "pull_horizontal", "accessory", level),
            _slot("Core",                          "core",            "core",       level),
        ]
    elif dauer <= 30:
        return [
            _slot("Haupt-Horizontaldruck",     "push_horizontal", "compound",  level),
            _slot("Haupt-Vertikalzug",         "pull_vertical",   "compound",  level),
            _slot("Vertikales Drücken",        "push_vertical",   "accessory", level),
            _slot("Core",                      "core",            "core",       level),
        ]
    elif dauer <= 45:
        return [
            _slot("Haupt-Horizontaldruck",     "push_horizontal", "compound",       level),
            _slot("Haupt-Vertikalzug",         "pull_vertical",   "compound",       level),
            _slot("Vertikales Drücken",        "push_vertical",   "accessory",      level),
            _slot("Hintere Schulter Isolation","pull_horizontal",  "isolation", min(level, 2)),
            _slot("Core",                      "core",            "core",            level),
        ]
    else:  # 60
        return [
            _slot("Haupt-Horizontaldruck",     "push_horizontal", "compound",       level),
            _slot("Horizontales Ziehen",       "pull_horizontal", "compound",       level),
            _slot("Vertikales Drücken",        "push_vertical",   "accessory",      level),
            _slot("Vertikales Ziehen",         "pull_vertical",   "accessory",      level),
            _slot("Schulter / Arm Isolation",  "push_vertical",   "isolation", min(level, 2)),
            _slot("Core",                      "core",            "core",            level),
        ]


def _upper_b_slots(dauer: int, level: int) -> list[dict]:
    """Spiegelbildlich zu Upper A — Pull-Betonung für Push/Pull-Balance."""
    if dauer <= 20:
        return [
            _slot("Haupt-Vertikalzug",          "pull_vertical",   "compound",  level),
            _slot("Horizontales Drücken",        "push_horizontal", "accessory", level),
            _slot("Core",                        "core",            "core",       level),
        ]
    elif dauer <= 30:
        return [
            _slot("Haupt-Horizontales Ziehen",  "pull_horizontal", "compound",  level),
            _slot("Vertikales Drücken",         "push_vertical",   "compound",  level),
            _slot("Vertikales Ziehen",          "pull_vertical",   "accessory", level),
            _slot("Core",                       "core",            "core",       level),
        ]
    elif dauer <= 45:
        return [
            _slot("Haupt-Vertikalzug",          "pull_vertical",   "compound",       level),
            _slot("Haupt-Horizontales Ziehen",  "pull_horizontal", "compound",       level),
            _slot("Push-Support",               "push_horizontal", "accessory",      level),
            _slot("Schulter Isolation",         "push_vertical",   "isolation", min(level, 2)),
            _slot("Core",                       "core",            "core",            level),
        ]
    else:  # 60
        return [
            _slot("Haupt-Vertikalzug",          "pull_vertical",   "compound",       level),
            _slot("Horizontales Drücken",       "push_horizontal", "compound",       level),
            _slot("Horizontales Ziehen",        "pull_horizontal", "accessory",      level),
            _slot("Push-Support",               "push_horizontal", "accessory",      level),
            _slot("Hintere Schulter Isolation", "pull_horizontal", "isolation", min(level, 2)),
            _slot("Core",                       "core",            "core",            level),
        ]


def _lower_a_slots(dauer: int, level: int) -> list[dict]:
    if dauer <= 20:
        return [
            _slot("Haupt-Squat (bilateral)",   "squat",      "compound",  level),
            _slot("Hinge / Posterior Chain",   "hinge",      "accessory", level),
            _slot("Core",                      "core",        "core",      level),
        ]
    elif dauer <= 30:
        return [
            _slot("Haupt-Squat (bilateral)",   "squat",      "compound",  level),
            _slot("Haupt-Hinge",               "hinge",      "compound",  level),
            _slot("Unilateral Squat / Lunge",  "single_leg", "accessory", level),
            _slot("Core",                      "core",        "core",      level),
        ]
    elif dauer <= 45:
        return [
            _slot("Haupt-Squat (bilateral)",   "squat",      "compound",       level),
            _slot("Haupt-Hinge",               "hinge",      "compound",       level),
            _slot("Unilateral Squat / Lunge",  "single_leg", "accessory",      level),
            _slot("Posterior Chain Isolation", "hinge",      "isolation", min(level, 2)),
            _slot("Core",                      "core",        "core",           level),
        ]
    else:  # 60
        return [
            _slot("Haupt-Squat (bilateral)",   "squat",      "compound",       level),
            _slot("Haupt-Hinge",               "hinge",      "compound",       level),
            _slot("Unilateral Squat / Lunge",  "single_leg", "accessory",      level),
            _slot("Posterior Chain",           "hinge",      "accessory",      level),
            _slot("Wade / Isolation",          "single_leg", "isolation", min(level, 2)),
            _slot("Core",                      "core",        "core",           level),
        ]


def _lower_b_slots(dauer: int, level: int) -> list[dict]:
    """Hinge-Betonung als Gegenstück zu Lower A (Squat-Betonung)."""
    if dauer <= 20:
        return [
            _slot("Haupt-Hinge (Deadlift)",    "hinge",      "compound",  level),
            _slot("Squat-Support",             "squat",      "accessory", level),
            _slot("Core",                      "core",        "core",      level),
        ]
    elif dauer <= 30:
        return [
            _slot("Haupt-Hinge (Deadlift)",    "hinge",      "compound",  level),
            _slot("Squat-Support / Presse",    "squat",      "compound",  level),
            _slot("Single Leg Hip Hinge",      "single_leg", "accessory", level),
            _slot("Core",                      "core",        "core",      level),
        ]
    elif dauer <= 45:
        return [
            _slot("Haupt-Hinge (Deadlift)",    "hinge",      "compound",       level),
            _slot("Squat-Support / Presse",    "squat",      "compound",       level),
            _slot("Single Leg Hip Hinge",      "single_leg", "accessory",      level),
            _slot("Hip Thrust Isolation",      "hinge",      "isolation", min(level, 2)),
            _slot("Core",                      "core",        "core",           level),
        ]
    else:  # 60
        return [
            _slot("Haupt-Hinge (Deadlift)",    "hinge",      "compound",  level),
            _slot("Squat-Support / Presse",    "squat",      "compound",  level),
            _slot("Single Leg Hip Hinge",      "single_leg", "accessory", level),
            _slot("Posterior Chain / Hip Thrust","hinge",    "accessory", level),
            _slot("Carry / Loaded Carry",      "carry",      "isolation", level),
            _slot("Core",                      "core",        "core",      level),
        ]


def _upper_c_slots(dauer: int, level: int) -> list[dict]:
    """Dritte Upper-Variante (6-Tage A/B/C, Spec :356) — PULL-betont, Lead pull_horizontal
    (Upper B führt pull_vertical → distinkt, doppelt nicht die B-Session)."""
    if dauer <= 20:
        return [
            _slot("Haupt-Horizontales Ziehen", "pull_horizontal", "compound",  level),
            _slot("Vertikales Ziehen",         "pull_vertical",   "accessory", level),
            _slot("Core",                      "core",            "core",       level),
        ]
    elif dauer <= 30:
        return [
            _slot("Haupt-Horizontales Ziehen", "pull_horizontal", "compound",  level),
            _slot("Vertikales Ziehen",         "pull_vertical",   "accessory", level),
            _slot("Push-Support (Balance)",    "push_horizontal", "accessory", level),
            _slot("Core",                      "core",            "core",       level),
        ]
    elif dauer <= 45:
        return [
            _slot("Haupt-Horizontales Ziehen", "pull_horizontal", "compound",       level),
            _slot("Vertikales Ziehen",         "pull_vertical",   "accessory",      level),
            _slot("Push-Support (Balance)",    "push_horizontal", "accessory",      level),
            _slot("Hintere Schulter Isolation","pull_horizontal", "isolation", min(level, 2)),
            _slot("Core",                      "core",            "core",            level),
        ]
    else:  # 60
        return [
            _slot("Haupt-Horizontales Ziehen", "pull_horizontal", "compound",       level),
            _slot("Vertikales Ziehen",         "pull_vertical",   "accessory",      level),
            _slot("Push-Support (Balance)",    "push_horizontal", "accessory",      level),
            _slot("Ruder-Support",             "pull_horizontal", "accessory",      level),
            _slot("Hintere Schulter Isolation","pull_horizontal", "isolation", min(level, 2)),
            _slot("Core",                      "core",            "core",            level),
        ]


def _lower_c_slots(dauer: int, level: int) -> list[dict]:
    """Dritte Lower-Variante (6-Tage A/B/C, Spec :356) — HAMSTRING/HINGE-betont. Lower B führt
    auch hinge (Deadlift-Lead); Lower C betont Hamstring/Curl über Slot-Reihenfolge, nicht neues pattern."""
    if dauer <= 20:
        return [
            _slot("Haupt-Hinge (Hamstring-Fokus)", "hinge",      "compound",  level),
            _slot("Single Leg Hip Hinge",          "single_leg", "accessory", level),
            _slot("Core",                          "core",        "core",      level),
        ]
    elif dauer <= 30:
        return [
            _slot("Haupt-Hinge (Hamstring-Fokus)", "hinge",      "compound",  level),
            _slot("Hamstring-Curl / Posterior",    "hinge",      "accessory", level),
            _slot("Single Leg Hip Hinge",          "single_leg", "accessory", level),
            _slot("Core",                          "core",        "core",      level),
        ]
    elif dauer <= 45:
        return [
            _slot("Haupt-Hinge (Hamstring-Fokus)", "hinge",      "compound",       level),
            _slot("Hamstring-Curl / Posterior",    "hinge",      "accessory",      level),
            _slot("Single Leg Hip Hinge",          "single_leg", "accessory",      level),
            _slot("Wade / Isolation",              "single_leg", "isolation", min(level, 2)),
            _slot("Core",                          "core",        "core",           level),
        ]
    else:  # 60
        return [
            _slot("Haupt-Hinge (Hamstring-Fokus)", "hinge",      "compound",       level),
            _slot("Hamstring-Curl / Posterior",    "hinge",      "accessory",      level),
            _slot("Single Leg Hip Hinge",          "single_leg", "accessory",      level),
            _slot("Squat-Support",                 "squat",      "accessory",      level),
            _slot("Wade / Isolation",              "single_leg", "isolation", min(level, 2)),
            _slot("Core",                          "core",        "core",           level),
        ]


# ── Session-Zusammenbau ────────────────────────────────────────────────────────

def _upper_lower_sessions(level: int, dauer: int) -> list[dict]:
    return [
        _tag_session("w1_s1", "Upper A — Push", _upper_a_slots(dauer, level)),
        _tag_session("w1_s2", "Lower A — Squat", _lower_a_slots(dauer, level)),
        _tag_session("w1_s3", "Upper B — Pull", _upper_b_slots(dauer, level)),
        _tag_session("w1_s4", "Lower B — Hinge", _lower_b_slots(dauer, level)),
    ]


def _upper_lower_3x_sessions(level: int, dauer: int) -> list[dict]:
    """6-Tage A/B/C-Rotation (Spec :356) — sechs DISTINKTE Sessions statt [:2]-Verdopplung von A.
    C-Varianten leanen pull/hamstring → kippt die alte Push2:Pull1-/Squat2:Hinge1-Schieflage in
    Richtung der Spec-Vorgabe „leicht mehr Pull/Hinge". session_id via _renumber beim Aufruf."""
    return [
        _tag_session("w1_s1", "Upper A — Push", _upper_a_slots(dauer, level)),
        _tag_session("w1_s2", "Lower A — Squat", _lower_a_slots(dauer, level)),
        _tag_session("w1_s3", "Upper B — Pull", _upper_b_slots(dauer, level)),
        _tag_session("w1_s4", "Lower B — Hinge", _lower_b_slots(dauer, level)),
        _tag_session("w1_s5", "Upper C — Pull-Fokus", _upper_c_slots(dauer, level)),
        _tag_session("w1_s6", "Lower C — Hamstring-Fokus", _lower_c_slots(dauer, level)),
    ]


def _full_body_sessions(tage: int, level: int, dauer: int) -> list[dict]:
    """Für Full Body: dauer bestimmt Slot-Zahl, aber Patterns bleiben full-body."""
    def _fb_slots(fokus_typ: str) -> list[dict]:
        if fokus_typ == "a":
            # Squat + Push
            if dauer <= 20:
                return [
                    _slot("Haupt-Squat",           "squat",          "compound",  level),
                    _slot("Horizontales Drücken",  "push_horizontal", "accessory", level),
                    _slot("Core",                  "core",            "core",       level),
                ]
            elif dauer <= 30:
                return [
                    _slot("Haupt-Squat",           "squat",          "compound",  level),
                    _slot("Horizontales Drücken",  "push_horizontal", "compound",  level),
                    _slot("Vertikales Ziehen",     "pull_vertical",   "accessory", level),
                    _slot("Core",                  "core",            "core",       level),
                ]
            elif dauer <= 45:
                return [
                    _slot("Haupt-Squat",           "squat",          "compound",  level),
                    _slot("Horizontales Drücken",  "push_horizontal", "compound",  level),
                    _slot("Vertikales Ziehen",     "pull_vertical",   "accessory", level),
                    _slot("Single Leg",            "single_leg",      "accessory", level),
                    _slot("Core",                  "core",            "core",       level),
                ]
            else:  # 60 — bleibt 4-Slot Full Body
                return [
                    _slot("Haupt-Squat (bilateral)", "squat",          "compound",  level),
                    _slot("Horizontales Drücken",    "push_horizontal", "compound",  level),
                    _slot("Vertikales Ziehen",       "pull_vertical",   "accessory", level),
                    _slot("Core",                    "core",            "core",       level),
                ]
        elif fokus_typ == "b":
            # Hinge + Pull
            if dauer <= 20:
                return [
                    _slot("Haupt-Hinge",           "hinge",          "compound",  level),
                    _slot("Horizontales Ziehen",   "pull_horizontal", "accessory", level),
                    _slot("Core",                  "core",            "core",       level),
                ]
            elif dauer <= 30:
                return [
                    _slot("Haupt-Hinge",           "hinge",          "compound",  level),
                    _slot("Horizontales Ziehen",   "pull_horizontal", "compound",  level),
                    _slot("Vertikales Drücken",    "push_vertical",   "accessory", level),
                    _slot("Core",                  "core",            "core",       level),
                ]
            elif dauer <= 45:
                return [
                    _slot("Haupt-Hinge",           "hinge",          "compound",  level),
                    _slot("Horizontales Ziehen",   "pull_horizontal", "compound",  level),
                    _slot("Vertikales Drücken",    "push_vertical",   "accessory", level),
                    _slot("Single Leg",            "single_leg",      "accessory", level),
                    _slot("Core",                  "core",            "core",       level),
                ]
            else:
                return [
                    _slot("Haupt-Hinge",           "hinge",          "compound",  level),
                    _slot("Horizontales Ziehen",   "pull_horizontal", "compound",  level),
                    _slot("Vertikales Drücken",    "push_vertical",   "accessory", level),
                    _slot("Single Leg",            "single_leg",      "accessory", level),
                ]
        else:
            # Full Body C — Single Leg + Carry
            if dauer <= 20:
                return [
                    _slot("Single Leg",            "single_leg",      "accessory", level),
                    _slot("Horizontales Drücken",  "push_horizontal", "compound",  level),
                    _slot("Core",                  "core",            "core",       level),
                ]
            elif dauer <= 30:
                return [
                    _slot("Single Leg",            "single_leg",      "accessory", level),
                    _slot("Horizontales Drücken",  "push_horizontal", "compound",  level),
                    _slot("Horizontales Ziehen",   "pull_horizontal", "compound",  level),
                    _slot("Core",                  "core",            "core",       level),
                ]
            else:
                return [
                    _slot("Single Leg Squat/Lunge","single_leg",      "accessory", level),
                    _slot("Horizontales Drücken",  "push_horizontal", "compound",  level),
                    _slot("Horizontales Ziehen",   "pull_horizontal", "compound",  level),
                    _slot("Carry / Core",          "carry",           "core",       level),
                ]

    templates = [
        {"fokus": "Full Body A — Squat + Push", "slots": _fb_slots("a")},
        {"fokus": "Full Body B — Hinge + Pull", "slots": _fb_slots("b")},
        {"fokus": "Full Body C — Single Leg + Carry", "slots": _fb_slots("c")},
    ]
    return [
        _tag_session(f"w1_s{i+1}", t["fokus"], t["slots"], "kraft")
        for i, t in enumerate(templates[:tage])
    ]


_FOKUS_MAP = {
    "zirkel":     "Zirkel — Ganzkörper Kondition",
    "amrap":      "AMRAP — Kraft-Ausdauer",
    "intervalle": "Intervalle — HIIT Kondition",
    "tabata":     "Tabata — Intervall-Kondition",
    "density":    "Density — Volumen-Kondition",
}

# Naht 4c: reine Conditioning-Tage ziehen aus dem Conditioning-Pool (pool="conditioning"-Marker),
# NICHT mehr aus Kraft-Pattern. 4 Slots = 4 Bewegungen (Zirkel/AMRAP üblich); Block-Formate
# bestimmen ihre Übungszahl über n_blocks. Den Marker liest der Assembler in 4c-2 (A1, deterministisch).
_CONDITIONING_SLOTS = [
    _slot("Conditioning 1", "conditioning", "accessory", 4, pool="conditioning"),
    _slot("Conditioning 2", "conditioning", "accessory", 4, pool="conditioning"),
    _slot("Conditioning 3", "conditioning", "accessory", 4, pool="conditioning"),
    _slot("Conditioning 4", "conditioning", "accessory", 4, pool="conditioning"),
]

def _conditioning_session(idx: int, session_typ: str = "zirkel") -> dict:
    return _tag_session(
        f"w1_s{idx}",
        _FOKUS_MAP.get(session_typ, "Kondition"),
        _CONDITIONING_SLOTS,
        session_typ,
    )


_ZONE2_SLOTS = [
    _slot("Mobility / Squat-Variation", "squat",          "accessory", 2),
    _slot("Hinge / Carries",            "hinge",          "accessory", 2),
    _slot("Push / Pull leicht",         "push_horizontal", "accessory", 2),
    _slot("Core / Cool-Down",           "core",            "core",       1),
]


def _zone2_session(idx: int, rotate_cardio: bool = False) -> dict:
    # Naht 5-3: rotate_cardio markiert den EINEN Longevity-Cardio-Tag (4-Tage-Fall) als
    # Z2/Athletik-alternierend — der Assembler entscheidet je Woche (W1=Zone-2, gerade Wochen
    # = Athletik). Bei 2 Cardio-Tagen (5/6) bleibt Zone-2 fix; der Athletik-Tag ist dort eigen (5-2).
    s = _tag_session(f"w1_s{idx}", "Zone 2 / Longevity", _ZONE2_SLOTS, "zone2")
    if rotate_cardio:
        s["rotate_cardio"] = True
    return s


# Naht 5-2: Athletik-Tag (Longevity) — Übungen kommen aus dem Athletik-Pool (pool="athletik"-Marker),
# der Assembler dosiert skill-gestaffelt. Slot-Pattern ist Platzhalter (für pool-Tage ignoriert).
_ATHLETIK_SLOTS = [
    _slot(f"Athletik {i + 1}", "athletik", "compound", 4, pool="athletik") for i in range(5)
]


def _athletik_session(idx: int) -> dict:
    return _tag_session(f"w1_s{idx}", "Athletik / Longevity", _ATHLETIK_SLOTS, "athletik")


def _ganzkoerper_akzent_session(idx: int, dauer: int, level: int) -> dict:
    """5. Trainingstag (Muskelaufbau/Recomp): Ganzkörper-Akzent (FB-C-Template).
    Schwachstellen-Fokus gestrichen (2026-06-11) — V1.5-Idee, siehe BACKLOG +
    TODO(v15-schwachstelle) in models.py."""
    fb_c = _full_body_sessions(3, level, dauer)[2]
    return _tag_session(f"w1_s{idx}", "Ganzkörper-Akzent", fb_c["slots"], "kraft")


def _renumber(sessions: list[dict]) -> list[dict]:
    for i, s in enumerate(sessions):
        s["session_id"] = f"w1_s{i+1}"
    return sessions


# ── Split selector ─────────────────────────────────────────────────────────────

def _waehle_split_impl(klient: KlientenInput, level: int) -> dict:
    """
    Returns {"split_typ": str, "sessions": list[dict]}.
    Ziel × Tage × Dauer → Split (Spec Thema 4); Slot-Zahl je Dauer in den Templates.
    """
    ziel   = klient.hauptziel
    tage   = klient.tage_pro_woche
    dauer  = klient.session_dauer_min

    if ziel == Hauptziel.muskelaufbau:
        if tage <= 3:
            return {"split_typ": "Full Body 3×", "sessions": _full_body_sessions(tage, level, dauer)}
        elif tage == 4:
            return {"split_typ": "Upper/Lower 4×", "sessions": _upper_lower_sessions(level, dauer)}
        elif tage == 5:
            ul = _upper_lower_sessions(level, dauer)
            akzent = _ganzkoerper_akzent_session(5, dauer, level)
            return {"split_typ": "Upper/Lower 4× + Ganzkörper-Akzent", "sessions": _renumber(ul + [akzent])}
        else:  # 6: Upper/Lower 3× A/B/C — jeder Muskel 3×/Woche, 6 distinkte Sessions (Spec :356)
            ul6 = _upper_lower_3x_sessions(level, dauer)
            return {"split_typ": "Upper/Lower 3× (6 Tage, A/B/C)", "sessions": _renumber(ul6)}

    elif ziel == Hauptziel.recomp:
        # Alle Sessions: Kraftteil + Metcon-Finisher (außer 20 min — zu kurz)
        metcon_typ = None if dauer <= 20 else "amrap"   # "amrap" = nur „hat Finisher"-Signal; echtes Format rotiert {amrap, zirkel} im Assembler (Naht 4e)

        def _recomp_session(sid: str, fokus: str, slots: list[dict]) -> dict:
            return _tag_session(sid, fokus, slots, "kraft", metcon_typ)

        if tage <= 3:
            sessions = [
                _recomp_session(f"w1_s{i+1}", t["fokus"], t["slots"])
                for i, t in enumerate(_full_body_sessions(tage, level, dauer))
            ]
            return {"split_typ": f"Full Body {tage}× + Metcon", "sessions": sessions}
        elif tage == 4:
            ul = _upper_lower_sessions(level, dauer)
            sessions = [_recomp_session(s["session_id"], s["fokus"], s["slots"]) for s in ul]
            return {"split_typ": "Upper/Lower 4× + Metcon", "sessions": sessions}
        elif tage == 5:
            ul = _upper_lower_sessions(level, dauer)
            akzent = _ganzkoerper_akzent_session(5, dauer, level)
            sessions = [_recomp_session(s["session_id"], s["fokus"], s["slots"]) for s in ul + [akzent]]
            return {"split_typ": "Upper/Lower 4× + Ganzkörper-Akzent + Metcon",
                    "sessions": _renumber(sessions)}
        else:  # 6: Upper/Lower 3× A/B/C + Metcon (Struktur identisch Muskelaufbau, Spec :356)
            ul6 = _upper_lower_3x_sessions(level, dauer)
            sessions = [_recomp_session(s["session_id"], s["fokus"], s["slots"]) for s in ul6]
            return {"split_typ": "Upper/Lower 3× + Metcon (6 Tage, A/B/C)", "sessions": _renumber(sessions)}

    elif ziel == Hauptziel.fettabbau:
        # Kraft + Conditioning (Spec Thema 4) — kein reines Conditioning mehr.
        # Naht 3: reine C-Tage rotieren das Format (pick_conditioning_formats, s.u.); Übungs-Rotation +
        # Mischtag-Finisher-Rotation {amrap, zirkel} laufen im Assembler (Naht 4e).
        if tage <= 3:
            # Full Body mit metabolischen Akzenten: Kraft + Metcon-Finisher (wie Recomp)
            metcon_typ = None if dauer <= 20 else "amrap"   # "amrap" = nur „hat Finisher"-Signal; echtes Format rotiert {amrap, zirkel} im Assembler (Naht 4e)
            sessions = [
                _tag_session(s["session_id"], s["fokus"], s["slots"], "kraft", metcon_typ)
                for s in _full_body_sessions(tage, level, dauer)
            ]
            return {"split_typ": f"Full Body {tage}× + Metcon-Akzente", "sessions": sessions}
        # 4/5/6 Tage: (tage−2)× Kraft + Finisher (GEMISCHT, wie Recomp) + fix 2× reine Conditioning.
        # Die 2 C-Tage bekommen 2 verschiedene Formate (räumliche Rotation + Equipment-Bevorzugung,
        # nie 2× hintereinander; Übungs- + Finisher-Rotation = Naht 4e). Ladders ist block-dosierbar
        # (Naht 4d); nur Komplexe bleibt offen (TODO(mvp7-komplexe)).
        cond_fmts = pick_conditioning_formats(level, klient.equipment.value, 2)
        metcon_typ = None if dauer <= 20 else "amrap"
        n_kraft = tage - 2                              # 4→2 · 5→3 · 6→4
        kraft_base = (_full_body_sessions(n_kraft, level, dauer) if n_kraft <= 3
                      else _upper_lower_sessions(level, dauer))
        kraft = [_tag_session(s["session_id"], s["fokus"], s["slots"], "kraft", metcon_typ)
                 for s in kraft_base]
        cond = [_conditioning_session(n_kraft + 1, cond_fmts[0]),
                _conditioning_session(n_kraft + 2, cond_fmts[1])]
        sessions = _renumber(kraft + cond)
        return {"split_typ": f"{n_kraft}× Kraft+Metcon + 2× Conditioning", "sessions": sessions}

    else:  # Hauptziel.longevity — Generalist: Kraft + Zone-2-Cardio (Spec Thema 4)
        if tage <= 3:
            return {"split_typ": "Full Body 3× (Longevity)",
                    "sessions": _full_body_sessions(tage, level, dauer)}
        elif tage == 4:
            # Naht 5-3: 1 Cardio-Tag/Woche → über die 4 Wochen alternierend Zone-2/Athletik (W1=Z2).
            fb = _full_body_sessions(3, level, dauer)
            return {"split_typ": "3× Kraft + Cardio (Zone 2 / Athletik alternierend)",
                    "sessions": _renumber(fb + [_zone2_session(4, rotate_cardio=True)])}
        elif tage == 5:
            # Naht 5-2: 2 Cardio-Tage/Woche → 1× Zone-2 + 1× Athletik (Spec Thema 4, räumlich).
            fb = _full_body_sessions(3, level, dauer)
            return {"split_typ": "3× Kraft + Zone 2 + Athletik",
                    "sessions": _renumber(fb + [_zone2_session(4), _athletik_session(5)])}
        else:  # 6: jeder Muskel 2× Kraft + 2 Cardio-Tage (1× Zone-2 + 1× Athletik)
            ul = _upper_lower_sessions(level, dauer)
            return {"split_typ": "Upper/Lower 4× + Zone 2 + Athletik",
                    "sessions": _renumber(ul + [_zone2_session(5), _athletik_session(6)])}


# ── Equipment-bewusste Carry-Behandlung ────────────────────────────────────────

def _carry_moeglich(klient: KlientenInput, level: int) -> bool:
    """Ground truth: hat der Klient nach Equipment + Level + Verletzungsfilter eine ECHTE
    Carry-Übung? `filtere_uebungen` backfillt einen leeren carry-Pool über
    `_apply_pattern_fallback` mit Core-Übungen (`ersatz_fuer="carry"`) — die zählen NICHT
    als befüllbares Carry. Daher: mindestens eine carry-Übung OHNE `ersatz_fuer`-Marker."""
    pool = filtere_uebungen(klient, level)
    return any(not ex.get("ersatz_fuer") for ex in pool.get("carry", []))


def _ersetze_unbefuellbaren_carry(sessions: list[dict]) -> None:
    """Klient ohne echtes Carry (Equipment): Carry-Slots auflösen (in-place). Diskriminiert
    am tier des Carry-Slots — deckt sich mit den zwei Carry-Templates:
      • tier 'core'  → Full Body C, wo Carry den Core-Slot ERSETZT → zurück zu einem Core-Slot
        (Session bleibt gleich lang, behält einen Core).
      • sonst (tier 'isolation' = Lower B, Carry ist ZUSATZ-Slot, Core separat vorhanden)
        → Slot ersatzlos entfernen (Session wird um 1 kürzer; kein doppelter Core)."""
    for s in sessions:
        neue: list[dict] = []
        for slot in s["slots"]:
            if slot["pattern"] != "carry":
                neue.append(slot)
            elif slot["tier"] == "core":
                neue.append(_slot("Core", "core", "core", slot["max_level"]))
            # tier != core → weglassen
        s["slots"] = neue
        # Befund 6: Label ↔ Inhalt — wenn kein Carry-Slot mehr da ist, "+ Carry" aus dem fokus entfernen
        # (betrifft "Full Body C — Single Leg + Carry"), sonst verspricht das Label einen fehlenden Slot.
        if "Carry" in s["fokus"] and not any(sl["pattern"] == "carry" for sl in neue):
            s["fokus"] = s["fokus"].replace(" + Carry", "").rstrip(" +")


def waehle_split(klient: KlientenInput, level: int) -> dict:
    """Ziel × Tage × Dauer → Split (Spec Thema 4). Danach: Carry-Slots auflösen, wenn der
    Klient equipment-bedingt KEIN echtes Carry befüllen kann (nur dieser Fall — andere leere
    Pools laufen bewusst weiter über den 9-3a-Vollständigkeits-Check / MVP-5-Fallback)."""
    result = _waehle_split_impl(klient, level)
    if not _carry_moeglich(klient, level):
        _ersetze_unbefuellbaren_carry(result["sessions"])
    return result
