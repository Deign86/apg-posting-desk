-- Migration 016: Storage path convention lint + flat->nested migration helper
-- Non-destructive. The canonical storage key pattern is:
--   properties/{property_id}/images/{asset_id}/original.jpg
--   properties/{property_id}/images/{asset_id}/thumb.webp
--   properties/{property_id}/images/{asset_id}/v{version}/facebook-ready.jpg
--   properties/{property_id}/documents/{asset_id}/brochure.pdf
-- This migration adds a lint VIEW that flags assets NOT following the nested convention,
-- so the flat-path assets created by the old asset_service.py ({uuid}-original.{ext})
-- can be found and migrated. Actual byte relocation is a manual/scripted step (see below).

-- View: assets whose storage_path does NOT start with 'properties/'
create or replace view public.v_assets_noncanonical_path as
  select id, asset_type, storage_bucket, storage_path, original_name, ingestion_status
  from public.assets
  where storage_path is not null
    and storage_path not like 'properties/%';

-- Helper: build the canonical nested path for an asset given an offering id.
-- Usage: select public.canonical_asset_path(<offering_id>, <asset_id>, 'image', 'original', 'jpg');
create or replace function public.canonical_asset_path(
  p_offering_id uuid, p_asset_id uuid, p_asset_type text, p_derivative text, p_ext text
) returns text language sql stable as $$
  select case
    when p_asset_type in ('brochure','floor_plan','document') then
      format('properties/%s/documents/%s/%s.%s', p_offering_id, p_asset_id, p_derivative, p_ext)
    else
      case
        when p_derivative in ('original') then
          format('properties/%s/images/%s/original.%s', p_offering_id, p_asset_id, p_ext)
        when p_derivative like 'v%' then
          format('properties/%s/images/%s/%s/facebook-ready.%s', p_offering_id, p_asset_id, p_derivative, p_ext)
        else
          format('properties/%s/images/%s/%s.%s', p_offering_id, p_asset_id, p_derivative, p_ext)
      end
  end;
$$;

-- Record that the convention is adopted (non-destructive marker)
insert into public.site_settings (key, value)
values ('storage_path_convention', 'properties/{property_id}/(images|documents)/{asset_id}/...')
on conflict (key) do update set value = excluded.value;

-- MANUAL MIGRATION STEP (run after ingest refactor; not done in SQL because it moves bytes):
--   For each row in v_assets_noncanonical_path:
--     1. Download the object from its bucket at storage_path.
--     2. Find the offering_id via property_asset_relations.asset_id = assets.id.
--     3. Upload to the canonical path from canonical_asset_path(...).
--     4. Update assets.storage_path + property_asset_versions.object_path to the new path.
--     5. Optionally remove the old object.
--   The desk's asset_service.py now writes nested paths directly, so new uploads are correct.
