"""
Kundenseitige Anzeige-Labels für das interne `fokus`-Feld (Single Source).

`fokus` bleibt der interne Routing-Key (Substring-Parsing für warm_up/cool_down/cardio/zone
im Assembler). Das kundenfreundliche Label entsteht NUR hier — Assembler (fokus_anzeige im
JSON) UND pdf_generator importieren von hier, kein Duplikat.

Befund 6: Upper/Lower-Tage sind Schwerpunkt-Tage (bewusst gemischt, nicht exklusiv) → das
Label nennt den Schwerpunkt, nicht den internen A/B/C-Key. Doppelte Schwerpunkt-Tage (z.B.
Upper B + Upper C beide „Pull") unterscheidet das Frontend über tag/session_id, nicht das Label.
"""
from __future__ import annotations

# Keys = exakte interne fokus-Strings (em-dash „—" wie in split_selector._FOKUS_MAP / _tag_session).
# Werte = kundenseitige Labels (en-dash „–").
_FOKUS_ANZEIGE: dict[str, str] = {
    "Upper A — Push":                   "Oberkörper – Push",
    "Upper B — Pull":                   "Oberkörper – Pull",
    "Upper C — Pull-Fokus":             "Oberkörper – Pull",
    "Lower A — Squat":                  "Unterkörper – Squat",
    "Lower B — Hinge":                  "Unterkörper – Hinge",
    "Lower C — Hamstring-Fokus":        "Unterkörper – Hamstring",
    "Full Body A — Squat + Push":       "Ganzkörper",
    "Full Body B — Hinge + Pull":       "Ganzkörper",
    "Full Body C — Single Leg + Carry": "Ganzkörper",
    "Full Body C — Single Leg":         "Ganzkörper",
    "Ganzkörper-Akzent":                "Ganzkörper",
    "Zone 2 / Longevity":               "Zone 2 – Grundlagenausdauer",
    "Athletik / Longevity":             "Athletik – Schnellkraft & Mobilität",
    "Zirkel — Ganzkörper Kondition":    "Zirkel – Ganzkörper-Kondition",
    "AMRAP — Kraft-Ausdauer":           "AMRAP – Kraft-Ausdauer",
    "Intervalle — HIIT Kondition":      "Intervalle – HIIT-Kondition",
    "Tabata — Intervall-Kondition":     "Tabata – Intervall-Kondition",
    "Density — Volumen-Kondition":      "Density – Volumen-Kondition",
    "Kondition":                        "Kondition",
}


def anzeige_fokus(fokus: str) -> str:
    """Internes fokus → kundenseitiges Label. Fallback NIE der rohe Routing-Key:
    Teil vor „—"/„/" (gesäubert), sonst generisch „Training"."""
    label = _FOKUS_ANZEIGE.get(fokus)
    if label is not None:
        return label
    for sep in ("—", "/"):
        if sep in fokus:
            kopf = fokus.split(sep, 1)[0].strip()
            return kopf or "Training"
    return "Training"


# session_typ → internes fokus-Label (Single Source). split_selector setzt es zur Split-Zeit;
# der Assembler leitet es neu ab, wenn er session_typ NACH der Split-fokus-Vergabe ändert
# (Conditioning-Erstformat-Tausch · Athletik→zone2-Fallback). Conditioning-Formate (zirkel/amrap/
# intervalle/tabata/density; ladders→Fallback "Kondition") + Longevity-Cardio-Typen (zone2/athletik).
_SESSION_TYP_LABEL: dict[str, str] = {
    "zirkel":     "Zirkel — Ganzkörper Kondition",
    "amrap":      "AMRAP — Kraft-Ausdauer",
    "intervalle": "Intervalle — HIIT Kondition",
    "tabata":     "Tabata — Intervall-Kondition",
    "density":    "Density — Volumen-Kondition",
    "zone2":      "Zone 2 / Longevity",
    "athletik":   "Athletik / Longevity",
}


def label_fuer_session_typ(session_typ: str) -> str:
    """fokus-Label für einen session_typ (Fallback „Kondition" — wie die bisherige Split-Vergabe)."""
    return _SESSION_TYP_LABEL.get(session_typ, "Kondition")
