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

# Robustheit (Naht 9-3a): Retry mit Backoff bei transienten/inhaltlichen Fehlern.
MAX_VERSUCHE = 3            # 1 Erstversuch + 2 Retries
BACKOFF_SEKUNDEN = [2, 5]   # Pause (Sek.) VOR Retry 1, VOR Retry 2


class UnvollstaendigerClaudeOutput(Exception):
    """Claude-Antwort deckt nicht alle erwarteten Sessions/Slots ab (SOLL aus `sessions`).
    Landet im selben Retry-Pfad wie API-/JSON-/Validierungs-Fehler."""


def _strip_fences(text: str) -> str:
    return re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text, flags=re.MULTILINE).strip()


def _pruefe_vollstaendigkeit(result: ClaudeOutput, sessions: list[dict]) -> None:
    """Wirft UnvollstaendigerClaudeOutput, wenn IST != SOLL — SOLL **nur über Kraft-Sessions**
    (Claude-gefüllt). Conditioning-/Athletik-Sessions (Slot-Marker `pool` ∈ {conditioning,
    athletik}) baut der Assembler deterministisch und werden hier NICHT gefordert. Die
    exercise_ids sind durch den ClaudeOutput-Modell-Validator bereits gültig — hier zählt nur
    die Anzahl. (Zone-2 trägt echte Kraft-Pattern ohne `pool` → bleibt korrekt in SOLL.)"""
    def _ist_kraft(s: dict) -> bool:
        return not any(slot.get("pool") for slot in s.get("slots", []))

    erwartete = {s["session_id"]: len(s.get("slots", [])) for s in sessions if _ist_kraft(s)}
    ist = {s.session_id: len(s.uebungen) for s in result.sessions}

    # Prüfung 1 (Subset): jede erwartete Kraft-Session muss vorhanden sein. Zusätzliche
    # IST-Sessions (z.B. Conditioning, die Claude trotzdem befüllt hat) sind KEIN Fehler.
    fehlend = set(erwartete) - set(ist)
    if fehlend:
        raise UnvollstaendigerClaudeOutput(f"Fehlende Kraft-Sessions: {sorted(fehlend)}")
    extra = set(ist) - set(erwartete)
    if extra:
        log.debug(f"Claude lieferte zusätzliche (nicht geforderte) Sessions: {sorted(extra)}")

    # Prüfung 2: Slot-Anzahl je erwarteter Kraft-Session (nur über SOLL iterieren).
    abweichungen = [
        f"{sid} ist={ist[sid]}/soll={soll}"
        for sid, soll in erwartete.items()
        if ist[sid] != soll
    ]
    if abweichungen:
        raise UnvollstaendigerClaudeOutput("Slot-Anzahl-Abweichung — " + ", ".join(abweichungen))


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

    # Retry mit Backoff (9-3a): API-Fehler, JSON-Parse, Pydantic-Validierung (unbekannte
    # exercise_id) UND Vollständigkeits-Check laufen über denselben Pfad. NIE Prompt-Inhalt loggen.
    for versuch in range(1, MAX_VERSUCHE + 1):
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
            _pruefe_vollstaendigkeit(result, sessions)
        except Exception as e:
            # NUR Fehlertyp + Message (enthält nur IDs/Counts/API-Text) — NIE Prompt/Klient-Daten.
            if versuch < MAX_VERSUCHE:
                pause = BACKOFF_SEKUNDEN[versuch - 1]
                log.warning(f"[vorgang={vorgang_id}] Claude-Versuch {versuch}/{MAX_VERSUCHE} "
                            f"fehlgeschlagen nach {time.monotonic() - t0:.1f}s: "
                            f"{type(e).__name__}: {e} — Retry in {pause}s")
                time.sleep(pause)
                continue
            log.error(f"[vorgang={vorgang_id}] Claude endgültig fehlgeschlagen nach {MAX_VERSUCHE} "
                      f"Versuchen: {type(e).__name__}: {e}")
            raise

        usage = getattr(response, "usage", None)
        tok = f", Tokens in/out {usage.input_tokens}/{usage.output_tokens}" if usage else ""
        log.info(f"[vorgang={vorgang_id}] Claude-Antwort — {time.monotonic() - t0:.1f}s, "
                 f"{len(result.sessions)} Sessions{tok} (Versuch {versuch}/{MAX_VERSUCHE})")
        return result
