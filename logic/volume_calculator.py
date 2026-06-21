"""
Level + Ziel + Wochen-Typ + Recovery → per-Tier Sätze + RPE

Volumen = Modell A v2 (Befund 3) — additive Satz-Regel pro Slot, ziel- + level- + wochen-abhängig:
  saetze = clamp(BASIS[ziel][tier] + LEVEL_OFFSET[level] (nur acc/iso) + RAMPE[ziel][woche],
                 BODEN[tier], DECKE[ziel][tier]).
  Mike-Rampe: muskelaufbau/recomp steigern über W1→W3 und deloaden in W4 über das Volumen;
  fettabbau/longevity bleiben flach (Deload dort nur über die RPE). RPE-Welle separat (s.u.).

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

# Volumen-Korridore (Modell A v2, Befund 3): additive Satz-Regel pro Slot —
# saetze = clamp(BASIS[ziel][tier] + LEVEL_OFFSET[level](nur acc/iso) + RAMPE[ziel][woche], BODEN, DECKE)
_BASIS: dict[str, dict[str, int]] = {
    "muskelaufbau": {"compound": 3, "accessory": 3, "isolation": 3, "core": 2},
    "fettabbau":    {"compound": 3, "accessory": 2, "isolation": 2, "core": 2},
    "recomp":       {"compound": 3, "accessory": 3, "isolation": 2, "core": 2},
    "longevity":    {"compound": 2, "accessory": 2, "isolation": 2, "core": 2},
}
_LEVEL_OFFSET: dict[int, int] = {1: -1, 2: 0, 3: 0, 4: 1}   # nur accessory + isolation
_RAMPE: dict[str, list[int]] = {   # W1 Akku · W2 Prog · W3 Int · W4 Deload
    "muskelaufbau": [0, 1, 2, -2],
    "recomp":       [0, 0, 1, -1],
    "fettabbau":    [0, 0, 0, 0],
    "longevity":    [0, 0, 0, 0],
}
_BODEN: dict[str, int] = {"compound": 2, "accessory": 2, "isolation": 2, "core": 1}
_WOCHE_IDX = {"akkumulation": 0, "progression": 1, "intensivierung": 2, "deload": 3}


def _decke(ziel: str, tier: str) -> int:
    if tier == "compound": return 4
    if tier == "core":     return 3
    return 5 if ziel == "muskelaufbau" else 4   # accessory/isolation

# Kapazitäts-Konstanten (Spec Thema 3, Zeit-Parameter) — Single Source of Truth,
# auch von plan_assembler konsumiert (Naht 2).
WARMUP_MIN          = 10
FINISHER_MIN_RECOMP = 8
ZEIT_PRO_SATZ_KRAFT = 2.0


def finisher_min(ziel: Hauptziel) -> int:
    return FINISHER_MIN_RECOMP if ziel == Hauptziel.recomp else 0


def tier_floor(tier: str) -> int:
    return _BODEN[tier]   # Korridor-Boden je Tier — Trim-Floor (Modell A v2)

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


def rir_hinweis(level: int, rpe: float) -> str | None:
    """RIR-Klartext für Level-1-Einsteiger (RPE ist für sie noch abstrakt).
    RIR = 10 − RPE. Halb-RPE → Spanne (z.B. RPE 6.5 → '3-4'). Level ≥ 2: None."""
    if level != 1:
        return None
    rir = 10 - rpe
    if rir <= 0:
        return "bis nahe ans Maximum (kaum Reserve)"
    if rir == int(rir):
        return f"noch ~{int(rir)} Wiederholungen in Reserve"
    return f"noch ~{int(rir)}-{int(rir) + 1} Wiederholungen in Reserve"


def _wave_rpe(woche_typ: WocheTyp, rpe_low: int, rpe_high: int) -> float:
    # Welle ankert unten, rampt über die volle Spanne (Intensität vor Volumen):
    #   Akku = rpe_low · Progression = Mitte · Intensivierung = rpe_high
    if woche_typ == "akkumulation":
        return float(rpe_low)
    if woche_typ == "progression":
        return (rpe_low + rpe_high) / 2
    return float(rpe_high)   # intensivierung


def _tier_saetze(ziel: str, level: int, tier: str, woche_typ: WocheTyp) -> int:
    # additive Korridor-Regel: Basis(ziel) + Level-Offset(nur acc/iso) + Rampe(ziel,woche),
    # geklemmt in [Boden, Decke]. Mike-Rampe steigert muskel/recomp, deloadet via −Rampe.
    offset = _LEVEL_OFFSET[level] if tier in ("accessory", "isolation") else 0
    rampe  = _RAMPE[ziel][_WOCHE_IDX[woche_typ]]
    return max(_BODEN[tier], min(_decke(ziel, tier), _BASIS[ziel][tier] + offset + rampe))


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

    # ── Volumen: Modell A v2 — additive Korridor-Regel (ziel × level × woche), Befund 3 ──
    ziel = klient.hauptziel.value
    compound_saetze  = _tier_saetze(ziel, level, "compound", woche_typ)
    accessory_saetze = _tier_saetze(ziel, level, "accessory", woche_typ)
    isolation_saetze = _tier_saetze(ziel, level, "isolation", woche_typ)
    core_saetze      = _tier_saetze(ziel, level, "core", woche_typ)

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
