"""
Level + Ziel + Wochen-Typ + Recovery → per-Tier Sätze + RPE

Wöchentliches Ziel-Volumen (Sätze pro Muskelgruppe):
  muskelaufbau: L1=(8,10),  L2=(12,16), L3=(16,20), L4=(18,22)
  fettabbau:    L1=(6,8),   L2=(10,14), L3=(14,18), L4=(16,20)
  recomp:       L1=(8,10),  L2=(12,16), L3=(16,20), L4=(18,22)
  longevity:    L1=(6,8),   L2=(8,10),  L3=(8,12),  L4=(10,12)   # TODO(longevity-volume): Platzhalter = alte gesundheit-Werte, final mit MVP-3 / Thema 4-6

Periodisierungs-Faktor:
  akkumulation=0.70, progression=0.85, intensivierung=1.00, deload=0.50

Slot-Tier-Multiplikator:
  compound=1.0, accessory=0.9, isolation=0.7, core=0.8

Frequenz (FREQ): tage ≤ 3 → FREQ=tage; tage ≥ 4 → FREQ=2 (Upper/Lower)

Recovery (nur RPE, NIE Volumen) — schlechtester Fall gewinnt:
  Stress ≥9 ODER Schlaf ≤4h → unteres Ende der RPE-Spanne − 1
  Stress ≥8 ODER Schlaf ≤5h → unteres Ende der RPE-Spanne
  Stress <5 UND Schlaf ≥7h  → oberes Ende der RPE-Spanne
  sonst                      → keine Anpassung
  RPE-Boden: nie < 4. Deload: RPE-Floor (rpe_low) greift, Recovery wirkt nicht.
"""

from __future__ import annotations
from typing import Literal
from models import KlientenInput, Hauptziel


WocheTyp = Literal["akkumulation", "progression", "intensivierung", "deload"]

_WOCHEN_VOLUMEN: dict[Hauptziel, dict[int, tuple[int, int]]] = {
    Hauptziel.muskelaufbau: {1: (8, 10),  2: (12, 16), 3: (16, 20), 4: (18, 22)},
    Hauptziel.fettabbau:    {1: (6, 8),   2: (10, 14), 3: (14, 18), 4: (16, 20)},
    Hauptziel.recomp:       {1: (8, 10),  2: (12, 16), 3: (16, 20), 4: (18, 22)},
    # TODO(longevity-volume): Platzhalter = alte gesundheit-Werte, final mit MVP-3 / Thema 4-6
    Hauptziel.longevity:    {1: (6, 8),   2: (8, 10),  3: (8, 12),  4: (10, 12)},
}

_PERIODISIERUNG_FAKTOR: dict[str, float] = {
    "akkumulation":   0.70,
    "progression":    0.85,
    "intensivierung": 1.00,
    "deload":         0.50,
}

_SLOT_TIER_MULTIPLIKATOR: dict[str, float] = {
    "compound":  1.0,
    "accessory": 0.9,
    "isolation": 0.7,
    "core":      0.8,
}

_RPE_RANGES: dict[int, tuple[int, int]] = {
    1: (6, 7),
    2: (7, 8),
    3: (7, 9),
    4: (7, 9),
}


def _recovery_lage(klient: KlientenInput) -> str:
    # Schlechtester zutreffender Fall gewinnt → schwerste Lage ZUERST:
    if klient.stress_level >= 9 or klient.schlaf_stunden <= 4:
        return "sehr_hoch"
    if klient.stress_level >= 8 or klient.schlaf_stunden <= 5:
        return "hoch"
    if klient.stress_level < 5 and klient.schlaf_stunden >= 7:
        return "gut"
    return "normal"


def _recovery_rpe(lage: str, wave_rpe: float, rpe_low: int, rpe_high: int) -> float:
    # Welle = Basis-RPE; Recovery = Deckel nach oben (schlecht) / Freigabe bis oberes Ende (gut)
    if lage == "sehr_hoch":
        rpe = min(wave_rpe, rpe_low - 1)   # unteres Ende − 1
    elif lage == "hoch":
        rpe = min(wave_rpe, rpe_low)        # unteres Ende
    elif lage == "gut":
        rpe = max(wave_rpe, rpe_high)       # oberes Ende
    else:
        rpe = wave_rpe                       # keine Anpassung
    return max(4, rpe)                       # RPE-Boden: nie < 4


def berechne_volumen(
    klient: KlientenInput,
    level: int,
    woche_typ: WocheTyp,
) -> dict:
    """
    Returns dict with:
      compound_saetze, accessory_saetze, isolation_saetze, core_saetze: int
      ziel_saetze: int (= compound_saetze, für Woche-Modell-Feld)
      ziel_rpe, compound_rpe, accessory_rpe, isolation_rpe: int
      volumen_stufe: str
      recovery_modifier: str
    """
    s_low, s_high = _WOCHEN_VOLUMEN[klient.hauptziel][level]
    rpe_low, rpe_high = _RPE_RANGES[level]
    lage = _recovery_lage(klient)
    periodo = _PERIODISIERUNG_FAKTOR[woche_typ]

    # Volumen ist recovery-unabhängig — Stress/Schlaf bewegen NUR die RPE (Spec Thema 5).
    # Deload = 50% des Intensivierungs-Volumens (nicht skaliert vom s_low)
    if woche_typ == "deload":
        intensiv_base = s_high
        base = intensiv_base * 0.5
        raw_rpe = float(rpe_low)  # Deload: RPE-Floor greift, Recovery wirkt nicht
    else:
        base = s_low + (s_high - s_low) * periodo
        wave_rpe = rpe_low + (rpe_high - rpe_low) * periodo
        raw_rpe = _recovery_rpe(lage, wave_rpe, rpe_low, rpe_high)

    # Upper/Lower-Splits (4+ Tage) trainieren jeden Muskel 2× pro Woche
    freq = 2 if klient.tage_pro_woche >= 4 else klient.tage_pro_woche

    def _sets(tier: str) -> int:
        return max(1, int(base * _SLOT_TIER_MULTIPLIKATOR[tier] / freq))

    ziel_rpe = max(4, min(10, round(raw_rpe)))

    if woche_typ == "deload":
        stufe = "sehr_niedrig"
    elif woche_typ == "akkumulation":
        stufe = "niedrig"
    elif woche_typ == "progression":
        stufe = "mittel"
    else:
        stufe = "hoch"

    compound_saetze = _sets("compound")
    return {
        "compound_saetze":  compound_saetze,
        "accessory_saetze": _sets("accessory"),
        "isolation_saetze": _sets("isolation"),
        "core_saetze":      _sets("core"),
        "ziel_saetze":      compound_saetze,
        "ziel_rpe":         ziel_rpe,
        "compound_rpe":     ziel_rpe,
        "accessory_rpe":    max(4, ziel_rpe - 1),
        "isolation_rpe":    max(4, ziel_rpe - 2),
        "volumen_stufe":    stufe,
        "recovery_modifier": lage,
    }
