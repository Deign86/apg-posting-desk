-- Migration 0101: Tighten admin RLS policies (defense-in-depth)
-- Moves inquiries, activity_log, and site_settings from is_staff() to is_admin()
-- Content tables (offerings, blogs, jobs, kb) stay is_staff() for editors

-- INQUIRIES: admin-only for staff operations (public create stays separate via inquiries_public_create)
drop policy if exists "staff write inquiries" on public.inquiries;
create policy "staff write inquiries" on public.inquiries
  for all to authenticated using (public.is_admin()) with check (public.is_admin());

-- ACTIVITY LOG: admin-only read/write
drop policy if exists "staff read activity" on public.activity_log;
create policy "staff read activity" on public.activity_log
  for select to authenticated using (public.is_admin());

drop policy if exists "staff write activity" on public.activity_log;
create policy "staff write activity" on public.activity_log
  for insert to authenticated with check (public.is_admin());

-- SITE SETTINGS: admin-only (read + write)
drop policy if exists "staff read settings" on public.site_settings;
create policy "staff read settings" on public.site_settings
  for select to authenticated using (public.is_admin());

drop policy if exists "staff write settings" on public.site_settings;
create policy "staff write settings" on public.site_settings
  for all to authenticated using (public.is_admin()) with check (public.is_admin());