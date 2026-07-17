-- 0002_shared_assets.sql Ã¢â‚¬â€ Desk-owned posting workflow tables for apg-posting-desk
-- CANONICAL PROJECT: ldtavdybcgwjgticrymz (shared with apg-website).
-- Creates ONLY desk-owned workflow tables. It does NOT create offerings, assets,
-- property_asset_relations, import_batches, import_file_mappings, profiles, activity_log,
-- categories, transaction_types, property_asset_versions, or raw_folder_mappings Ã¢â‚¬â€ those
-- are owned by apg-website and already exist in the shared project. The website owns
-- canonical asset tables; the desk owns posting workflow tables that reference them.
-- See SHARED_ASSET_ARCHITECTURE.md. Apply from this repo after:
--   supabase link --project-ref ldtavdybcgwjgticrymz
--   supabase db push

-- 1) Posting jobs (desk-owned Facebook posting workflow; bound to canonical offering)
CREATE TABLE IF NOT EXISTS public.posting_jobs (
    id                     TEXT PRIMARY KEY,          -- e.g. APG-0704-001
    offering_id            BIGINT REFERENCES public.offerings(id) ON DELETE SET NULL,
    property_name          TEXT NOT NULL DEFAULT '',  -- denormalized for display/legacy
    assigned_by            TEXT NOT NULL DEFAULT '',
    operator               TEXT NOT NULL DEFAULT '',
    due_date               DATE,
    status                 TEXT NOT NULL DEFAULT 'assigned'
        CHECK (status IN ('assigned','preparing','ready','posted','cancelled')),
    caption                TEXT NOT NULL DEFAULT '',
    selected_caption       TEXT NOT NULL DEFAULT '',
    caption_details        TEXT NOT NULL DEFAULT '',
    caption_document_name  TEXT NOT NULL DEFAULT '',
    variants               JSONB NOT NULL DEFAULT '[]'::jsonb,
    violations             JSONB NOT NULL DEFAULT '[]'::jsonb,
    requires_manual_review BOOLEAN NOT NULL DEFAULT false,
    final_facebook_url     TEXT NOT NULL DEFAULT '',
    approved_by            UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    approved_at            TIMESTAMPTZ,
    created_on             DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_posting_jobs_status ON public.posting_jobs (status);
CREATE INDEX IF NOT EXISTS idx_posting_jobs_offering ON public.posting_jobs (offering_id);

-- 2) Posting job assets (ordered/selected subset of canonical assets for one FB post)
CREATE TABLE IF NOT EXISTS public.posting_job_assets (
    id               BIGSERIAL PRIMARY KEY,
    job_id           TEXT NOT NULL REFERENCES public.posting_jobs(id) ON DELETE CASCADE,
    asset_id         UUID NOT NULL REFERENCES public.assets(id) ON DELETE CASCADE,
    display_order    INT NOT NULL DEFAULT 0,
    selected         BOOLEAN NOT NULL DEFAULT true,
    caption_override TEXT NOT NULL DEFAULT '',
    UNIQUE (job_id, asset_id)
);
CREATE INDEX IF NOT EXISTS idx_pja_order ON public.posting_job_assets (job_id, display_order);
CREATE INDEX IF NOT EXISTS idx_pja_selected ON public.posting_job_assets (job_id) WHERE selected = true;

-- 3) Atomic claim: oldest assigned job -> preparing, return the row
-- (LANGUAGE sql avoids dollar-quoting; the single UPDATE...RETURNING yields the row)
CREATE OR REPLACE FUNCTION public.claim_next_job(p_operator TEXT)
RETURNS public.posting_jobs LANGUAGE sql SECURITY DEFINER SET search_path = public AS $func$
  UPDATE public.posting_jobs
     SET status = 'preparing',
         operator = COALESCE(NULLIF(p_operator, ''), operator)
   WHERE id = (
     SELECT id FROM public.posting_jobs
      WHERE status = 'assigned'
      ORDER BY created_on, created_at
      FOR UPDATE SKIP LOCKED
      LIMIT 1
   )
   RETURNING *;
$func$;

-- Ã¢â€â‚¬Ã¢â€â‚¬ Row Level Security Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
ALTER TABLE public.posting_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posting_job_assets ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "staff crud posting_jobs" ON public.posting_jobs;
CREATE POLICY "staff crud posting_jobs" ON public.posting_jobs
    FOR ALL TO authenticated USING (public.is_staff()) WITH CHECK (public.is_staff());
DROP POLICY IF EXISTS "staff crud posting_job_assets" ON public.posting_job_assets;
CREATE POLICY "staff crud posting_job_assets" ON public.posting_job_assets
    FOR ALL TO authenticated USING (public.is_staff()) WITH CHECK (public.is_staff());

-- Ã¢â€â‚¬Ã¢â€â‚¬ Updated_at trigger Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬Ã¢â€â‚¬
DROP TRIGGER IF EXISTS set_updated_at ON public.posting_jobs;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON public.posting_jobs
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Ã¢â€â‚¬Ã¢â€â‚¬ activity_log access for desk staff (coexists with website 0101 admin policies) Ã¢â€â‚¬Ã¢â€â‚¬
-- Desk operators (role='staff') need to write per-job activity and read their own
-- posting_job-scoped rows. The website's admin-only policies remain (OR semantics).
DROP POLICY IF EXISTS "staff insert activity_log" ON public.activity_log;
CREATE POLICY "staff insert activity_log" ON public.activity_log
    FOR INSERT TO authenticated WITH CHECK (public.is_staff());
DROP POLICY IF EXISTS "staff read posting_job activity" ON public.activity_log;
CREATE POLICY "staff read posting_job activity" ON public.activity_log
    FOR SELECT TO authenticated USING (public.is_staff() AND entity = 'posting_job');

