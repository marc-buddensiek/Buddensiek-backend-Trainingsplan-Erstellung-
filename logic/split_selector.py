"""
Hauptziel × Tage → Split-Name + Sessions mit Slots

Split-Tabelle aus PDF Seite 8:
  muskelaufbau: 3T=Full Body 3×, 4T=Upper/Lower+Mobility, 5T=Upper/Lower×2+Mobility
  fettabbau:    3T=Full Body+Conditioning, 4T=Upper/Lower+Conditioning+Mobility
  ausdauer:     3T=Full Body 3×, 4T=Upper/Lower+Mobility
  gesundheit:   3T=Full Body+Zone2, 4T=Upper/Lower+Zone2+Mobility

Ab 4 Tagen immer 1× Mobility-Session als eigene Session.

Sessions: list of {"session_id": "w1_sN", "fokus": str, "session_typ": str, "slots": [...]}
"""

from __future__ import annotations
from models import KlientenInput, Hauptziel


def _slot(beschreibung: str, pattern: str, max_level: int = 4) -> dict:
    return {"beschreibung": beschreibung, "pattern": pattern, "max_level": max_level}


def _tag_session(session_id: str, fokus: str, slots: list[dict], session_typ: str = "kraft") -> dict:
    return {"session_id": session_id, "fokus": fokus, "session_typ": session_typ, "slots": slots}


# ── Session templates ──────────────────────────────────────────────────────────

def _full_body_sessions(tage: int, level: int) -> list[dict]:
    templates = [
        {
            "fokus": "Full Body A — Squat + Push",
            "slots": [
                _slot("Haupt-Squat (bilateral)", "squat", level),
                _slot("Horizontales Drücken", "push_horizontal", level),
                _slot("Vertikales Ziehen", "pull_vertical", level),
                _slot("Core", "core", level),
            ],
        },
        {
            "fokus": "Full Body B — Hinge + Pull",
            "slots": [
                _slot("Haupt-Hinge", "hinge", level),
                _slot("Horizontales Ziehen", "pull_horizontal", level),
                _slot("Vertikales Drücken", "push_vertical", level),
                _slot("Single Leg", "single_leg", level),
            ],
        },
        {
            "fokus": "Full Body C — Single Leg + Carry",
            "slots": [
                _slot("Single Leg Squat/Lunge", "single_leg", level),
                _slot("Horizontales Drücken", "push_horizontal", level),
                _slot("Horizontales Ziehen", "pull_horizontal", level),
                _slot("Carry / Core", "carry", level),
            ],
        },
    ]
    return [
        _tag_session(f"w1_s{i+1}", t["fokus"], t["slots"], "kraft")
        for i, t in enumerate(templates[:tage])
    ]


def _upper_lower_sessions(level: int) -> list[dict]:
    return [
        _tag_session("w1_s1", "Upper A — Push", [
            _slot("Haupt-Horizontaldruck (Compound)", "push_horizontal", level),
            _slot("Vertikales Drücken", "push_vertical", level),
            _slot("Horizontales Ziehen (Balance)", "pull_horizontal", level),
            _slot("Isolation / Prähab", "push_horizontal", min(level, 2)),
        ]),
        _tag_session("w1_s2", "Lower A — Squat", [
            _slot("Haupt-Squat (bilateral)", "squat", level),
            _slot("Single Leg Squat / Lunge", "single_leg", level),
            _slot("Hinge-Support (Romanian)", "hinge", level),
            _slot("Core", "core", level),
        ]),
        _tag_session("w1_s3", "Upper B — Pull", [
            _slot("Haupt-Vertikalzug (Compound)", "pull_vertical", level),
            _slot("Horizontales Ziehen", "pull_horizontal", level),
            _slot("Drück-Support", "push_horizontal", level),
            _slot("Schulter / Prähab", "push_vertical", min(level, 2)),
        ]),
        _tag_session("w1_s4", "Lower B — Hinge", [
            _slot("Haupt-Hinge (Deadlift-Variante)", "hinge", level),
            _slot("Squat-Support / Beinpresse", "squat", level),
            _slot("Single Leg Hip Hinge", "single_leg", level),
            _slot("Core / Carry", "core", level),
        ]),
    ]


def _conditioning_session(idx: int, session_typ: str = "zirkel") -> dict:
    fokus_map = {
        "zirkel": "Kondition — Zirkel",
        "amrap":  "Kondition — AMRAP",
        "emom":   "Kondition — EMOM",
    }
    return _tag_session(
        f"w1_s{idx}",
        fokus_map.get(session_typ, "Kondition — Zirkel"),
        [
            _slot("Ganzkörper-Compound (leicht)", "squat", 2),
            _slot("Hinge / Swing", "hinge", 2),
            _slot("Push-Variation", "push_horizontal", 2),
            _slot("Core / Carry", "core", 2),
        ],
        session_typ,
    )


