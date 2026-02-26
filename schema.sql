-- ============================================================
--  PARKEYE — Supabase Schema
--  Paste this entire file into:
--  Supabase Dashboard → SQL Editor → New Query → Run
-- ============================================================


-- ── Extensions ───────────────────────────────────────────────
create extension if not exists "uuid-ossp";   -- uuid_generate_v4()
create extension if not exists "pg_trgm";     -- fuzzy text search (future use)


-- ============================================================
--  TABLE 1: lots
--  One row per physical parking lot or deck on campus.
-- ============================================================
create table if not exists public.lots (
  id               uuid          primary key default uuid_generate_v4(),
  name             text          not null,
  capacity         integer       not null,
  permit_types     text[]        not null default '{}',
  lat              double precision not null,
  lon              double precision not null,
  is_deck          boolean       not null default false,
  floors           integer,                          -- null for surface lots
  status           text          not null default 'open'
                   check (status in ('open', 'limited', 'closed')),
  status_until     timestamptz,                      -- null = no expiry
  status_reason    text,
  created_at       timestamptz   not null default now(),
  updated_at       timestamptz   not null default now()
);

-- Auto-update updated_at on any row change
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger lots_updated_at
  before update on public.lots
  for each row execute function public.set_updated_at();

-- Index for permit filtering (used heavily by /recommendations)
create index if not exists idx_lots_permit_types on public.lots using gin(permit_types);


-- ============================================================
--  TABLE 2: occupancy_snapshots
--  Pre-seeded synthetic occupancy per lot × hour × day.
--  168 rows per lot (24 hours × 7 days).
--  The WebSocket loop and prediction service read from this.
-- ============================================================
create table if not exists public.occupancy_snapshots (
  id              bigserial     primary key,
  lot_id          uuid          not null references public.lots(id) on delete cascade,
  hour_of_day     smallint      not null check (hour_of_day between 0 and 23),
  day_of_week     smallint      not null check (day_of_week between 0 and 6),  -- 0=Mon, 6=Sun
  occupancy_pct   real          not null check (occupancy_pct between 0.0 and 1.0),
  color           text          not null check (color in ('green', 'yellow', 'red')),
  unique (lot_id, hour_of_day, day_of_week)   -- one row per slot per lot
);

create index if not exists idx_occupancy_lot_time
  on public.occupancy_snapshots(lot_id, hour_of_day, day_of_week);


-- ============================================================
--  TABLE 3: campus_events
--  Pre-seeded from mock/events.json via seed.py.
--  Used to bump predicted occupancy for affected lots.
-- ============================================================
create table if not exists public.campus_events (
  id              uuid          primary key default uuid_generate_v4(),
  title           text          not null,
  start_time      timestamptz   not null,
  end_time        timestamptz   not null,
  impact_level    text          not null default 'low'
                  check (impact_level in ('low', 'medium', 'high')),
  affected_lots   uuid[]        not null default '{}',
  created_at      timestamptz   not null default now()
);

create index if not exists idx_events_time
  on public.campus_events(start_time, end_time);


-- ============================================================
--  TABLE 4: feedback
--  Written by POST /feedback after user parks.
-- ============================================================
create table if not exists public.feedback (
  id                  uuid        primary key default uuid_generate_v4(),
  user_id             uuid,                           -- nullable: guests can submit too
  lot_id              uuid        not null references public.lots(id) on delete cascade,
  accuracy_rating     smallint    check (accuracy_rating between 1 and 5),
  experience_rating   smallint    check (experience_rating between 1 and 5),
  note                text,
  created_at          timestamptz not null default now()
);

create index if not exists idx_feedback_lot on public.feedback(lot_id);
create index if not exists idx_feedback_user on public.feedback(user_id);


-- ============================================================
--  TABLE 5: user_settings
--  Stores each user's permit type + notification preference.
--  Linked to Supabase Auth users via user_id = auth.uid().
-- ============================================================
create table if not exists public.user_settings (
  user_id               uuid        primary key references auth.users(id) on delete cascade,
  permit_type           text        not null default 'none',
  notifications_enabled boolean     not null default true,
  updated_at            timestamptz not null default now()
);

create trigger user_settings_updated_at
  before update on public.user_settings
  for each row execute function public.set_updated_at();


-- ============================================================
--  ROW LEVEL SECURITY (RLS)
--  Protects all tables from direct client access.
--  The FastAPI backend uses the service role key (bypasses RLS).
--  These policies only matter if you ever query Supabase directly
--  from the iOS app (which you should NOT do for sensitive data).
-- ============================================================

alter table public.lots               enable row level security;
alter table public.occupancy_snapshots enable row level security;
alter table public.campus_events      enable row level security;
alter table public.feedback           enable row level security;
alter table public.user_settings      enable row level security;

-- lots: anyone authenticated can read, nobody can write directly
create policy "lots_read" on public.lots
  for select using (auth.role() = 'authenticated');

-- occupancy_snapshots: read-only for authenticated users
create policy "occupancy_read" on public.occupancy_snapshots
  for select using (auth.role() = 'authenticated');

-- campus_events: read-only for authenticated users
create policy "events_read" on public.campus_events
  for select using (auth.role() = 'authenticated');

-- feedback: users can insert their own rows and read their own rows
create policy "feedback_insert" on public.feedback
  for insert with check (auth.uid() = user_id or user_id is null);

create policy "feedback_read_own" on public.feedback
  for select using (auth.uid() = user_id);

-- user_settings: users can only see and edit their own row
create policy "settings_select" on public.user_settings
  for select using (auth.uid() = user_id);

create policy "settings_upsert" on public.user_settings
  for all using (auth.uid() = user_id);


-- ============================================================
--  ADMIN ROLE HELPER
--  Call this in the Supabase dashboard to grant a user
--  the 'admin' role so PATCH /admin/lots/{id}/status works.
--
--  Usage (run separately, replace the email):
--    select public.make_admin('shabeer@gmu.edu');
-- ============================================================
create or replace function public.make_admin(user_email text)
returns void language plpgsql security definer as $$
declare
  target_id uuid;
begin
  select id into target_id from auth.users where email = user_email;
  if target_id is null then
    raise exception 'No user found with email %', user_email;
  end if;
  update auth.users
  set raw_app_meta_data = raw_app_meta_data || '{"role": "admin"}'::jsonb
  where id = target_id;
end;
$$;


-- ============================================================
--  SEED: 3 placeholder lots
--  (seed.py will overwrite/extend this with all 10 real GMU lots)
--  This just verifies the schema works immediately after running.
-- ============================================================
insert into public.lots (name, capacity, permit_types, lat, lon, is_deck, floors, status)
values
  ('Lot K',         312,  array['general', 'west_campus'], 38.8296, -77.3069, false, null,  'open'),
  ('Parking Deck 1', 900, array['general', 'deck'],        38.8312, -77.3054, true,  6,     'open'),
  ('Lot J',         198,  array['general'],                38.8278, -77.3081, false, null,  'limited')
on conflict do nothing;
