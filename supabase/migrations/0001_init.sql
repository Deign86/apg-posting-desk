-- supabase/migrations/0001_init.sql — Alpha Premier Group

-- ============ OFFERINGS ============
create table if not exists public.offerings (
  id uuid primary key default gen_random_uuid(),
  title text, location text, property_type text, status text,
  price numeric, price_unit text default '₱',
  floor_area text, lot_area text, description text,
  email text, phone text, images jsonb default '[]'::jsonb,
  slug text, beds int, baths int, garage int,
  featured boolean not null default false,
  is_published boolean not null default true,
  deleted_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ============ PROFILES ============
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text, full_name text, avatar_url text,
  role text not null default 'editor' check (role in ('owner','admin','editor')),
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create or replace function public.handle_new_user()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  insert into public.profiles (id, email, full_name)
  values (new.id, new.email, coalesce(new.raw_user_meta_data->>'full_name', new.email))
  on conflict (id) do nothing;
  return new;
end; $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- ============ INQUIRIES ============
create table if not exists public.inquiries (
  id uuid primary key default gen_random_uuid(),
  ticket text unique, name text not null, email text not null,
  phone text, subject text, message text,
  source text default 'contact_form', property_id text,
  status text not null default 'new' check (status in ('new','contacted','qualified','won','lost','archived')),
  assigned_to uuid references public.profiles(id) on delete set null,
  notes text, lead_score int default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ============ BLOG POSTS ============
create table if not exists public.blog_posts (
  id uuid primary key default gen_random_uuid(),
  slug text unique not null, title text not null,
  excerpt text, content text, category text,
  cover_image text, author text,
  status text not null default 'draft' check (status in ('draft','published','archived')),
  published_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ============ JOB OPENINGS ============
create table if not exists public.job_openings (
  id uuid primary key default gen_random_uuid(),
  title text not null, location text,
  type text, tag text, description text,
  status text not null default 'active' check (status in ('active','closed','draft')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ============ CHATBOT KB ============
create table if not exists public.chatbot_kb (
  id uuid primary key default gen_random_uuid(),
  trigger text not null, answer text not null,
  keywords text, priority int default 0,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ============ ACTIVITY LOG ============
create table if not exists public.activity_log (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.profiles(id) on delete set null,
  action text not null, entity text, entity_id text,
  meta jsonb,
  created_at timestamptz not null default now()
);

-- ============ SITE SETTINGS ============
create table if not exists public.site_settings (
  key text primary key,
  value text,
  updated_by uuid references public.profiles(id) on delete set null,
  updated_at timestamptz not null default now()
);

-- ============ updated_at trigger for all content tables ============
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

-- ============ HELPER FUNCTIONS ============
create or replace function public.is_admin()
returns boolean language sql stable security definer set search_path = public as $$
  select exists(select 1 from public.profiles where id = auth.uid() and role in ('owner','admin') and active);
$$;

create or replace function public.is_staff()
returns boolean language sql stable security definer set search_path = public as $$
  select exists(select 1 from public.profiles where id = auth.uid() and role in ('owner','admin','editor') and active);
$$;

-- ============ ROW-LEVEL SECURITY ============
alter table public.offerings enable row level security;
alter table public.inquiries enable row level security;
alter table public.blog_posts enable row level security;
alter table public.job_openings enable row level security;
alter table public.chatbot_kb enable row level security;
alter table public.activity_log enable row level security;
alter table public.site_settings enable row level security;
alter table public.profiles enable row level security;

-- PUBLIC READ (anyone)
drop policy if exists "public read offerings" on public.offerings;
create policy "public read offerings" on public.offerings for select using (is_published = true and deleted_at is null);
drop policy if exists "public read blogs" on public.blog_posts;
create policy "public read blogs" on public.blog_posts for select using (status = 'published');
drop policy if exists "public read jobs" on public.job_openings;
create policy "public read jobs" on public.job_openings for select using (status = 'active');
drop policy if exists "public read kb" on public.chatbot_kb;
create policy "public read kb" on public.chatbot_kb for select using (active = true);
drop policy if exists "public read settings" on public.site_settings;
create policy "public read settings" on public.site_settings for select using (true);

-- STAFF READ (authenticated + active profile)
drop policy if exists "staff read offerings" on public.offerings;
create policy "staff read offerings" on public.offerings for select to authenticated using (public.is_staff());
drop policy if exists "staff read inquiries" on public.inquiries;
create policy "staff read inquiries" on public.inquiries for select to authenticated using (public.is_staff());
drop policy if exists "staff read blogs" on public.blog_posts;
create policy "staff read blogs" on public.blog_posts for select to authenticated using (public.is_staff());
drop policy if exists "staff read jobs" on public.job_openings;
create policy "staff read jobs" on public.job_openings for select to authenticated using (public.is_staff());
drop policy if exists "staff read kb" on public.chatbot_kb;
create policy "staff read kb" on public.chatbot_kb for select to authenticated using (public.is_staff());
drop policy if exists "staff read activity" on public.activity_log;
create policy "staff read activity" on public.activity_log for select to authenticated using (public.is_staff());
drop policy if exists "staff read profiles" on public.profiles;
create policy "staff read profiles" on public.profiles for select to authenticated using (public.is_staff());
drop policy if exists "staff read settings" on public.site_settings;
create policy "staff read settings" on public.site_settings for select to authenticated using (public.is_staff());

-- STAFF WRITE
drop policy if exists "staff write offerings" on public.offerings;
create policy "staff write offerings" on public.offerings for all to authenticated using (public.is_staff()) with check (public.is_staff());
drop policy if exists "staff write inquiries" on public.inquiries;
create policy "staff write inquiries" on public.inquiries for all to authenticated using (public.is_staff()) with check (public.is_staff());
drop policy if exists "staff write blogs" on public.blog_posts;
create policy "staff write blogs" on public.blog_posts for all to authenticated using (public.is_staff()) with check (public.is_staff());
drop policy if exists "staff write jobs" on public.job_openings;
create policy "staff write jobs" on public.job_openings for all to authenticated using (public.is_staff()) with check (public.is_staff());
drop policy if exists "staff write kb" on public.chatbot_kb;
create policy "staff write kb" on public.chatbot_kb for all to authenticated using (public.is_staff()) with check (public.is_staff());
drop policy if exists "staff write activity" on public.activity_log;
create policy "staff write activity" on public.activity_log for insert to authenticated with check (public.is_staff());
drop policy if exists "staff write settings" on public.site_settings;
create policy "staff write settings" on public.site_settings for all to authenticated using (public.is_staff()) with check (public.is_staff());

-- PROFILES: self-read/update
drop policy if exists "user read own profile" on public.profiles;
create policy "user read own profile" on public.profiles for select to authenticated using (id = auth.uid());
drop policy if exists "user update own profile" on public.profiles;
create policy "user update own profile" on public.profiles for update to authenticated using (id = auth.uid()) with check (id = auth.uid());

-- STORAGE buckets
insert into storage.buckets (id, name, public) values ('listing-images', 'listing-images', true) on conflict (id) do nothing;
insert into storage.buckets (id, name, public) values ('blog-images', 'blog-images', true) on conflict (id) do nothing;

-- STORAGE policies
drop policy if exists "public read listing images" on storage.objects;
create policy "public read listing images" on storage.objects for select using (bucket_id = 'listing-images');
drop policy if exists "staff write listing images" on storage.objects;
create policy "staff write listing images" on storage.objects for insert to authenticated with check (bucket_id = 'listing-images' and public.is_staff());
drop policy if exists "staff delete listing images" on storage.objects;
create policy "staff delete listing images" on storage.objects for delete to authenticated using (bucket_id = 'listing-images' and public.is_staff());
drop policy if exists "public read blog images" on storage.objects;
create policy "public read blog images" on storage.objects for select using (bucket_id = 'blog-images');
drop policy if exists "staff write blog images" on storage.objects;
create policy "staff write blog images" on storage.objects for insert to authenticated with check (bucket_id = 'blog-images' and public.is_staff());
drop policy if exists "staff delete blog images" on storage.objects;
create policy "staff delete blog images" on storage.objects for delete to authenticated using (bucket_id = 'blog-images' and public.is_staff());
