-- Migration 017: Add updated_at columns for tables that have set_updated_at triggers
alter table public.categories add column if not exists updated_at timestamptz not null default now();
alter table public.transaction_types add column if not exists updated_at timestamptz not null default now();
alter table public.property_asset_versions add column if not exists updated_at timestamptz not null default now();
alter table public.raw_folder_mappings add column if not exists updated_at timestamptz not null default now();
alter table public.posted_log add column if not exists updated_at timestamptz not null default now();
-- Also add set_updated_at trigger to posted_log (desk-owned, was missing)
do $$
declare t text;
begin
  foreach t in array array['posted_log']
  loop
    execute format('drop trigger if exists set_updated_at on public.%I', t);
    execute format('create trigger set_updated_at before update on public.%I for each row execute function public.handle_updated_at()', t);
  end loop;
end $$;
