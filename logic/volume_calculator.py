"""
Level + Ziel + Wochen-Typ + Recovery → per-Tier Sätze + RPE

Volumen = Modell A (Session-Kapazität), intensitätsgeführt → Sätze ~flach:
  Tier-Satz-Caps (harte Obergrenze 4): compound 3-4, accessory/isolation/core 2-3.
  Sätze bleiben über W1–W3 auf/nahe Cap-Unterkante (nur Intensivierung +1);
  Deload = Cap-Unterkante. Die Progression läuft über die RPE, NICHT das Volumen.

Session-Budget (Kraft): (Dauer − Warmup 10 − Finisher) ÷ 2 Min/Satz;
  Finisher = 8 Min bei Recomp, sonst 0. Conditioning läuft separat über _METABOLIC_CONFIG.

RPE-Welle (ankert unten, rampt über die volle Spanne — float, 0.5-Raster):
  Akku = rpe_low · Progression = Mitte · Intensivierung = rpe_high
  Deload = rpe_low − 1 (eine Stufe unter der leichtesten Ladewoche), Floor 4.

Recovery (nur RPE, NIE Volumen) — Deckel auf die Wellen-Basis, schlechtester Fall gewinnt:
  Stress ≥9 ODER Schlaf ≤4h → Basis-RPE gedeckelt auf rpe_low − 1
  Stress ≥8 ODER Schlaf ≤5h → Basis-RPE gedeckelt auf rpe_low
  Stress <5 UND Schlaf ≥7h  → Basis-RPE freigegeben bis rpe_high (nie darüber)
  sonst                      → keine Anpassung
  RPE-Boden: nie < 4. Deload ignoriert Recovery (rpe_low − 1 greift direkt).
"""

from __future__ import annotations
from typing import Literal
from models import KlientenInput, Hauptziel


WocheTyp = Literal["akkumulation", "progression", "intensivierung", "deload"]

# Volumen-Ramp (nur _tier_saetze; die RPE-Welle ankert separat in _wave_rpe).
# Deload nutzt die Cap-Unterkante direkt → kein deload-Eintrag (Prozent-Faktor war tot).
_PERIODISIERUNG_FAKTOR: dict[str, float] = {
    "akkumulation":   0.70,
    "progression":    0.85,
    "intensivierung": 1.00,
}

_TIER_CAP: dict[str, tuple[int, int]] = {   # Satz-Cap je Tier, harte Obergrenze 4
    "compound":  (3, 4),
    "accessory": (2, 3),
    "isolation": (2, 3),
    "core":      (2, 3),
}

# Kapazitäts-Konstanten (Spec Thema 3, Zeit-Parameter) — Single Source of Truth,
# auch von plan_assembler konsumiert (Naht 2).
WARMUP_MIN          = 10
FINISHER_MIN_RECOMP = 8
ZEIT_PRO_SATZ_KRAFT = 2.0
ZEIT_PRO_SATZ_COND  = 1.5


def finisher_min(ziel: Hauptziel) -> int:
    return FINISHER_MIN_RECOMP if ziel == Hauptziel.recomp else 0


def tier_floor(tier: str) -> int:
    return _TIER_CAP[tier][0]   # Cap-Unterkante je Tier — Trim-Floor in Naht 2b

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


def _wave_rpe(woche_typ: WocheTyp, rpe_low: int, rpe_high: int) -> float:
    # Welle ankert unten, rampt über die volle Spanne (Intensität vor Volumen):
    #   Akku = rpe_low · Progression = Mitte · Intensivierung = rpe_high
    if woche_typ == "akkumulation":
        return float(rpe_low)
    if woche_typ == "progression":
        return (rpe_low + rpe_high) / 2
    return float(rpe_high)   # intensivierung


def _tier_saetze(tier: str, woche_typ: WocheTyp) -> int:
    # Welle rampt in der Cap-Range; Deload = Cap-Unterkante (kein Prozent-Faktor)
    cap_low, cap_high = _TIER_CAP[tier]
    if woche_typ == "deload":
        return cap_low
    periodo = _PERIODISIERUNG_FAKTOR[woche_typ]
    return min(cap_high, int(cap_low + (cap_high - cap_low) * periodo))


def berechne_volumen(
    klient: KlientenInput,
    level: int,
    woche_typ: WocheTyp,
) -> dict:
    """
    Returns dict with:
      compound_saetze, accessory_saetze, isolation_saetze, core_saetze: int (Tier-Caps 2–4)
      ziel_saetze: int (= compound_saetze, Haupt-Compound der Session)
      ziel_rpe, compound_rpe, accessory_rpe, isolation_rpe: float (0.5-Raster)
      volumen_stufe: str
      recovery_modifier: str
    """
    rpe_low, rpe_high = _RPE_RANGES[level]
    lage = _recovery_lage(klient)

    # ── Volumen: Modell A — Sätze aus Tier-Caps, intensitätsgeführt (~flach) ──
    compound_saetze  = _tier_saetze("compound", woche_typ)
    accessory_saetze = _tier_saetze("accessory", woche_typ)
    isolation_saetze = _tier_saetze("isolation", woche_typ)
    core_saetze      = _tier_saetze("core", woche_typ)

    # ── RPE: Welle ankert unten → rampt auf rpe_high; Recovery deckelt (Thema 1/5) ──
    if woche_typ == "deload":
        raw_rpe = max(4.0, rpe_low - 1)   # eine Stufe unter leichtester Ladewoche; Recovery wirkt nicht
    else:
        base    = _wave_rpe(woche_typ, rpe_low, rpe_high)
        raw_rpe = _recovery_rpe(lage, base, rpe_low, rpe_high)
    ziel_rpe = max(4.0, min(10.0, round(raw_rpe * 2) / 2))   # 0.5-Raster, float in [4,10]

    # ── Volumen-Stufe (Wellen-Label, unverändert) ──
    if woche_typ == "deload":
        stufe = "sehr_niedrig"
    elif woche_typ == "akkumulation":
        stufe = "niedrig"
    elif woche_typ == "progression":
        stufe = "mittel"
    else:
        stufe = "hoch"

    return {
        "compound_saetze":  compound_saetze,
        "accessory_saetze": accessory_saetze,
        "isolation_saetze": isolation_saetze,
        "core_saetze":      core_saetze,
        "ziel_saetze":      compound_saetze,
        "ziel_rpe":         ziel_rpe,
        "compound_rpe":     ziel_rpe,
        "accessory_rpe":    max(4.0, ziel_rpe - 1),
        "isolation_rpe":    max(4.0, ziel_rpe - 2),
        "volumen_stufe":    stufe,
        "recovery_modifier": lage,
    }