def _zone2_session(idx: int) -> dict:
    return _tag_session(
        f"w1_s{idx}",
        "Zone 2 / Longevity",
        [
            _slot("Mobility / Squat-Variation", "squat", 2),
            _slot("Hinge / Carries", "hinge", 2),
            _slot("Push / Pull leicht", "push_horizontal", 2),
            _slot("Core / Cool-Down", "core", 1),
        ],
        "kraft",
    )


def _mobility_session(idx: int) -> dict:
    return _tag_session(
        f"w1_s{idx}",
        "Mobility & Beweglichkeit",
        [],  # Assembler verwendet hardcodierte Mobility-Übungen — keine Slots nötig
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
    Ab 4 Tagen enthält jede Woche 1× Mobility-Session als letzten Slot.
    """
    ziel = klient.hauptziel
    tage = klient.tage_pro_woche
    mit_mobility = tage >= 4

    if ziel == Hauptziel.muskelaufbau:
        if tage <= 3:
            return {"split_typ": "Full Body 3×", "sessions": _full_body_sessions(tage, level)}
        elif tage == 4:
            sessions = _upper_lower_sessions(level)[:3] + [_mobility_session(4)]
            return {"split_typ": "Upper/Lower + Mobility", "sessions": sessions}
        elif tage == 5:
            sessions = _upper_lower_sessions(level) + [_mobility_session(5)]
            return {"split_typ": "Upper/Lower × 2 + Mobility", "sessions": sessions}
        else:  # 6 Tage
            ul = _upper_lower_sessions(level)
            extra = _full_body_sessions(1, level)[0]
            extra["session_id"] = "w1_s5"
            sessions = ul + [extra, _mobility_session(6)]
            return {"split_typ": "PPL + Mobility", "sessions": sessions}

    elif ziel == Hauptziel.recomp:
        # Recomp = Kraft + EMOM (Fettabbau nutzt Zirkel, Recomp nutzt EMOM)
        if tage <= 3:
            kraft = _full_body_sessions(tage - 1, level) if tage > 1 else []
            sessions = _renumber(kraft + [_conditioning_session(tage, "emom")])
            return {"split_typ": "Full Body + EMOM", "sessions": sessions}
        elif tage == 4:
            ul = _upper_lower_sessions(level)[:2]
            sessions = _renumber(ul + [_conditioning_session(3, "emom"), _mobility_session(4)])
            return {"split_typ": "Upper/Lower + EMOM + Mobility", "sessions": sessions}
        else:
            ul = _upper_lower_sessions(level)
            sessions = _renumber(ul + [_conditioning_session(5, "emom"), _mobility_session(6)])
            return {"split_typ": "Upper/Lower x2 + EMOM + Mobility", "sessions": sessions[:tage]}

    elif ziel == Hauptziel.fettabbau:
        if tage <= 3:
            kraft = _full_body_sessions(tage - 1, level) if tage > 1 else []
            sessions = _renumber(kraft + [_conditioning_session(tage, "zirkel")])
            return {"split_typ": "Full Body + Conditioning", "sessions": sessions}
        elif tage == 4:
            ul = _upper_lower_sessions(level)[:2]
            sessions = _renumber(ul + [_conditioning_session(3, "zirkel"), _mobility_session(4)])
            return {"split_typ": "Upper/Lower + Conditioning + Mobility", "sessions": sessions}
        else:  # 5-6 Tage
            ul = _upper_lower_sessions(level)
            sessions = _renumber(ul + [_conditioning_session(5, "zirkel"), _mobility_session(6)])
            return {"split_typ": "Upper/Lower × 2 + Conditioning + Mobility", "sessions": sessions[:tage]}

    elif ziel == Hauptziel.ausdauer:
        if tage <= 3:
            return {"split_typ": "Full Body Strength", "sessions": _full_body_sessions(tage, level)}
        elif tage == 4:
            ul = _upper_lower_sessions(level)[:3]
            sessions = ul + [_mobility_session(4)]
            return {"split_typ": "Upper/Lower + Mobility", "sessions": sessions}
        else:
            ul = _upper_lower_sessions(level)
            sessions = _renumber(ul + [_conditioning_session(5, "intervalle"), _mobility_session(6)])
            return {"split_typ": "Upper/Lower × 2 + Intervalle + Mobility", "sessions": sessions[:tage]}

    else:  # gesundheit / longevity
        if tage <= 3:
            sessions = _full_body_sessions(tage - 1, level) if tage > 1 else []
            sessions = _renumber(sessions + [_zone2_session(tage)])
            return {"split_typ": "Full Body + Zone 2", "sessions": sessions}
        elif tage == 4:
            ul = _upper_lower_sessions(level)[:2]
            sessions = _renumber(ul + [_zone2_session(3), _mobility_session(4)])
            return {"split_typ": "Upper/Lower + Zone 2 + Mobility", "sessions": sessions}
        else:
            ul = _upper_lower_sessions(level)[:3]
            sessions = _renumber(ul + [_zone2_session(4), _mobility_session(5)])
            return {"split_typ": "Upper/Lower + Zone 2 + Mobility", "sessions": sessions[:tage]}
