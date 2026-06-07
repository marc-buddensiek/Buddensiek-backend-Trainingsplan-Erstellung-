"""
PST-Punkte → Level 1–4

Scoring-Tabelle aus Buddensiek_KI_Trainingsplan_Uebersicht.pdf Seite 7:
  Kniebeugen: <30=1, 30-50=2, 51-70=3, 71+=4
  Push-Ups:   <15=1, 15-30=2, 31-50=3, 51+=4
  Sit-Ups:    <30=1, 30-50=2, 51-70=3, 71+=4
  Burpees:    <15=1, 15-25=2, 26-35=3, 36+=4
  Plank (s):  <60=1, 60-120=2, 121-180=3, 181+=4

Level-Schwellenwerte: 5-8=1, 9-13=2, 14-17=3, 18-20=4
Trainingsjahre-Cap: keine→1, unter_1→2, ein_bis_zwei→3, drei_bis_fuenf→4, fuenf_plus→4
"""

from __future__ import annotations
from models import KlientenInput, Trainingsjahre


def _kniebeugen_punkte(wdh: int) -> int:
    if wdh < 30:  return 1
    if wdh <= 50: return 2
    if wdh <= 70: return 3
    return 4


def _pushups_punkte(wdh: int) -> int:
    if wdh < 15:  return 1
    if wdh <= 30: return 2
    if wdh <= 50: return 3
    return 4


def _situps_punkte(wdh: int) -> int:
    if wdh < 30:  return 1
    if wdh <= 50: return 2
    if wdh <= 70: return 3
    return 4


def _burpees_punkte(wdh: int) -> int:
    if wdh < 15:  return 1
    if wdh <= 25: return 2
    if wdh <= 35: return 3
    return 4


def _plank_punkte(sek: int) -> int:
    if sek < 60:   return 1
    if sek <= 120: return 2
    if sek <= 180: return 3
    return 4


_JAHRES_CAP = {
    Trainingsjahre.keine:          1,
    Trainingsjahre.unter_1:        2,
    Trainingsjahre.ein_bis_zwei:   3,
    Trainingsjahre.drei_bis_fuenf: 4,
    Trainingsjahre.fuenf_plus:     4,
}


def berechne_pst_punkte(klient: KlientenInput) -> dict[str, int]:
    return {
        "kniebeugen": _kniebeugen_punkte(klient.kniebeugen_wdh),
        "pushups":    _pushups_punkte(klient.pushups_wdh),
        "situps":     _situps_punkte(klient.situps_wdh),
        "burpees":    _burpees_punkte(klient.burpees_wdh),
        "plank":      _plank_punkte(klient.plank_sek),
    }


def berechne_level(klient: KlientenInput) -> tuple[int, dict[str, int]]:
    """
    Returns (level, pst_punkte_dict).
    Level is capped by Trainingsjahre.
    """
    punkte = berechne_pst_punkte(klient)
    gesamt = sum(punkte.values())

    if gesamt <= 8:   raw_level = 1
    elif gesamt <= 13: raw_level = 2
    elif gesamt <= 17: raw_level = 3
    else:              raw_level = 4

    cap = _JAHRES_CAP[klient.trainingsjahre]
    level = min(raw_level, cap)
    return level, punkte
