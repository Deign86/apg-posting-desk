-- Migration 024: Create apr-listing staging bucket, extend assets CHECK, fix apg-private drift
--
-- This migration does four things:
--   1. Creates the `apr-listing` bucket (private, staff-write) as the raw staging
--      mirror of the APR LISTING Drive folder. The desk's ingest writes pending-review
--      originals here; approved/published assets get promoted to apg-public/apg-private.
--   2. Extends the `assets.storage_bucket` CHECK constraint to allow `apr-listing`.
--   3. Adds RLS policies for the new bucket (staff read/write/delete).
--   4. Drops the `apg_private_public_read` policy from migration 020 (which made
--      the "private" bucket publicly readable), restoring staff-only per 012.

-- ============ 1. Create apr-listing bucket (private staging) ============
INSERT INTO storage.buckets (id, name, public, avif_autodetection, file_size_limit, allowed_mime_types)
VALUES (
  'apr-listing',
  'apr-listing',
  false,
  false,
  26214400,
  '{image/jpeg,image/png,image/webp,application/pdf}'
)
ON CONFLICT (id) DO NOTHING;

-- ============ 2. Extend assets.storage_bucket CHECK to include apr-listing ============
ALTER TABLE public.assets
  DROP CONSTRAINT IF EXISTS assets_storage_bucket_check,
  ADD CONSTRAINT assets_storage_bucket_check
    CHECK (storage_bucket IN ('apg-public', 'apg-private', 'apr-listing'));

-- ============ 3. RLS for apr-listing (staff-only read/write/delete) ============
DROP POLICY IF EXISTS "apr-listing staff read" ON storage.objects;
CREATE POLICY "apr-listing staff read"
  ON storage.objects FOR SELECT
  TO authenticated
  USING (bucket_id = 'apr-listing' AND public.is_staff());

DROP POLICY IF EXISTS "apr-listing staff write" ON storage.objects;
CREATE POLICY "apr-listing staff write"
  ON storage.objects FOR INSERT
  TO authenticated
  WITH CHECK (bucket_id = 'apr-listing' AND public.is_staff());

DROP POLICY IF EXISTS "apr-listing staff update" ON storage.objects;
CREATE POLICY "apr-listing staff update"
  ON storage.objects FOR UPDATE
  TO authenticated
  USING (bucket_id = 'apr-listing' AND public.is_staff());

DROP POLICY IF EXISTS "apr-listing staff delete" ON storage.objects;
CREATE POLICY "apr-listing staff delete"
  ON storage.objects FOR DELETE
  TO authenticated
  USING (bucket_id = 'apr-listing' AND public.is_staff());

-- ============ 4. Fix apg-private drift from migration 020 ============
-- Migration 020 added an unrestricted SELECT policy on apg-private, making the
-- "private" bucket publicly readable. Restore staff-only per 012.
DROP POLICY IF EXISTS "apg_private_public_read" ON storage.objects;
