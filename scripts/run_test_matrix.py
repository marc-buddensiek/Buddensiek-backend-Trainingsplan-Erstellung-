"""
Test-Matrix — Profil-Konstruktion + TROCKENVALIDIERUNG (kein Claude-Call, keine Plan-Generierung).

Baut aus kompakten Case-Dicts vollständige Typeform-Webhook-Payloads (Format wie
data/fake_typeform.json) und prüft NUR, dass jedes Profil sauber parst und das
intendierte Level/Equipment erzeugt. Erzeugt KEINEN Plan und ruft KEINE API.

  python3 scripts/run_test_matrix.py

Output: data/test_profiles/caseNN_<kurzname>.json (gitignored) + Validierungs-Tabelle.
"""
from __future__ import annotations

import json
import pathlib
import sys
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from parsers import parse_typeform_payload
from logic.level_calculator import berechne_level

_OUT_DIR = pathlib.Path(__file__).parent.parent / "data" / "test_profiles"


# ── Payload-Builder ─────────────────────────────────────────────────────────────
# Antwort-Typen/refs exakt wie data/fake_typeform.json. Der Parser liest field.ref +
# den typ-spezifischen Wert; hauptziel/equipment/trainingsjahre via choice.ref,
# tage/dauer/schlaf via choice.label, verletzungen via choices.labels.

def _f(ref: str, typ: str = "multiple_choice") -> dict:
    return {"id": ref, "ref": ref, "type": typ}

def _text(ref, text):       return {"type": "text",   "text": text,     "field": _f(ref, "short_text")}
def _num(ref, num):         return {"type": "number", "number": num,    "field": _f(ref, "number")}
def _choice_ref(ref, cref): return {"type": "choice", "choice": {"id": cref, "ref": cref, "label": cref}, "field": _f(ref)}
def _choice_label(ref, lab):return {"type": "choice", "choice": {"id": f"uuid-{lab}", "ref": f"uuid-{lab}", "label": str(lab)}, "field": _f(ref)}
def _choices(ref, labels):  return {"type": "choices", "choices": {"ids": [], "labels": labels, "refs": []}, "field": _f(ref)}


def baue_payload(case: dict) -> dict:
    """Kompaktes Case-Dict → vollständiger Typeform-Webhook-Payload (Format fake_typeform.json).

    stress_level/schlaf_stunden sind nicht in der Case-Tabelle → neutrale Defaults
    (4 / 7), da sie nur die RPE (Recovery) steuern, nicht das Level."""
    verletzungen = case.get("verletzungen") or ["keine"]   # leer → "keine" (Parser filtert es)
    answers = [
        _text("vorname", case.get("vorname", "Testklient")),
        _num("alter", case["alter"]),
        _choice_ref("hauptziel", case["hauptziel"]),
        _choice_label("tage_pro_woche", case["tage_pro_woche"]),
        _choice_label("session_dauer_min", case["session_dauer_min"]),
        _choice_ref("equipment", case["equipment"]),
        _choice_ref("trainingsjahre", case["trainingsjahre"]),
        _num("stress_level", case.get("stress_level", 4)),
        _choice_label("schlaf_stunden", case.get("schlaf_stunden", 7)),
        _choices("verletzungen", verletzungen),
        _num("kniebeugen_wdh", case["kniebeugen"]),
        _num("pushups_wdh", case["pushups"]),
        _num("situps_wdh", case["situps"]),
        _num("burpees_wdh", case["burpees"]),
        _num("plank_sek", case["plank_sek"]),
    ]
    return {
        "event_id": uuid.uuid4().hex,
        "event_type": "form_response",
        "form_response": {
            "form_id": "TESTMATRIX",
            "token": uuid.uuid4().hex,
            "hidden": {"client_id": str(uuid.uuid4())},
            "answers": answers,
        },
    }


