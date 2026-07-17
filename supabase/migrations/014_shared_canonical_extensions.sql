-- Migration 014: Shared canonical extensions for apg-website x apg-posting-desk
-- Adds: categories, transaction_types, property_asset_versions, raw_folder_mappings
-- Extends: offerings (category/txn/raw folder/parse fields), assets (version/approval)
-- Idempotent. Owner: apg-website (canonical schema). See SHARED_ASSET_ARCHITECTURE.md.
-- Assumes: offerings.id is uuid (per supabase/schema.sql); assets + import_batches from 011;
--          profiles from 001/0090; is_staff()/handle_updated_at() exist.

-- ============ categories (shared lookup) ============
create table if not exists public.categories (
  id            uuid primary key default gen_random_uuid(),
  name          text unique not null,
  slug          text unique not null,
  parent_id     uuid references public.categories(id) on delete set null,
  display_order int  not null default 0,
  created_at    timestamptz not null default now()
);
alter table public.categories enable row level security;
drop policy if exists "public read categories" on public.categories;
create policy "public read categories" on public.categories for select using (true);
drop policy if exists "staff manage categories" on public.categories;
create policy "staff manage categories" on public.categories for all to authenticated
  using (public.is_staff()) with check (public.is_staff());

-- ============ transaction_types (shared lookup) ============
create table if not exists public.transaction_types (
  id    uuid primary key default gen_random_uuid(),
  name  text unique not null,                 -- 'lease' | 'sale' | 'sold' | 'virtual'
  label text,                                 -- human label
  created_at timestamptz not null default now()
);
alter table public.transaction_types enable row level security;
drop policy if exists "public read transaction_types" on public.transaction_types;
create policy "public read transaction_types" on public.transaction_types for select using (true);
drop policy if exists "staff manage transaction_types" on public.transaction_types;
create policy "staff manage transaction_types" on public.transaction_types for all to authenticated
  using (public.is_staff()) with check (public.is_staff());

-- ============ property_asset_versions (shared, non-destructive history) ============
create table if not exists public.property_asset_versions (
  id              uuid primary key default gen_random_uuid(),
  asset_id        uuid not null references public.assets(id) on delete cascade,
  version_number  int  not null,
  storage_bucket  text not null check (storage_bucket in ('apg-public','apg-private')),
  object_path     text not null,
  derivative_kind text not null default 'original'
                  check (derivative_kind in ('original','thumb','hero','gallery','facebook-ready','web-optimized')),
  width           int, height int, size_bytes bigint,
  sha256          text,
  created_by      uuid references public.profiles(id) on delete set null,
  is_current      boolean not null default true,
  created_at      timestamptz not null default now(),
  unique (asset_id, version_number, derivative_kind)
);
create index if not exists idx_pav_asset on public.property_asset_versions (asset_id);
create index if not exists idx_pav_current on public.property_asset_versions (asset_id) where is_current = true;
alter table public.property_asset_versions enable row level security;
drop policy if exists "public read current public versions" on public.property_asset_versions;
create policy "public read current public versions" on public.property_asset_versions
  for select using (
    is_current = true
    and exists (select 1 from public.assets a where a.id = asset_id
                and a.is_public = true and a.ingestion_status = 'active')
  );
drop policy if exists "staff manage versions" on public.property_asset_versions;
create policy "staff manage versions" on public.property_asset_versions for all to authenticated
  using (public.is_staff()) with check (public.is_staff());

-- ============ raw_folder_mappings (shared, folder->property audit; staff-only) ============
create table if not exists public.raw_folder_mappings (
  id                  uuid primary key default gen_random_uuid(),
  property_id         bigint not null references public.offerings(id) on delete cascade,
  raw_folder_name     text not null,
  raw_folder_path     text not null unique,        -- one canonical property per source folder
  category_id         uuid references public.categories(id) on delete set null,
  transaction_type_id uuid references public.transaction_types(id) on delete set null,
  iteration_label     text,                         -- Virtual Office iteration folder name
  parse_payload       jsonb default '{}'::jsonb,    -- full parser output
  parse_confidence    text not null default 'high' check (parse_confidence in ('high','partial','low')),
  parse_errors        jsonb default '[]'::jsonb,
  import_batch_id     text references public.import_batches(id) on delete set null,
  created_at          timestamptz not null default now()
);
create index if not exists idx_rfm_property on public.raw_folder_mappings (property_id);
create index if not exists idx_rfm_batch on public.raw_folder_mappings (import_batch_id);
alter table public.raw_folder_mappings enable row level security;
drop policy if exists "staff manage raw_folder_mappings" on public.raw_folder_mappings;
create policy "staff manage raw_folder_mappings" on public.raw_folder_mappings for all to authenticated
  using (public.is_staff()) with check (public.is_staff());

-- ============ EXTEND offerings ============
alter table public.offerings
  add column if not exists category_id          uuid references public.categories(id) on delete set null,
  add column if not exists transaction_type_id  uuid references public.transaction_types(id) on delete set null,
  add column if not exists raw_folder_name      text,
  add column if not exists raw_folder_path      text,
  add column if not exists normalized_title     text,
  add column if not exists location_label       text,
  add column if not exists approximate_area_sqm numeric,
  add column if not exists parse_confidence     text check (parse_confidence is null or parse_confidence in ('high','partial','low')),
  add column if not exists parse_errors         jsonb default '[]'::jsonb;
create index if not exists idx_offerings_category on public.offerings (category_id);
create index if not exists idx_offerings_txn on public.offerings (transaction_type_id);

-- Unique slug (only if no duplicates currently exist, to keep migration safe)
do $$
begin
  if not exists (select 1 from pg_indexes where indexname = 'offerings_slug_key') then
    if not exists (select slug from public.offerings where slug is not null group by slug having count(*) > 1) then
      create unique index offerings_slug_key on public.offerings (slug) where slug is not null;
    else
      raise notice 'Skipped unique slug index: duplicate slugs exist — dedup before re-running.';
    end if;
  end if;
end $$;

-- ============ EXTEND assets ============
alter table public.assets
  add column if not exists current_version int  not null default 1,
  add column if not exists approved_by     uuid references public.profiles(id) on delete set null,
  add column if not exists approved_at     timestamptz;

-- ============ updated_at triggers for new tables ============
do $$
declare t text;
begin
  foreach t in array array['categories','transaction_types','property_asset_versions','raw_folder_mappings']
  loop
    execute format('drop trigger if exists set_updated_at on public.%I', t);
    execute format('create trigger set_updated_at before update on public.%I for each row execute function public.handle_updated_at()', t);
  end loop;
end $$;

-- ============ Seed default transaction types ============
insert into public.transaction_types (name, label) values
  ('lease','For Lease'), ('sale','For Sale'), ('sold','Sold'), ('virtual','Virtual Office')
on conflict (name) do nothing;

