-- 0001_init.sql -- APG Posting Desk: desk-owned reporting tables
-- CANONICAL PROJECT: ldtavdybcgwjgticrymz (shared with apg-website).
-- Creates ONLY desk-owned tables. Does NOT create profiles, offerings, assets,
-- categories, transaction_types, property_asset_versions, raw_folder_mappings,
-- or activity_log -- those are owned by apg-website. See SHARED_ASSET_ARCHITECTURE.md.

CREATE TABLE IF NOT EXISTS public.posted_log (
  id            BIGSERIAL PRIMARY KEY,
  posted_on     DATE NOT NULL,
  offering_id   BIGINT REFERENCES public.offerings(id) ON DELETE SET NULL,
  property_name TEXT NOT NULL,
  post_url      TEXT NOT NULL,
  status        TEXT NOT NULL DEFAULT 'Posted',
  posted_by     TEXT NOT NULL DEFAULT '',
  posted_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS posted_log_on_idx ON public.posted_log (posted_on);
CREATE INDEX IF NOT EXISTS posted_log_offering_idx ON public.posted_log (offering_id);

ALTER TABLE public.posted_log ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "staff read posted_log" ON public.posted_log;
CREATE POLICY "staff read posted_log" ON public.posted_log
  FOR SELECT TO authenticated USING (public.is_staff());
DROP POLICY IF EXISTS "staff insert posted_log" ON public.posted_log;
CREATE POLICY "staff insert posted_log" ON public.posted_log
  FOR INSERT TO authenticated WITH CHECK (public.is_staff());
DROP POLICY IF EXISTS "staff update posted_log" ON public.posted_log;
CREATE POLICY "staff update posted_log" ON public.posted_log
  FOR UPDATE TO authenticated USING (public.is_staff()) WITH CHECK (public.is_staff());