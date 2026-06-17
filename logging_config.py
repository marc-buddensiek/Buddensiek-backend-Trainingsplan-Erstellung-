"""
Zentrales Logging-Fundament für das Buddensiek Performance Backend.

KONVENTION — so loggt JEDES Modul in diesem System (auch neue: Mobility, Ausdauer, …):
  - Oben im Modul:   ``log = logging.getLogger(__name__)``  (nie ``print()`` im Produktivcode)
  - ``setup_logging()`` wird EINMAL beim Start aufgerufen — in ``main.py`` vor ``app = FastAPI``,
    in Skripten (``scripts/``) am Anfang von ``main()``. So haben Module auch OHNE ``main``
    konfiguriertes Logging.
  - ``vorgang_id`` (Correlation-ID) wo vorhanden in jede Logzeile mitführen, damit ein
    Async-Vorgang über den ganzen Pfad zusammen-filterbar ist (Präfix
    ``[vorgang=… client=…]``, s. ``main._log_prefix``).
  - NIE PII oder Gesundheitsdaten loggen: kein Name, Alter, Verletzungen, Stress/Schlaf,
    Motivation, Prompt-Inhalte. Nur IDs (vorgang_id, client_id, plan_id) + fachliche Kennzahlen.

Bewusst PLAINTEXT (kein JSON/structlog) — Render erfasst Konsolen-Logs automatisch (StreamHandler
auf stdout, KEIN FileHandler). Ein späterer Wechsel auf JSON / gehosteten Log-Dienst ist ein
Formatter-Tausch an genau DIESER Stelle (s. BACKLOG).
"""
from __future__ import annotations

import logging.config

# Modulname (%(name)s) MUSS in jeder Zeile stehen — bei vielen Modulen sonst nicht zuordenbar.
_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def setup_logging(level: str = "INFO") -> None:
    """Richtet das zentrale Logging ein (idempotent — Mehrfachaufruf ist ein No-op).

    Konsole/StreamHandler auf stdout, Plaintext mit Modulname. Aufrufbar von ``main`` UND
    von Skripten in ``scripts/``."""
    global _configured
    if _configured:
        return
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": _LOG_FORMAT, "datefmt": _DATE_FORMAT},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {"level": level, "handlers": ["console"]},
    })
    _configured = True
