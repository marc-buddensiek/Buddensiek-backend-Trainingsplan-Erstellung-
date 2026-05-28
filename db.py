"""
Supabase-Datenbankschicht.

Tabellen:
  clients  — Klientenstammdaten + aktuelles Level
  plans    — vollständige Plan-JSONs (JSONB-Spalte)
"""

from __future__ import annotations
import logging
import os

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
