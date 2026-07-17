-- 0090_fix_security_and_triggers.sql
-- Idempotent fixes applied on top of 0001_init.sql (already applied on remote).
-- Fixes: (1) RLS on profiles, (2) is_staff role check, (3) updated_at triggers, (4) security definer on helpers.

-- 1. Enable RLS on profiles (omitted in original 0001 migration)
alter table public.profiles enable row level security;

-- 2. is_admin() with security definer + pinned search_path
create or replace function public.is_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select exists(select 1 from public.profiles where id = auth.uid() and role in ('owner','admin') and active);
$$;

-- 3. is_staff() with role check (owner/admin/editor) + security definer + pinned search_path
create or replace function public.is_staff()
returns boolean language sql stable security definer set search_path = public as $$
  select exists(select 1 from public.profiles where id = auth.uid() and role in ('owner','admin','editor') and active);
$$;

-- 4. updated_at auto-trigger for all content tables
create or replace function public.handle_updated_at()
returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end; $$;

do $$
declare t text;
begin
  foreach t in array array['offerings','inquiries','blog_posts','job_openings','chatbot_kb','site_settings']
  loop
    execute format('drop trigger if exists set_updated_at on public.%I', t);
    execute format('create trigger set_updated_at before update on public.%I for each row execute function public.handle_updated_at()', t);
  end loop;
end $$;
