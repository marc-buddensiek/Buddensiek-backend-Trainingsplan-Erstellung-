"""
Hauptziel × Tage → Split-Name + Sessions mit Slots

Split-Tabelle aus PDF Seite 8:
  muskelaufbau: 3T=Full Body, 4T=Upper/Lower, 5T=PPL+UL
  fettabbau:    3T=Full Body+Conditioning, 4T=Upper/Lower+2×Conditioning, 5T=4×Kraft+Conditioning
  ausdauer:     3T=Full Body strength, 4T=Upper/Lower+Power, 5T=Lower/Upper×2+Conditioning
  gesundheit:   3T=Full Body+Zone2, 4T=Upper/Lower+2×Zone2, 5T=individuell

Sessions: list of {"session_id": "w1_sN", "fokus": str, "slots": [{"beschreibung": str, "pattern": str, "max_level": int}]}
"""

from __future__ import annotations
from models import KlientenInput, Hauptziel


def _slot(beschreibung: str, pattern: str, max_level: int = 4) -> dict:
    return {"beschreibung": beschreibung, "pattern": pattern, "max_level": max_level}


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
    return [{"session_id": f"w1_s{i+1}", **t} for i, t in enumerate(templates[:tage])]


def _upper_lower_sessions(level: int) -> list[dict]:
    return [
        {
            "session_id": "w1_s1",
            "fokus": "Upper A — Push",
            "slots": [
                _slot("Haupt-Horizontaldruck (Compound)", "push_horizontal", level),
                _slot("Vertikales Drücken", "push_vertical", level),
                _slot("Horizontales Ziehen (Balance)", "pull_horizontal", level),
                _slot("Isolation / Prähab", "push_horizontal", min(level, 2)),
            ],
        },
        {
            "session_id": "w1_s2",
            "fokus": "Lower A — Squat",
            "slots": [
                _slot("Haupt-Squat (bilateral)", "squat", level),
                _slot("Single Leg Squat / Lunge", "single_leg", level),
                _slot("Hinge-Support (Romanian)", "hinge", level),
                _slot("Core", "core", level),
            ],
        },
        {
            "session_id": "w1_s3",
            "fokus": "Upper B — Pull",
            "slots": [
                _slot("Haupt-Vertikalzug (Compound)", "pull_vertical", level),
                _slot("Horizontales Ziehen", "pull_horizontal", level),
                _slot("Drück-Support", "push_horizontal", level),
                _slot("Schulter / Prähab", "push_vertical", min(level, 2)),
            ],
        },
        {
            "session_id": "w1_s4",
            "fokus": "Lower B — Hinge",
            "slots": [
                _slot("Haupt-Hinge (Deadlift-Variante)", "hinge", level),
                _slot("Squat-Support / Beinpresse", "squat", level),
                _slot("Single Leg Hip Hinge", "single_leg", level),
                _slot("Core / Carry", "core", level),
            ],
        },
    ]


def _conditioning_session(idx: int) -> dict:
    return {
        "session_id": f"w1_s{idx}",
        "fokus": "Conditioning / HIIT",
        "slots": [
            _slot("Ganzkörper-Compound (leicht)", "squat", 2),
            _slot("Hinge / Swing", "hinge", 2),
            _slot("Push-Variation", "push_horizontal", 2),
            _slot("Core / Carry", "core", 2),
        ],
    }


def _zone2_session(idx: int) -> dict:
    return {
        "session_id": f"w1_s{idx}",
        "fokus": "Zone 2 / Longevity",
        "slots": [
            _slot("Mobility / Squat-Variation", "squat", 2),
            _slot("Hinge / Carries", "hinge", 2),
            _slot("Push / Pull leicht", "push_horizontal", 2),
            _slot("Core / Cool-Down", "core", 1),
        ],
    }


# ── Split selector ─────────────────────────────────────────────────────────────

def waehle_split(klient: KlientenInput, level: int) -> dict:
    """
    Returns {"split_typ": str, "sessions": list[dict]}.
    """
    ziel = klient.hauptziel
    tage = klient.tage_pro_woche

    if ziel == Hauptziel.muskelaufbau:
        if tage <= 3:
            return {"split_typ": "Full Body 3×", "sessions": _full_body_sessions(tage, level)}
        elif tage == 4:
            return {"split_typ": "Upper/Lower", "sessions": _upper_lower_sessions(level)}
        else:  # 5-6 days
            sessions = _upper_lower_sessions(level)
            # Add extra sessions cycling through upper/lower
            for i in range(4, tage):
                extra = _full_body_sessions(1, level)[0]
                extra["session_id"] = f"w1_s{i+1}"
                extra["fokus"] = f"Zusatz — Full Body {i-2}"
                sessions.append(extra)
            return {"split_typ": "PPL / Upper-Lower Hybrid", "sessions": sessions}

    elif ziel == Hauptziel.fettabbau:
        if tage <= 3:
            kraft = _full_body_sessions(tage - 1, level) if tage > 1 else []
            sessions = kraft + [_conditioning_session(tage)]
            for i, s in enumerate(sessions):
                s["session_id"] = f"w1_s{i+1}"
            return {"split_typ": "Full Body + Conditioning", "sessions": sessions}
        elif tage == 4:
            ul = _upper_lower_sessions(level)[:2]
            sessions = ul + [_conditioning_session(3), _conditioning_session(4)]
            return {"split_typ": "Upper/Lower + 2× Conditioning", "sessions": sessions}
        else:
            ul = _upper_lower_sessions(level)
            sessions = ul + [_conditioning_session(5)]
            return {"split_typ": "4× Kraft + 1× Conditioning", "sessions": sessions}

    elif ziel == Hauptziel.ausdauer:
        if tage <= 3:
            return {"split_typ": "Full Body Strength", "sessions": _full_body_sessions(tage, level)}
        elif tage == 4:
            ul = _upper_lower_sessions(level)
            return {"split_typ": "Upper/Lower + Power-Akzente", "sessions": ul}
        else:
            sessions = _upper_lower_sessions(level) + [_conditioning_session(5)]
            return {"split_typ": "Lower/Upper × 2 + Conditioning", "sessions": sessions}

    else:  # gesundheit / longevity
        if tage <= 3:
            sessions = _full_body_sessions(tage - 1, level) if tage > 1 else []
            sessions.append(_zone2_session(tage))
            for i, s in enumerate(sessions):
                s["session_id"] = f"w1_s{i+1}"
            return {"split_typ": "Full Body + Zone 2", "sessions": sessions}
        elif tage == 4:
            ul = _upper_lower_sessions(level)[:2]
            sessions = ul + [_zone2_session(3), _zone2_session(4)]
            return {"split_typ": "Upper/Lower + 2× Zone 2", "sessions": sessions}
        else:
            sessions = _upper_lower_sessions(level) + [_zone2_session(5)]
            return {"split_typ": "Upper/Lower + Zone 2", "sessions": sessions}