# ── Die 12 Cases (PST bereits auf die Ziel-Level kalibriert) ────────────────────
CASES = [
    {"nr": "01", "kurzname": "bodyweight_l2",       "equipment": "bodyweight", "trainingsjahre": "ein_bis_zwei",   "kniebeugen": 40, "pushups": 20, "situps": 40, "burpees": 20, "plank_sek": 90,  "erwartetes_level": 2, "hauptziel": "muskelaufbau", "tage_pro_woche": 3, "session_dauer_min": 45, "alter": 30, "verletzungen": []},
    {"nr": "02", "kurzname": "travel_l2",           "equipment": "travel",     "trainingsjahre": "ein_bis_zwei",   "kniebeugen": 40, "pushups": 20, "situps": 40, "burpees": 20, "plank_sek": 90,  "erwartetes_level": 2, "hauptziel": "fettabbau",    "tage_pro_woche": 4, "session_dauer_min": 30, "alter": 30, "verletzungen": []},
    {"nr": "03", "kurzname": "kettlebell_l3_knie",  "equipment": "kettlebell", "trainingsjahre": "drei_bis_fuenf", "kniebeugen": 60, "pushups": 40, "situps": 60, "burpees": 30, "plank_sek": 150, "erwartetes_level": 3, "hauptziel": "fettabbau",    "tage_pro_woche": 5, "session_dauer_min": 60, "alter": 35, "verletzungen": ["knie"]},
    {"nr": "04", "kurzname": "homegym_l2",          "equipment": "home_gym",   "trainingsjahre": "ein_bis_zwei",   "kniebeugen": 40, "pushups": 20, "situps": 40, "burpees": 20, "plank_sek": 90,  "erwartetes_level": 2, "hauptziel": "muskelaufbau", "tage_pro_woche": 4, "session_dauer_min": 60, "alter": 30, "verletzungen": []},
    {"nr": "05", "kurzname": "hybrid_l3",           "equipment": "hybrid",     "trainingsjahre": "drei_bis_fuenf", "kniebeugen": 60, "pushups": 40, "situps": 60, "burpees": 30, "plank_sek": 150, "erwartetes_level": 3, "hauptziel": "recomp",       "tage_pro_woche": 4, "session_dauer_min": 60, "alter": 32, "verletzungen": []},
    {"nr": "06", "kurzname": "gym_l4",              "equipment": "gym",        "trainingsjahre": "drei_bis_fuenf", "kniebeugen": 75, "pushups": 55, "situps": 75, "burpees": 40, "plank_sek": 200, "erwartetes_level": 4, "hauptziel": "muskelaufbau", "tage_pro_woche": 5, "session_dauer_min": 60, "alter": 28, "verletzungen": []},
    {"nr": "07", "kurzname": "gym_l2_wirbel",       "equipment": "gym",        "trainingsjahre": "ein_bis_zwei",   "kniebeugen": 40, "pushups": 20, "situps": 40, "burpees": 20, "plank_sek": 90,  "erwartetes_level": 2, "hauptziel": "muskelaufbau", "tage_pro_woche": 4, "session_dauer_min": 60, "alter": 30, "verletzungen": ["wirbelsäule"]},
    {"nr": "08", "kurzname": "kettlebell_l2_multi", "equipment": "kettlebell", "trainingsjahre": "ein_bis_zwei",   "kniebeugen": 40, "pushups": 20, "situps": 40, "burpees": 20, "plank_sek": 90,  "erwartetes_level": 2, "hauptziel": "fettabbau",    "tage_pro_woche": 4, "session_dauer_min": 60, "alter": 38, "verletzungen": ["wirbelsäule", "knie"]},
    {"nr": "09", "kurzname": "gym_l2_6tage",        "equipment": "gym",        "trainingsjahre": "ein_bis_zwei",   "kniebeugen": 40, "pushups": 20, "situps": 40, "burpees": 20, "plank_sek": 90,  "erwartetes_level": 2, "hauptziel": "muskelaufbau", "tage_pro_woche": 6, "session_dauer_min": 60, "alter": 30, "verletzungen": []},
    {"nr": "10", "kurzname": "gym_l1_kurz",         "equipment": "gym",        "trainingsjahre": "unter_1",        "kniebeugen": 20, "pushups": 10, "situps": 20, "burpees": 5,  "plank_sek": 30,  "erwartetes_level": 1, "hauptziel": "recomp",       "tage_pro_woche": 3, "session_dauer_min": 30, "alter": 30, "verletzungen": []},
    {"nr": "11", "kurzname": "gym_l2_longevity",    "equipment": "gym",        "trainingsjahre": "ein_bis_zwei",   "kniebeugen": 40, "pushups": 20, "situps": 40, "burpees": 20, "plank_sek": 90,  "erwartetes_level": 2, "hauptziel": "longevity",    "tage_pro_woche": 4, "session_dauer_min": 60, "alter": 55, "verletzungen": []},
    {"nr": "12", "kurzname": "bodyweight_l1_short", "equipment": "bodyweight", "trainingsjahre": "unter_1",        "kniebeugen": 20, "pushups": 10, "situps": 20, "burpees": 5,  "plank_sek": 30,  "erwartetes_level": 1, "hauptziel": "muskelaufbau", "tage_pro_woche": 4, "session_dauer_min": 20, "alter": 30, "verletzungen": []},
]


def main() -> None:
    _OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Test-Matrix Trockenvalidierung — {len(CASES)} Cases (kein Claude-Call)\n")
    header = f"{'Case':<22} {'erw':>3} {'ber':>3} {'equipment':<11} {'ziel':<12} {'tg':>2} {'dau':>3} {'verletzungen':<22} {'Status'}"
    print(header); print("-" * len(header))

    fehler = 0
    for c in CASES:
        name = f"{c['nr']}_{c['kurzname']}"
        payload = baue_payload(c)
        (_OUT_DIR / f"case{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        verl = ", ".join(c["verletzungen"]) or "—"
        try:
            klient = parse_typeform_payload(payload)
            level, _ = berechne_level(klient)
            ok = (level == c["erwartetes_level"]
                  and klient.equipment.value == c["equipment"]
                  and klient.hauptziel.value == c["hauptziel"]
                  and klient.tage_pro_woche == c["tage_pro_woche"]
                  and klient.session_dauer_min == c["session_dauer_min"])
            status = "OK" if ok else f"FEHLER (Level erw {c['erwartetes_level']} != ber {level})"
            if not ok:
                fehler += 1
            print(f"{name:<22} {c['erwartetes_level']:>3} {level:>3} {klient.equipment.value:<11} "
                  f"{klient.hauptziel.value:<12} {klient.tage_pro_woche:>2} {klient.session_dauer_min:>3} {verl:<22} {status}")
        except Exception as e:
            fehler += 1
            print(f"{name:<22} {c['erwartetes_level']:>3} {'—':>3} {c['equipment']:<11} "
                  f"{c['hauptziel']:<12} {c['tage_pro_woche']:>2} {c['session_dauer_min']:>3} {verl:<22} "
                  f"FEHLER ({type(e).__name__}: {e})")

    print("-" * len(header))
    print(f"\n{'Alle 12 Profile OK ✓' if fehler == 0 else f'{fehler} FEHLER'}  ·  Payloads: {_OUT_DIR}")


if __name__ == "__main__":
    main()
