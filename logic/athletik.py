"""
Longevity-Athletik (MVP-7 Naht 5) — Spec Thema 4.

Getrennter Pfad vom Conditioning (Fettabbau/Recomp): Athletik-Tage gehören zu Longevity
und rotieren mit den Zone-2-Cardio-Tagen (1 Tag/Woche alternierend, 2 Tage/Woche 1× Z2 +
1× Athletik).

Athletik-Übungen behalten ihr Kraft-Pattern (squat/single_leg/core/push_horizontal) und
tragen `"athletik" ∈ pattern_tags` (analog zum Conditioning-Hybrid mit `conditioning_friendly`).
Dosierung läuft über `skill_level` (explosive Plyos = wenige Wdh, submaximale Athletik = mehr),
Athletik trägt KEINE RPE (CNS/Qualität, wie Conditioning).
"""
from __future__ import annotations

# DQ2 (Naht 5-2): Sätze je skill_level — explosive Plyos (hoch) wenige Sätze, submaximale Athletik (niedrig) mehr.
_ATHLETIK_SAETZE = {1: 4, 2: 4, 3: 3, 4: 2}
# DQ5: Deload reduziert das Volumen pauschal (~⅔, im 60–70%-Band) — Kraft deloadet auf die Cap-Unterkante,
# Athletik analog pauschal runter (keine spezielle Übungs-Streichung).
_ATHLETIK_DELOAD_FAKTOR = 0.67


def athletik_dosierung(skill_level: int, deload: bool = False) -> tuple[int, int, int]:
    """Sätze, Wdh, Pause(Sek) für eine Athletik-Übung (Naht 5-2, DQ2) — skill-gestaffelt:
    `Wdh = 20 − skill·4` (L1=16 · L2=12 · L3=8 · L4=4), Sätze 4/4/3/2, Pause ~120 s, KEINE RPE
    (Quality over fatigue). Im Deload Volumen pauschal runter (~⅔, DQ5)."""
    wdh = 20 - skill_level * 4
    saetze = _ATHLETIK_SAETZE.get(skill_level, 3)
    if deload:
        saetze = max(1, round(saetze * _ATHLETIK_DELOAD_FAKTOR))
    return saetze, wdh, 120


def athletik_pool(uebungen_gefiltert: dict[str, list[dict]]) -> list[dict]:
    """ÜBUNGS-Pool für Longevity-Athletik-Tage (MVP-7 Naht 5): alle Übungen mit
    `"athletik" ∈ pattern_tags` aus den schon equipment-/skill-gefilterten Pattern-Buckets.
    Dedup nach id, Reihenfolge des ersten Auftretens erhalten. Equipment-/Level-Filterung
    greift automatisch (der Pool wird aus `filtere_uebungen` gespeist), getrennt vom
    Conditioning-Pool. Naht 5-1: Helfer existiert, ist aber noch NICHT verdrahtet (5-2/5-3)."""
    pool: dict[str, dict] = {}
    for exs in uebungen_gefiltert.values():
        for ex in exs:
            if "athletik" in ex.get("pattern_tags", []):
                pool.setdefault(ex["id"], ex)
    return list(pool.values())
