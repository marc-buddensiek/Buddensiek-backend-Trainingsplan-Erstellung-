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
