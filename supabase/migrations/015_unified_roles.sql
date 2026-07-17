-- Migration 015: Unified role set for both repos (owner|admin|editor|staff|viewer)
-- Backward compatible: keeps the website's admin/editor roles and ADDS staff + viewer
-- so apg-posting-desk operators can be 'staff' (satisfies is_staff() RLS) without admin.
-- Owner: apg-website (profiles is a shared table). See SHARED_ASSET_ARCHITECTURE.md §4.10.

-- 1. Widen the role check constraint
alter table public.profiles drop constraint if exists profiles_role_check;
alter table public.profiles add constraint profiles_role_check
  check (role in ('owner','admin','editor','staff','viewer'));

-- 2. is_admin() — owner or admin (unchanged intent; now explicit set)
create or replace function public.is_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select exists(select 1 from public.profiles where id = auth.uid()
                and role in ('owner','admin') and coalesce(active, true));
$$;

-- 3. is_staff() — owner, admin, editor, OR staff (desk operators). viewer is read-only internal.
create or replace function public.is_staff()
returns boolean language sql stable security definer set search_path = public as $$
  select exists(select 1 from public.profiles where id = auth.uid()
                and role in ('owner','admin','editor','staff') and coalesce(active, true));
$$;

-- 4. is_viewer() — any authenticated internal role (owner/admin/editor/staff/viewer)
create or replace function public.is_viewer()
returns boolean language sql stable security definer set search_path = public as $$
  select exists(select 1 from public.profiles where id = auth.uid()
                and role in ('owner','admin','editor','staff','viewer') and coalesce(active, true));
$$;

-- 5. Keep the default sane for new sign-ups (website content editors)
alter table public.profiles alter column role set default 'editor';

-- Note: desk operator accounts should be created with role='staff' via the desk's
-- SupabaseTokenVerifier.create_user (or the website admin invite flow).
