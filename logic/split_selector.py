"""
Hauptziel × Tage × session_dauer_min → Split-Name + Sessions mit Slots

Slot-Anzahl nach Session-Dauer:
  20 min → 3 Slots: [compound, accessory, core]
  30 min → 4 Slots: [compound, compound, accessory, core]
  45 min → 5 Slots: [compound, compound, accessory, isolation, core]
  60 min → 6 Slots: [compound, compound, accessory, accessory, isolation, core]

Special Case: session_dauer_min == 20 → immer Full Body, unabhängig von tage_pro_woche
Mobility erst ab 5 Tagen als eigene Session (nur wenn dauer >= 30).
"""

from __future__ import annotations
from models import KlientenInput, Hauptziel


def _slot(beschreibung: str, pattern: str, tier: str = "compound", max_level: int = 4) -> dict:
    return {"beschreibung": beschreibung, "pattern": pattern, "tier": tier, "max_level": max_level}


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


# ── Session-Zusammenbau ────────────────────────────────────────────────────────

def _upper_lower_sessions(level: int, dauer: int) -> list[dict]:
    return [
        _tag_session("w1_s1", "Upper A — Push", _upper_a_slots(dauer, level)),
        _tag_session("w1_s2", "Lower A — Squat", _lower_a_slots(dauer, level)),
        _tag_session("w1_s3", "Upper B — Pull", _upper_b_slots(dauer, level)),
        _tag_session("w1_s4", "Lower B — Hinge", _lower_b_slots(dauer, level)),
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
    "emom":       "EMOM — Metabolic Training",
    "intervalle": "Intervalle — HIIT Kondition",
}

_CONDITIONING_SLOTS = [
    _slot("Compound / Squat",    "squat",          "accessory", 2),
    _slot("Hinge / Swing",       "hinge",          "accessory", 2),
    _slot("Push-Variation",      "push_horizontal", "accessory", 2),
    _slot("Core / Carry",        "core",            "core",       2),
]

def _conditioning_session(idx: int, session_typ: str = "zirkel") -> dict:
    return _tag_session(
        f"w1_s{idx}",
        _FOKUS_MAP.get(session_typ, "Kondition"),
        _CONDITIONING_SLOTS,
        session_typ,
    )


def _zone2_session(idx: int) -> dict:
    # TODO(mvp7-athletik): V1 nur Zone-2-Cardio-Tage; die Athletik-Rotation
    # (Spec Thema 4/6) kommt mit den MVP-7-Athletik-Übungen (Bibliothek: 0 vorhanden).
    return _tag_session(
        f"w1_s{idx}",
        "Zone 2 / Longevity",
        [
            _slot("Mobility / Squat-Variation", "squat",          "accessory", 2),
            _slot("Hinge / Carries",            "hinge",          "accessory", 2),
            _slot("Push / Pull leicht",         "push_horizontal", "accessory", 2),
            _slot("Core / Cool-Down",           "core",            "core",       1),
        ],
        "zone2",
    )


def _ganzkoerper_akzent_session(idx: int, dauer: int, level: int) -> dict:
    """5. Trainingstag (Muskelaufbau/Recomp): Ganzkörper-Akzent (FB-C-Template).
    Schwachstellen-Fokus gestrichen (2026-06-11) — V1.5-Idee, siehe BACKLOG +
    TODO(v15-schwachstelle) in models.py."""
    fb_c = _full_body_sessions(3, level, dauer)[2]
    return _tag_session(f"w1_s{idx}", "Ganzkörper-Akzent", fb_c["slots"], "kraft")


def _mobility_session(idx: int) -> dict:
    return _tag_session(
        f"w1_s{idx}",
        "Mobility & Beweglichkeit",
        [],
        "mobility",
    )


def _renumber(sessions: list[dict]) -> list[dict]:
    for i, s in enumerate(sessions):
        s["session_id"] = f"w1_s{i+1}"
    return sessions


# ── Split selector ─────────────────────────────────────────────────────────────

