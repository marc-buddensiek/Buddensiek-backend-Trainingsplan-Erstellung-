"""
Realismus-Prüfung: Wöchentliche Trainingszeit vs. Ziel-Mindestanforderungen.

pruefe_realismus() gibt None zurück wenn alles passt,
oder ein dict {"typ": "warnung"|"hinweis", "nachricht": str}.
"""

from __future__ import annotations
from models import Hauptziel


# (warnung_schwelle_min, hinweis_schwelle_min) — wöchentliche Trainingsminuten
_SCHWELLEN: dict[Hauptziel, tuple[int, int]] = {
    Hauptziel.muskelaufbau: (120, 180),
    Hauptziel.fettabbau:    (90,  150),
    Hauptziel.recomp:       (150, 210),
    Hauptziel.ausdauer:     (90,  150),
    Hauptziel.gesundheit:   (60,  120),
}

_WARNUNGEN: dict[Hauptziel, str] = {
    Hauptziel.muskelaufbau: (
        "Für Muskelaufbau empfehlen wir mindestens 3× pro Woche à 45 Min. "
        "Mit dem aktuellen Volumen ({wmin} Min./Woche) sind die Fortschritte sehr begrenzt."
    ),
    Hauptziel.fettabbau: (
        "Für nachhaltigen Fettabbau sind mindestens 3× pro Woche à 30 Min. nötig. "
        "Das aktuelle Volumen ({wmin} Min./Woche) reicht kaum für spürbare Veränderungen."
    ),
    Hauptziel.recomp: (
        "Body Recomposition ist das anspruchsvollste Ziel — es braucht mindestens 3× à 45 Min. pro Woche. "
        "Mit {wmin} Min./Woche ist der Fortschritt sehr langsam."
    ),
    Hauptziel.ausdauer: (
        "Ausdaueraufbau erfordert mindestens 3 Einheiten pro Woche. "
        "Mit {wmin} Min./Woche ist ein messbarer Ausdauereffekt kaum zu erwarten."
    ),
    Hauptziel.gesundheit: (
        "Für allgemeine Gesundheitsverbesserung empfehlen die WHO mindestens 150 Min. moderate Aktivität pro Woche. "
        "Das aktuelle Volumen ({wmin} Min./Woche) liegt darunter."
    ),
}

_HINWEISE: dict[Hauptziel, str] = {
    Hauptziel.muskelaufbau: (
        "Mit {wmin} Min./Woche ist Muskelaufbau möglich, aber langsam. "
        "Für deutlich bessere Ergebnisse: mehr Tage oder längere Einheiten einplanen."
    ),
    Hauptziel.fettabbau: (
        "Das aktuelle Volumen ({wmin} Min./Woche) unterstützt Fettabbau — kombiniere es mit angepasster Ernährung "
        "für spürbare Ergebnisse."
    ),
    Hauptziel.recomp: (
        "Recomp mit {wmin} Min./Woche ist möglich, aber dauert länger. "
        "Ernährung (Protein!) ist hier genauso entscheidend wie das Training."
    ),
    Hauptziel.ausdauer: (
        "{wmin} Min./Woche reicht für Einstieg und Gesundheitserhalt. "
        "Für merkliche Ausdauerverbesserungen mittelfristig auf 150+ Min./Woche steigern."
    ),
    Hauptziel.gesundheit: (
        "{wmin} Min./Woche ist ein solider Start. "
        "Für maximalen Gesundheitsnutzen schrittweise auf 3 Einheiten à 45 Min. steigern."
    ),
}


def pruefe_realismus(
    ziel: Hauptziel,
    tage: int,
    session_dauer_min: int,
) -> dict | None:
    wochenmins = tage * session_dauer_min
    warnung_schwelle, hinweis_schwelle = _SCHWELLEN[ziel]

    if wochenmins < warnung_schwelle:
        return {
            "typ": "warnung",
            "nachricht": _WARNUNGEN[ziel].format(wmin=wochenmins),
        }
    if wochenmins < hinweis_schwelle:
        return {
            "typ": "hinweis",
            "nachricht": _HINWEISE[ziel].format(wmin=wochenmins),
        }
    return None
