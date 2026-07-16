-- 1000_desk_posted_log.sql -- APG Posting Desk: desk-owned reporting tables

-- Standalone helper functions (not provided by website project in this DB)
CREATE OR REPLACE FUNCTION public.is_staff()
RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.profiles
    WHERE id = auth.uid() AND role IN ('staff', 'admin')
  );
$$;

CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

-- Add offering_id column if missing
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'posted_log' AND column_name = 'offering_id'
  ) THEN
    ALTER TABLE public.posted_log ADD COLUMN offering_id BIGINT;
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS public.posted_log (
  id            BIGSERIAL PRIMARY KEY,
  posted_on     DATE NOT NULL,
  offering_id   BIGINT,
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
