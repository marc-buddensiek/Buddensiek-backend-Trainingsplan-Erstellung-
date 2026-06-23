"""
Supabase-Datenbankschicht.

Tabellen:
  clients   — Klientenstammdaten + aktuelles Level
  plans     — vollständige Plan-JSONs (JSONB-Spalte)
  vorgaenge — technischer Vorgangs-Status (läuft → fertig | fehlgeschlagen), s. schema/001_vorgaenge.sql
"""

from __future__ import annotations
import logging
import os
from datetime import datetime, timezone

from supabase import create_client, Client
from models import KlientenInput, Plan

log = logging.getLogger(__name__)

_client: Client | None = None


def _get_client() -> Client:
    global _client
    if _client is None:
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_KEY"]
        _client = create_client(url, key)
    return _client


async def speichere_klient(klient: KlientenInput, level: int, split_typ: str) -> None:
    db = _get_client()
    db.table("clients").upsert({
        "client_id":  klient.client_id,
        "vorname":    klient.vorname,
        "alter":      klient.alter,
        "level":      level,
        "split_typ":  split_typ,
        "equipment":  klient.equipment.value,
    }).execute()
    log.info(f"[DB] Klient {klient.client_id} gespeichert")


async def speichere_plan(plan: Plan) -> None:
    db = _get_client()
    db.table("plans").insert({
        "plan_id":      plan.plan_id,
        "client_id":    plan.client_id,
        "erstellt_am":  plan.erstellt_am,
        "block_nummer": plan.block_nummer,
        "status":       "pending_review",
        "plan_data":    plan.model_dump(),
    }).execute()
    log.info(f"[DB] Plan {plan.plan_id} gespeichert")


# ── Vorgangs-Status-Lebenszyklus (MVP-10) ───────────────────────────────────────
# Bewusst SYNCHRON (anders als speichere_* oben): ein Vorgang muss sofort als 'läuft'
# persistiert sein, bevor der Hintergrund-Task startet. Status: läuft → fertig |
# fehlgeschlagen (s. schema/001_vorgaenge.sql). aktualisiert_am wird Python-seitig gesetzt
# (timestamptz akzeptiert ISO-8601); erstellt_am bleibt der DB-Default beim Insert.

def _jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def vorgang_starten(vorgang_id: str, client_id: str) -> None:
    _get_client().table("vorgaenge").upsert({
        "vorgang_id":      vorgang_id,
        "client_id":       client_id,
        "status":          "läuft",
        "aktualisiert_am": _jetzt(),
    }).execute()
    log.info(f"[DB] Vorgang {vorgang_id} → läuft")


def vorgang_fertig(vorgang_id: str, plan_id: str) -> None:
    _get_client().table("vorgaenge").update({
        "status":          "fertig",
        "plan_id":         plan_id,
        "aktualisiert_am": _jetzt(),
    }).eq("vorgang_id", vorgang_id).execute()
    log.info(f"[DB] Vorgang {vorgang_id} → fertig (plan {plan_id})")


def vorgang_fehlgeschlagen(vorgang_id: str, fehler_text: str) -> None:
    _get_client().table("vorgaenge").update({
        "status":          "fehlgeschlagen",
        "fehler_text":     fehler_text,
        "aktualisiert_am": _jetzt(),
    }).eq("vorgang_id", vorgang_id).execute()
    log.info(f"[DB] Vorgang {vorgang_id} → fehlgeschlagen: {fehler_text[:80]}")
