"""
Claude-Aufruf via OpenRouter (OpenAI-kompatibler Endpoint).

Erwartet Umgebungsvariable OPENROUTER_API_KEY.
JSON-Fences werden automatisch entfernt falls Claude sie trotzdem setzt.
"""

from __future__ import annotations
import json
import os
import re

import openai

from claude.prompt_template import SYSTEM_PROMPT, build_user_prompt
from models import KlientenInput, ClaudeOutput


_MODEL = "anthropic/claude-sonnet-4-5"


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
    """
    Ruft Claude auf und gibt einen validierten ClaudeOutput zurück.
    Raises: openai.APIError, json.JSONDecodeError, pydantic.ValidationError
    """
    api_key = os.environ["OPENROUTER_API_KEY"]
    client = openai.OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

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

    response = client.chat.completions.create(
        model=_MODEL,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = response.content[0].text if hasattr(response, "content") else response.choices[0].message.content
    clean = _strip_fences(raw)
    return ClaudeOutput(**json.loads(clean))
