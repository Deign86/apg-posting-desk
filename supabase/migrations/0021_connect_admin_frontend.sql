-- Migration 0021: Connect admin panel CRUD to public frontend reads
-- Ensures:
--   1. blog_posts has a public-read RLS policy (status='published')
--   2. job_openings has a public-read RLS policy (status='active')
--   3. offerings_public_read tightened to published + not-deleted only
--      (Staff still see all via the 'staff write offerings' for-all policy.)

-- ============ BLOG POSTS: public read (published only) ============
drop policy if exists "blog_posts_public_read" on public.blog_posts;
create policy "blog_posts_public_read" on public.blog_posts
  for select using (status = 'published');

-- ============ JOB OPENINGS: public read (active only) ============
drop policy if exists "job_openings_public_read" on public.job_openings;
create policy "job_openings_public_read" on public.job_openings
  for select using (status = 'active');

-- ============ OFFERINGS: tighten public read to published + not deleted ============
-- Authenticated staff still see everything via the 'staff write offerings' for-all policy.
drop policy if exists "offerings_public_read" on public.offerings;
create policy "offerings_public_read" on public.offerings
  for select using (is_published = true and deleted_at is null);
