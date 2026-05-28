"""
Supabase-Datenbankschicht — wird in Phase 2 implementiert.

Tabellen (PostgreSQL via Supabase):
  clients  — Klientenstammdaten + aktuelles Level
  plans    — vollständige Plan-JSONs (JSONB-Spalte)

Bis Supabase eingerichtet ist, speichert speichere_plan() lokal in output/.
"""

from __future__ import annotations
import json
import logging
import os
import pathlib

from models import KlientenInput, Plan

log = logging.getLogger(__name__)

_OUTPUT_DIR = pathlib.Path(__file__).parent / "output"

# ── Supabase Client (noch nicht aktiv) ────────────────────────────────────────
# from supabase import create_client
# _supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


async def speichere_klient(klient: KlientenInput, level: int, split_typ: str) -> None:
    """
    Klient in Supabase 'clients'-Tabelle anlegen oder aktualisieren (upsert).

    Geplantes Schema:
      client_id   UUID  PRIMARY KEY
      vorname     TEXT
      alter       INT
      level       INT
      split_typ   TEXT
      equipment   TEXT
      erstellt_am TIMESTAMPTZ
      aktualisiert_am TIMESTAMPTZ
    """
    # TODO: Supabase upsert
    # _supabase.table("clients").upsert({
    #     "client_id":  klient.client_id,
    #     "vorname":    klient.vorname,
    #     "alter":      klient.alter,
    #     "level":      level,
    #     "split_typ":  split_typ,
    #     "equipment":  klient.equipment.value,
    # }).execute()
    log.info(f"[DB] speichere_klient: {klient.client_id} (Supabase noch nicht konfiguriert)")


async def speichere_plan(plan: Plan) -> None:
    """
    Vollständigen Plan in Supabase 'plans'-Tabelle speichern.

    Geplantes Schema:
      plan_id      UUID  PRIMARY KEY
      client_id    UUID  REFERENCES clients(client_id)
      erstellt_am  TIMESTAMPTZ
      block_nummer INT
      status       TEXT  DEFAULT 'pending_review'
      plan_data    JSONB  — vollständiger Plan als JSON
    """
    # TODO: Supabase insert
    # _supabase.table("plans").insert({
    #     "plan_id":      plan.plan_id,
    #     "client_id":    plan.client_id,
    #     "erstellt_am":  plan.erstellt_am,
    #     "block_nummer": plan.block_nummer,
    #     "status":       "pending_review",
    #     "plan_data":    plan.model_dump(),
    # }).execute()

    # Fallback: lokal speichern
    _OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = _OUTPUT_DIR / f"plan_{plan.client_id[:8]}.json"
    out_path.write_text(json.dumps(plan.model_dump(), indent=2, ensure_ascii=False))
    log.info(f"[DB] Plan gespeichert lokal: {out_path}")
