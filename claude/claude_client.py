"""
Claude-Aufruf via Anthropic API.

Erwartet Umgebungsvariable ANTHROPIC_API_KEY.
JSON-Fences werden automatisch entfernt falls Claude sie trotzdem setzt.
"""

from __future__ import annotations
import json
import logging
import os
import re
import time

import anthropic

from claude.prompt_template import SYSTEM_PROMPT, build_user_prompt
from models import KlientenInput, ClaudeOutput

log = logging.getLogger(__name__)


# Aktueller Sonnet — richtige Wahl für den Auswahl-Task (gefilterter Pool, kein High-End-Reasoning
# nötig), kosteneffizient pro Aufruf. Versionierter String bewusst (kein Alias) → keine stille
# Modell-Drift. Einzige Wahrheit (nur hier konsumiert, :model unten).
_MODEL = "claude-sonnet-4-6"


def _strip_fences(text: str) -> str:
    return re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text, flags=re.MULTILINE).strip()


def generiere_uebungsauswahl(
    klient: KlientenInput,
    level: int,
    split_typ: str,
    block_nummer: int,
    sessions: list[dict],
    uebungen_gefiltert: dict[str, list[dict]],
    woche_typ: str,
    ziel_saetze: int,
    ziel_rpe: float,
    vorgang_id: str = "-",
) -> ClaudeOutput:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    user_prompt = build_user_prompt(
        klient=klient,
        level=level,
        split_typ=split_typ,
        block_nummer=block_nummer,
        sessions=sessions,
        uebungen_gefiltert=uebungen_gefiltert,
        woche_typ=woche_typ,
        ziel_saetze=ziel_saetze,
        ziel_rpe=ziel_rpe,
    )

    log.info(f"[vorgang={vorgang_id}] Claude-Aufruf — Modell {_MODEL}, {len(sessions)} Sessions")
    t0 = time.monotonic()
    try:
        response = client.messages.create(
            model=_MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = response.content[0].text
        clean = _strip_fences(raw)
        result = ClaudeOutput(**json.loads(clean))
    except Exception as e:
        # NUR Fehlertyp + Message — NIE Prompt-Inhalt/Klient-Daten ins Log (GDPR).
        log.error(f"[vorgang={vorgang_id}] Claude-Fehler nach {time.monotonic() - t0:.1f}s: "
                  f"{type(e).__name__}: {e}")
        raise

    usage = getattr(response, "usage", None)
    tok = f", Tokens in/out {usage.input_tokens}/{usage.output_tokens}" if usage else ""
    log.info(f"[vorgang={vorgang_id}] Claude-Antwort — {time.monotonic() - t0:.1f}s, "
             f"{len(result.sessions)} Sessions{tok}")
    return result
