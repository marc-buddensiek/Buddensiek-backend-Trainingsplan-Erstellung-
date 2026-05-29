"""
Claude-Aufruf via Anthropic API.

Erwartet Umgebungsvariable ANTHROPIC_API_KEY.
JSON-Fences werden automatisch entfernt falls Claude sie trotzdem setzt.
"""

from __future__ import annotations
import json
import os
import re

import anthropic

from claude.prompt_template import SYSTEM_PROMPT, build_user_prompt
from models import KlientenInput, ClaudeOutput


_MODEL = "claude-sonnet-4-5"


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
    ziel_rpe: int,
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
    return ClaudeOutput(**json.loads(clean))