def waehle_split(klient: KlientenInput, level: int) -> dict:
    """
    Returns {"split_typ": str, "sessions": list[dict]}.
    20-min → immer Full Body.
    Mobility nur ab 5 Tagen (und nur wenn dauer >= 30).
    """
    ziel   = klient.hauptziel
    tage   = klient.tage_pro_woche
    dauer  = klient.session_dauer_min

    # ── 20 Min: immer Full Body, egal wie viele Tage ──────────────────────────
    if dauer == 20:
        return {
            "split_typ": f"Full Body {tage}×",
            "sessions":  _full_body_sessions(min(tage, 3), level, dauer),
        }

    # ── Normale Split-Logik ───────────────────────────────────────────────────

    if ziel == Hauptziel.muskelaufbau:
        if tage <= 3:
            return {"split_typ": "Full Body 3×", "sessions": _full_body_sessions(tage, level, dauer)}
        elif tage == 4:
            return {"split_typ": "Upper/Lower 4×", "sessions": _upper_lower_sessions(level, dauer)}
        elif tage == 5:
            ul = _upper_lower_sessions(level, dauer)
            akzent = _ganzkoerper_akzent_session(5, dauer, level)
            return {"split_typ": "Upper/Lower 4× + Ganzkörper-Akzent", "sessions": _renumber(ul + [akzent])}
        else:  # 6: Upper/Lower 3× — jeder Muskel 3×/Woche (PPL entfällt, Spec Thema 4)
            ul6 = _upper_lower_sessions(level, dauer) + _upper_lower_sessions(level, dauer)[:2]
            return {"split_typ": "Upper/Lower 3× (6 Tage)", "sessions": _renumber(ul6)}

    elif ziel == Hauptziel.recomp:
        # Alle Sessions: Kraftteil + Metcon-Finisher (außer 20 min — zu kurz)
        metcon_typ = None if dauer <= 20 else "amrap" if dauer <= 45 else "emom"

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
        else:  # 6: Upper/Lower 3× + Metcon (Struktur identisch Muskelaufbau, Spec Thema 4)
            ul6 = _upper_lower_sessions(level, dauer) + _upper_lower_sessions(level, dauer)[:2]
            sessions = [_recomp_session(s["session_id"], s["fokus"], s["slots"]) for s in ul6]
            return {"split_typ": "Upper/Lower 3× + Metcon (6 Tage)", "sessions": _renumber(sessions)}

    elif ziel == Hauptziel.fettabbau:
        # Kraft + Conditioning (Spec Thema 4) — kein reines Conditioning mehr.
        # TODO(mvp7-formate): V1 nutzt die 4 bestehenden Formate, statisch je Session;
        # Block-Rotation ("jeder C-Tag im Block ein anderes Format") + neue Formate mit MVP-7.
        if tage <= 3:
            # Full Body mit metabolischen Akzenten: Kraft + Metcon-Finisher (wie Recomp)
            metcon_typ = None if dauer <= 20 else "amrap" if dauer <= 45 else "emom"
            sessions = [
                _tag_session(s["session_id"], s["fokus"], s["slots"], "kraft", metcon_typ)
                for s in _full_body_sessions(tage, level, dauer)
            ]
            return {"split_typ": f"Full Body {tage}× + Metcon-Akzente", "sessions": sessions}
        elif tage == 4:
            fb = _full_body_sessions(3, level, dauer)
            sessions = _renumber(fb + [_conditioning_session(4, "intervalle")])
            return {"split_typ": "3× Kraft + Conditioning", "sessions": sessions}
        elif tage == 5:
            ul = _upper_lower_sessions(level, dauer)
            sessions = _renumber(ul + [_conditioning_session(5, "intervalle")])
            return {"split_typ": "Upper/Lower 4× + Conditioning", "sessions": sessions}
        else:  # 6: 4 Kraft + 2 Conditioning (zwei unterschiedliche Formate, Spec Thema 6)
            ul = _upper_lower_sessions(level, dauer)
            sessions = _renumber(ul + [_conditioning_session(5, "intervalle"),
                                       _conditioning_session(6, "amrap")])
            return {"split_typ": "Upper/Lower 4× + 2× Conditioning", "sessions": sessions}

    else:  # Hauptziel.longevity — Generalist: Kraft + Zone-2-Cardio (Spec Thema 4)
        if tage <= 3:
            return {"split_typ": "Full Body 3× (Longevity)",
                    "sessions": _full_body_sessions(tage, level, dauer)}
        elif tage == 4:
            fb = _full_body_sessions(3, level, dauer)
            return {"split_typ": "3× Kraft + Zone 2",
                    "sessions": _renumber(fb + [_zone2_session(4)])}
        elif tage == 5:
            fb = _full_body_sessions(3, level, dauer)
            return {"split_typ": "3× Kraft + 2× Zone 2",
                    "sessions": _renumber(fb + [_zone2_session(4), _zone2_session(5)])}
        else:  # 6: jeder Muskel 2× Kraft + 2 Cardio-Tage
            ul = _upper_lower_sessions(level, dauer)
            return {"split_typ": "Upper/Lower 4× + 2× Zone 2",
                    "sessions": _renumber(ul + [_zone2_session(5), _zone2_session(6)])}
