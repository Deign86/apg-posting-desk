-- Migration 011: Asset layer schema for apg-website
-- Creates 4 new tables: assets, property_asset_relations, import_batches, import_file_mappings
-- Extends offerings with cover_asset_id, gallery_count, import_batch_id
-- Dependencies: public.handle_updated_at() and public.is_staff() already exist ( migrations 0090, 0101 )

-- ============ STORAGE BUCKETS ============
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  ('apg-public',  'apg-public',  true,  10485760,  '{image/jpeg,image/png,image/webp,image/avif}'),
  ('apg-private', 'apg-private', false, 26214400,  '{application/pdf,image/jpeg,image/png}')
on conflict (id) do nothing;

-- ============ NEW TABLES (create before FK references) ============

-- ============ assets ============
create table if not exists public.assets (
  id             uuid primary key default gen_random_uuid(),
  asset_type     text  not null default 'image'
                 check (asset_type in ('image','brochure','floor_plan','document','video')),
  mime_type      text  not null,
  size_bytes     bigint,
  original_name  text,
  storage_path   text  not null unique,
  storage_bucket text  not null default 'apg-public'
                 check (storage_bucket in ('apg-public','apg-private')),
  width          int,
  height         int,
  is_public      boolean not null default true,
  import_batch_id text,
  source_path    text,          -- Windows path for audit only — never exposed to frontend
  ingestion_status text not null default 'active'
                 check (ingestion_status in ('active','archived','error','pending_review')),
  error_message  text,
  created_by     uuid references public.profiles(id) on delete set null,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

create index if not exists idx_assets_bucket   on public.assets(storage_bucket);
create index if not exists idx_assets_type     on public.assets(asset_type);
create index if not exists idx_assets_public   on public.assets(is_public) where is_public = true;
create index if not exists idx_assets_batch    on public.assets(import_batch_id);

alter table public.assets enable row level security;

-- Public: discover active public assets (needed for gallery queries)
drop policy if exists "public read public assets" on public.assets;
create policy "public read public assets"
  on public.assets for select
  using (is_public = true and ingestion_status = 'active');

-- Staff: full CRUD
drop policy if exists "staff manage assets" on public.assets;
create policy "staff manage assets"
  on public.assets for all
  to authenticated
  using (public.is_staff())
  with check (public.is_staff());

drop trigger if exists set_updated_at on public.assets;
create trigger set_updated_at
  before update on public.assets
  for each row execute function public.handle_updated_at();

-- ============ property_asset_relations ============
create table if not exists public.property_asset_relations (
  id            uuid primary key default gen_random_uuid(),
  offering_id   bigint not null references public.offerings(id) on delete cascade,
  asset_id      uuid   not null references public.assets(id)   on delete cascade,
  gallery_role  text  not null default 'gallery'
                check (gallery_role in ('hero','gallery','thumbnail','brochure','floor_plan')),
  display_order int   not null default 0,
  alt_text      text,
  caption       text,
  is_cover      boolean not null default false,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now(),
  constraint unique_offering_asset unique (offering_id, asset_id)
);

-- Partial unique index: exactly one hero per offering
create unique index if not exists unique_offering_cover
  on public.property_asset_relations (offering_id)
  where is_cover = true;

create index if not exists idx_relations_offering
  on public.property_asset_relations (offering_id, display_order);
create index if not exists idx_relations_asset
  on public.property_asset_relations (asset_id);

alter table public.property_asset_relations enable row level security;

-- Public: read relations only for published, non-deleted offerings
drop policy if exists "public read relations for published offerings" on public.property_asset_relations;
create policy "public read relations for published offerings"
  on public.property_asset_relations for select
  using (
    exists (
      select 1 from public.offerings o
      where o.id = offering_id
        and o.is_published = true
        and o.deleted_at is null
    )
  );

-- Staff: full CRUD
drop policy if exists "staff manage relations" on public.property_asset_relations;
create policy "staff manage relations"
  on public.property_asset_relations for all
  to authenticated
  using (public.is_staff())
  with check (public.is_staff());

drop trigger if exists set_updated_at on public.property_asset_relations;
create trigger set_updated_at
  before update on public.property_asset_relations
  for each row execute function public.handle_updated_at();

-- ============ import_batches ============
create table if not exists public.import_batches (
  id           text primary key,
  source_root  text     not null,
  status       text     not null default 'running'
               check (status in ('running','completed','partial_failure','failed','cancelled')),
  stats        jsonb    default '{}'::jsonb,
  error_summary text,
  started_at   timestamptz not null default now(),
  completed_at timestamptz,
  created_by   uuid references public.profiles(id) on delete set null
);

-- ============ import_file_mappings ============
create table if not exists public.import_file_mappings (
  id               uuid primary key default gen_random_uuid(),
  import_batch_id  text  not null references public.import_batches(id) on delete cascade,
  source_path      text  not null,
  source_filename  text  not null,
  source_folder    text  not null,
  file_size_bytes  bigint,
  mime_type        text,
  checksum_sha256  text,
  asset_id         uuid references public.assets(id) on delete set null,
  status           text  not null default 'pending'
               check (status in ('pending','uploaded','skipped_duplicate','skipped_no_match','failed')),
  error_message    text,
  processed_at     timestamptz,
  created_at       timestamptz not null default now()
);

create index if not exists idx_mappings_batch  on public.import_file_mappings (import_batch_id);
create index if not exists idx_mappings_asset  on public.import_file_mappings (asset_id);
create index if not exists idx_mappings_status on public.import_file_mappings (status);

alter table public.import_file_mappings enable row level security;

-- Staff: read/write (internal traceability — never frontend-facing)
drop policy if exists "staff read mappings" on public.import_file_mappings;
create policy "staff read mappings"
  on public.import_file_mappings for select
  to authenticated
  using (public.is_staff());

drop policy if exists "staff write mappings" on public.import_file_mappings;
create policy "staff write mappings"
  on public.import_file_mappings for all
  to authenticated
  using (public.is_staff())
  with check (public.is_staff());

-- ============ EXTEND offerings (FK targets now exist) ============
alter table public.offerings
  add column if not exists cover_asset_id uuid references public.assets(id) on delete set null,
  add column if not exists gallery_count   int  not null default 0,
  add column if not exists import_batch_id text;

-- ============ EXTEND handle_updated_at trigger to new tables ============
do $$
declare t text;
begin
  foreach t in array array['assets','property_asset_relations','import_file_mappings','import_batches']
  loop
    execute format('drop trigger if exists set_updated_at on public.%I', t);
    execute format(
      'create trigger set_updated_at before update on public.%I for each row execute function public.handle_updated_at()', t);
  end loop;
end $$;
