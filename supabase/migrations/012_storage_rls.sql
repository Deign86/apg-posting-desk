-- Migration 012: Storage RLS policies for apg-public and apg-private buckets
-- Requires: buckets created in 011_asset_layer.sql

-- ============ apg-public (public read / staff write) ============
-- Public: anyone (including unauthenticated) can read
drop policy if exists "apg-public public read" on storage.objects;
create policy "apg-public public read"
  on storage.objects for select
  using (bucket_id = 'apg-public');

-- Staff: authenticated staff can insert, update, delete
drop policy if exists "apg-public staff write" on storage.objects;
create policy "apg-public staff write"
  on storage.objects for insert
  to authenticated
  with check (bucket_id = 'apg-public' and public.is_staff());

drop policy if exists "apg-public staff update" on storage.objects;
create policy "apg-public staff update"
  on storage.objects for update
  to authenticated
  using (bucket_id = 'apg-public' and public.is_staff());

drop policy if exists "apg-public staff delete" on storage.objects;
create policy "apg-public staff delete"
  on storage.objects for delete
  to authenticated
  using (bucket_id = 'apg-public' and public.is_staff());

-- ============ apg-private (staff-only read/write/delete) ============
-- Private: no public read at all — all access requires staff auth
drop policy if exists "apg-private staff read" on storage.objects;
create policy "apg-private staff read"
  on storage.objects for select
  to authenticated
  using (bucket_id = 'apg-private' and public.is_staff());

drop policy if exists "apg-private staff write" on storage.objects;
create policy "apg-private staff write"
  on storage.objects for insert
  to authenticated
  with check (bucket_id = 'apg-private' and public.is_staff());

drop policy if exists "apg-private staff update" on storage.objects;
create policy "apg-private staff update"
  on storage.objects for update
  to authenticated
  using (bucket_id = 'apg-private' and public.is_staff());

drop policy if exists "apg-private staff delete" on storage.objects;
create policy "apg-private staff delete"
  on storage.objects for delete
  to authenticated
  using (bucket_id = 'apg-private' and public.is_staff());
