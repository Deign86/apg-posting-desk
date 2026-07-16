-- 1001_desk_posting_jobs.sql -- Desk-owned posting workflow tables for apg-posting-desk

-- 1) Posting jobs
CREATE TABLE IF NOT EXISTS public.posting_jobs (
    id                     TEXT PRIMARY KEY,
    offering_id            BIGINT,
    property_name          TEXT NOT NULL DEFAULT '',
    assigned_by            TEXT NOT NULL DEFAULT '',
    operator               TEXT NOT NULL DEFAULT '',
    due_date               DATE,
    status                 TEXT NOT NULL DEFAULT 'assigned'
        CHECK (status IN ('assigned','preparing','ready','posted','cancelled')),
    caption                TEXT NOT NULL DEFAULT '',
    selected_caption       TEXT NOT NULL DEFAULT '',
    caption_details        TEXT NOT NULL DEFAULT '',
    caption_document_name  TEXT NOT NULL DEFAULT '',
    images                 JSONB NOT NULL DEFAULT '[]'::jsonb,
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

-- 2) Posting job assets (asset_id UUID without FK -- assets in website project)
CREATE TABLE IF NOT EXISTS public.posting_job_assets (
    id               BIGSERIAL PRIMARY KEY,
    job_id           TEXT NOT NULL REFERENCES public.posting_jobs(id) ON DELETE CASCADE,
    asset_id         UUID NOT NULL,
    display_order    INT NOT NULL DEFAULT 0,
    selected         BOOLEAN NOT NULL DEFAULT true,
    caption_override TEXT NOT NULL DEFAULT '',
    UNIQUE (job_id, asset_id)
);
CREATE INDEX IF NOT EXISTS idx_pja_order ON public.posting_job_assets (job_id, display_order);
CREATE INDEX IF NOT EXISTS idx_pja_selected ON public.posting_job_assets (job_id) WHERE selected = true;

-- 3) Atomic claim: oldest assigned job -> preparing
CREATE OR REPLACE FUNCTION public.claim_next_job(p_operator TEXT)
RETURNS public.posting_jobs LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
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
$$;

-- 4) Row Level Security
ALTER TABLE public.posting_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.posting_job_assets ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "staff crud posting_jobs" ON public.posting_jobs;
CREATE POLICY "staff crud posting_jobs" ON public.posting_jobs
    FOR ALL TO authenticated USING (public.is_staff()) WITH CHECK (public.is_staff());
DROP POLICY IF EXISTS "staff crud posting_job_assets" ON public.posting_job_assets;
CREATE POLICY "staff crud posting_job_assets" ON public.posting_job_assets
    FOR ALL TO authenticated USING (public.is_staff()) WITH CHECK (public.is_staff());

-- 5) Updated_at trigger
DROP TRIGGER IF EXISTS set_updated_at ON public.posting_jobs;
CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON public.posting_jobs
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();
