-- ═══════════════════════════════════════════════════════════════════════════
-- Schema 001 — Tabelle "vorgaenge" (Vorgangs-Status-Persistenz, MVP-10)
-- ═══════════════════════════════════════════════════════════════════════════
-- Zweck: technischer Lebenszyklus eines Plan-Generierungs-Vorgangs:
--   läuft → fertig | fehlgeschlagen
-- Macht hängende/fehlgeschlagene Vorgänge DB-seitig sichtbar (heute nur in Logzeilen).
--
-- Diese Datei ist die SCHEMA-WAHRHEIT (versioniert im Repo). Das Supabase-Dashboard
-- FÜHRT dieses SQL nur AUS — Änderungen passieren hier, nicht im Dashboard.
--
-- NICHT betroffen: plans.status = 'pending_review' (eigene Coaching-Achse, bleibt).

create table if not exists vorgaenge (
    vorgang_id      text primary key,
    client_id       text        not null,
    status          text        not null check (status in ('läuft', 'fertig', 'fehlgeschlagen')),
    fehler_text     text,
    plan_id         text,
    erstellt_am     timestamptz not null default now(),
    aktualisiert_am timestamptz not null default now()
);


-- ───────────────────────────────────────────────────────────────────────────
-- SKIZZE (NICHT ausführen) — spätere Trainings-Logging-Tabellen (MVP-11.7).
-- Hier nur als Kommentar dokumentiert, damit die spätere Ergänzung eine reine
-- Hinzufügung ist und KEINE Migration der obigen "vorgaenge"-Tabelle erfordert.
-- (Bezug: Thema 7 — Trainings-Logging / Set-Logs.)
--
-- create table weeks (
--     week_id      text primary key,
--     plan_id      text        not null references plans(plan_id),
--     woche_nummer int         not null,
--     block_typ    text        not null
-- );
--
-- create table sessions (
--     session_id   text primary key,
--     week_id      text        not null references weeks(week_id),
--     tag          text        not null,
--     session_typ  text        not null,
--     fokus        text
-- );
--
-- create table set_logs (
--     set_log_id      text primary key,
--     session_id      text        not null references sessions(session_id),
--     exercise_id     text        not null,
--     satz_nummer     int         not null,
--     last            numeric,
--     wiederholungen  int,
--     erstellt_am     timestamptz not null default now()
-- );
-- ───────────────────────────────────────────────────────────────────────────
