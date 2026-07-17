-- Migration 013: Deprecation checklist for old asset columns and buckets
-- All destructive operations are COMMENTED OUT below.
-- Only uncomment after verifying ALL listings render correctly from property_asset_relations.

-- ============ Record migration completion ============
insert into public.site_settings (key, value)
values ('asset_layer_migration_completed_at', now()::text)
on conflict (key) do update set value = excluded.value;

-- ============ offerings.images deprecation ============
-- The images JSONB column is no longer written by the application.
-- Frontend dual-read (Phase 6) falls back to it only when property_asset_relations is empty.
-- Once verified that no offering relies on the fallback (1-sprint observation period):

-- ⚠️ MANUAL STEP — only after verification checklist passes:
--   [ ] All offerings have at least one property_asset_relations row with is_cover=true
--   [ ] No frontend code references p.images[0] as primary source
--   [ ] No server/API route reads offerings.images
--   [ ] Admin has confirmed no broken images in dev console
--
-- alter table public.offerings drop column if exists images;

-- ============ Old storage bucket deprecation ============
-- Buckets replaced by apg-public/apg-private:
--   listing-images → migrated to apg-public via import pipeline
--   blog-images    → still in use by blog_posts.cover_image (text URL column, not asset layer)
--   careers        → still in use
--   admins         → still in use
--   chat           → still in use
--
-- Only listing-images is safe to remove after full cutover.
-- Blog-images/careers/admins/chat are NOT touched by this migration.
--
-- ⚠️ MANUAL STEP — only after verifying listing-images bucket is empty and unreferenced:
--
-- -- drop policy if exists "staff write listing images" on storage.objects;
-- -- drop policy if exists "staff delete listing images" on storage.objects;
-- -- drop policy if exists "public read listing images" on storage.objects;
-- -- drop storage bucket if exists listing-images;
