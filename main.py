"""
Buddensiek Performance — KI-Trainingsplan Backend
FastAPI App · Einstiegspunkt

Endpoint:
  POST /api/new-plan  — Typeform Webhook → Plan generieren + speichern
  GET  /health        — Railway Health-Check
"""

from __future__ import annotations
import logging
import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse

load_dotenv()

from parsers import parse_typeform_payload
from logic.level_calculator import berechne_level
from logic.volume_calculator import berechne_volumen
from logic.split_selector import waehle_split
from logic.equipment_filter import filtere_uebungen
from logic.plan_assembler import assemble_plan
from claude.claude_client import generiere_uebungsauswahl
from db import speichere_plan, speichere_klient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

app = FastAPI(title="Buddensiek Performance API", version="0.1.0")


# ═══════════════════════════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# ═══════════════════════════════════════════════════════════════════════════════
# Typeform Webhook → Plan generieren
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/new-plan", status_code=202)
async def new_plan(request: Request, background_tasks: BackgroundTasks):
    """
    Empfängt den Typeform-Webhook, validiert den Payload und
    startet die Plan-Generierung im Hintergrund (damit Typeform kein Timeout bekommt).
    """
    payload = await request.json()

    # Schnell-Validierung: ist das ein Typeform form_response?
    if payload.get("event_type") != "form_response":
        raise HTTPException(status_code=400, detail="Kein form_response Event")

    background_tasks.add_task(_generiere_plan_task, payload)
    return {"status": "accepted", "message": "Plan-Generierung gestartet"}


async def _generiere_plan_task(payload: dict):
    """Läuft im Hintergrund — Typeform muss nicht warten."""
    try:
        await _pipeline(payload)
    except Exception as e:
        log.error(f"Pipeline-Fehler: {e}", exc_info=True)


async def _pipeline(payload: dict):
    start = datetime.now(timezone.utc)

    # ── 1. Typeform parsen + validieren ───────────────────────────────────────
    try:
        klient = parse_typeform_payload(payload)
    except Exception as e:
        log.error(f"Parser-Fehler für payload token={payload.get('form_response', {}).get('token')}: {e}")
        return

    log.info(f"[{klient.client_id}] Start — {klient.vorname}, {klient.alter}J, {klient.hauptziel.value}")

    # ── 2. Deterministische Berechnungen ─────────────────────────────────────
    level, punkte = berechne_level(klient)
    woche_typ = "akkumulation"  # Block 1 startet immer mit Akkumulation
    volumen = berechne_volumen(klient, level, woche_typ)
    split = waehle_split(klient, level)
    uebungen = filtere_uebungen(klient, level)

    log.info(
        f"[{klient.client_id}] Level={level} | Split={split['split_typ']} | "
        f"{volumen['ziel_saetze']} Sätze RPE {volumen['ziel_rpe']} | "
        f"{sum(len(v) for v in uebungen.values())} Übungen verfügbar"
    )

    # ── 3. Claude: Übungsauswahl ──────────────────────────────────────────────
    sessions_fuer_claude = split["sessions"]
    claude_output = generiere_uebungsauswahl(
        klient=klient,
        level=level,
        split_typ=split["split_typ"],
        block_nummer=1,
        sessions=sessions_fuer_claude,
        uebungen_gefiltert=uebungen,
        woche_typ=woche_typ,
        ziel_saetze=volumen["ziel_saetze"],
        ziel_rpe=volumen["ziel_rpe"],
    )

    log.info(f"[{klient.client_id}] Claude: {len(claude_output.sessions)} Sessions erhalten")

    # ── 4. Vollständigen Plan zusammenbauen ───────────────────────────────────
    plan = assemble_plan(
        klient=klient,
        level=level,
        split=split,
        claude_output=claude_output,
        block_nummer=1,
    )

    dauer_sek = (datetime.now(timezone.utc) - start).total_seconds()
    log.info(f"[{klient.client_id}] Plan {plan.plan_id} fertig in {dauer_sek:.1f}s")

    # ── 5. Klient + Plan in Supabase speichern ────────────────────────────────
    await speichere_klient(klient, level, split["split_typ"])
    await speichere_plan(plan)

    log.info(f"[{klient.client_id}] Plan {plan.plan_id} gespeichert ✓")


# ═══════════════════════════════════════════════════════════════════════════════
# Dev-Endpunkt: Pipeline mit fake_typeform.json testen (nicht in Production)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/api/dev/test-plan")
async def test_plan(request: Request):
    """
    Führt die komplette Pipeline mit fake_typeform.json aus und gibt den Plan zurück.
    Nur lokal verwenden — in Production durch RENDER_SERVICE_ID geblockt.
    """
    if os.environ.get("RENDER_SERVICE_ID"):
        raise HTTPException(status_code=403, detail="Dev-Endpoint in Production nicht verfügbar")
    import json, pathlib
    payload = json.loads(
        (pathlib.Path(__file__).parent / "data" / "fake_typeform.json").read_text()
    )

    klient = parse_typeform_payload(payload)
    level, _ = berechne_level(klient)
    volumen = berechne_volumen(klient, level, "akkumulation")
    split = waehle_split(klient, level)
    uebungen = filtere_uebungen(klient, level)

    sessions_fuer_claude = split["sessions"]
    claude_output = generiere_uebungsauswahl(
        klient=klient,
        level=level,
        split_typ=split["split_typ"],
        block_nummer=1,
        sessions=sessions_fuer_claude,
        uebungen_gefiltert=uebungen,
        woche_typ="akkumulation",
        ziel_saetze=volumen["ziel_saetze"],
        ziel_rpe=volumen["ziel_rpe"],
    )

    plan = assemble_plan(
        klient=klient,
        level=level,
        split=split,
        claude_output=claude_output,
        block_nummer=1,
    )

    return plan.model_dump()
