"""
Level + Woche-Typ + Recovery → ziel_saetze + ziel_rpe

Volumen-Tabelle (Sätze pro Übung) aus PDF Seite 9:
  Level 1: RPE 6-7, 2-3 Sätze
  Level 2: RPE 7-8, 3-4 Sätze
  Level 3: RPE 7-9, 3-5 Sätze
  Level 4: RPE 7-9, 4-5 Sätze

Periodisierung (4-Wochen-Wave):
  Akkumulation  → unteres Drittel des Ranges (Volumen aufbauen)
  Progression   → mittleres Drittel
  Intensivierung → oberes Drittel
  Peak          → selbes Volumen wie Intensivierung, maximale Intensität

Recovery-Modifier aus PDF Seite 10:
  Stress 8+ ODER Schlaf < 6h  → Volumen -20%, RPE-Cap 8
  Stress < 5 UND Schlaf 7+h   → Volumen +10% möglich
  Sonst                        → Standard
"""

from __future__ import annotations
from typing import Literal
from models import KlientenInput


WocheTyp = Literal["akkumulation", "progression", "intensivierung", "peak"]

# (saetze_low, saetze_high, rpe_low, rpe_high) per Level
_LEVEL_RANGES = {
    1: (2, 3, 6, 7),
    2: (3, 4, 7, 8),
    3: (3, 5, 7, 9),
    4: (4, 5, 7, 9),
}

_WOCHE_FAKTOR = {
    "akkumulation":   0.0,   # lower bound
    "progression":    0.5,   # mid
    "intensivierung": 1.0,   # upper bound
    "peak":           1.0,   # same volume as intensivierung, max intensity
}


def _recovery_modifier(klient: KlientenInput) -> str:
    """Returns 'reduziert', 'standard', or 'erhoht'."""
    if klient.stress_level >= 8 or klient.schlaf_stunden < 6:
        return "reduziert"
    if klient.stress_level < 5 and klient.schlaf_stunden >= 7:
        return "erhoht"
    return "standard"


def berechne_volumen(
    klient: KlientenInput,
    level: int,
    woche_typ: WocheTyp,
) -> dict:
    """
    Returns dict with:
      ziel_saetze: int
      ziel_rpe: int
      volumen_stufe: str
      recovery_modifier: str
    """
    s_low, s_high, rpe_low, rpe_high = _LEVEL_RANGES[level]
    modifier = _recovery_modifier(klient)

    faktor = _WOCHE_FAKTOR[woche_typ]
    raw_saetze = s_low + (s_high - s_low) * faktor
    raw_rpe    = rpe_low + (rpe_high - rpe_low) * faktor

    if modifier == "reduziert":
        raw_saetze *= 0.8
        raw_rpe = min(raw_rpe, 8)
    elif modifier == "erhoht":
        raw_saetze *= 1.1

    saetze = max(1, round(raw_saetze))
    rpe    = max(4, min(10, round(raw_rpe)))

    if woche_typ == "akkumulation":
        stufe = "niedrig"
    elif woche_typ == "progression":
        stufe = "mittel"
    else:  # intensivierung + peak
        stufe = "hoch"

    if modifier == "reduziert":
        stufe = "niedrig" if stufe == "mittel" else "sehr_niedrig" if stufe == "niedrig" else stufe

    return {
        "ziel_saetze":       saetze,
        "ziel_rpe":          rpe,
        "volumen_stufe":     stufe,
        "recovery_modifier": modifier,
    }
