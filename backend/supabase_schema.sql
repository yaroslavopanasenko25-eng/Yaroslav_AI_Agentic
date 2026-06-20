-- GuardianEye — Supabase schema
-- Run this once in the Supabase SQL Editor (or via psql) to create all tables.
-- Tables use Row Level Security (RLS) — enable policies as needed for your auth setup.

-- ── alerts ────────────────────────────────────────────────────────────────────
-- Stores every air-raid alert ingested from alerts.in.ua.

create table if not exists public.alerts (
    id               text        primary key,          -- external ID from alerts.in.ua
    region_id        text,                              -- numeric UID from the API (e.g. "19")
    region           text        not null default 'unknown',
    alert_type       text        not null default 'unknown',  -- e.g. "air_raid", "artillery"
    start_time       timestamptz,
    end_time         timestamptz,
    duration_minutes integer,
    is_active        boolean     not null default true,
    raw              jsonb,                             -- full original API payload
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now()
);

-- Auto-update updated_at on every row change
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists alerts_updated_at on public.alerts;
create trigger alerts_updated_at
    before update on public.alerts
    for each row execute procedure public.set_updated_at();

-- Useful indexes
create index if not exists alerts_start_time_idx  on public.alerts (start_time desc);
create index if not exists alerts_region_idx       on public.alerts (region);
create index if not exists alerts_is_active_idx    on public.alerts (is_active);
create index if not exists alerts_alert_type_idx   on public.alerts (alert_type);

-- ── shelters ──────────────────────────────────────────────────────────────────
-- Known shelter locations shown on the Safety tab map.

create table if not exists public.shelters (
    id          text        primary key,
    name_uk     text        not null,
    name_en     text        not null,
    city        text        not null,
    lat         double precision not null,
    lng         double precision not null,
    capacity    integer,
    shelter_type text       not null default 'basement',  -- metro | basement | bomb_shelter
    is_active   boolean     not null default true,
    created_at  timestamptz not null default now()
);

create index if not exists shelters_city_idx on public.shelters (city);

-- ── ai_conversations ──────────────────────────────────────────────────────────
-- Optional: persist AI Agent chat history per anonymous session.

create table if not exists public.ai_conversations (
    id          uuid        primary key default gen_random_uuid(),
    session_id  text        not null,
    role        text        not null check (role in ('user', 'assistant')),
    content     text        not null,
    created_at  timestamptz not null default now()
);

create index if not exists ai_conversations_session_idx on public.ai_conversations (session_id, created_at);

-- ── Row Level Security ────────────────────────────────────────────────────────
-- Alerts and shelters are public-read; writes are restricted to the service role.

alter table public.alerts             enable row level security;
alter table public.shelters           enable row level security;
alter table public.ai_conversations   enable row level security;

-- Allow anyone to read alerts and shelters (dashboard is public)
create policy "public read alerts"
    on public.alerts for select using (true);

create policy "public read shelters"
    on public.shelters for select using (true);

-- Service role (your SUPABASE_KEY) can do everything (bypasses RLS by default).
-- To allow the backend to write alerts, either use the service-role key or add:
--
-- create policy "service write alerts"
--     on public.alerts for all
--     using (auth.role() = 'service_role');
