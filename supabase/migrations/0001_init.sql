-- 0001_init.sql — APG Posting Desk Supabase schema
-- Apply via: supabase db push --project-ref <ref>
-- Fallback: psql connection with the same SQL.

-- 1) Profiles (one row per auth user; carries the APG role)
create table if not exists public.profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  email        text not null,
  display_name text not null default '',
  role         text not null default 'user'
    check (role in ('admin','user')),
  created_at   timestamptz not null default now()
);

-- Auto-create a profile when a new auth user signs up
create or replace function public.handle_new_user()
returns trigger language plpgsql security definer as $$
begin
  insert into public.profiles (id, email, display_name, role)
  values (new.id, coalesce(new.email,''),
          coalesce(new.raw_user_meta_data->>'display_name', new.email, ''), 'user')
  on conflict (id) do nothing;
  return new;
end; $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

alter table public.profiles enable row level security;
create policy "users read own profile" on public.profiles
  for select using (auth.uid() = id);

-- 2) Property queue
create table if not exists public.property_queue (
  id            uuid primary key default gen_random_uuid(),
  property_name text not null,
  drive_url     text not null default '',
  status        text not null default 'pending'
    check (status in ('pending','processing','done','error')),
  assigned_at   timestamptz not null default now(),
  claimed_by    uuid references public.profiles(id),
  error         text not null default ''
);
create index if not exists property_queue_claim_idx
  on public.property_queue (status, assigned_at) where status = 'pending';
alter table public.property_queue enable row level security;
create policy "authenticated can read queue" on public.property_queue
  for select using (auth.role() = 'authenticated');

-- Atomic claim: oldest pending -> processing, return the row
create or replace function public.claim_next_queue_item(p_operator text)
returns public.property_queue language plpgsql security definer as $$
declare row public.property_queue;
begin
  update public.property_queue
     set status = 'processing',
         claimed_by = (
            select id from public.profiles
            where email = p_operator or id::text = p_operator
            limit 1
         )
   where id = (
     select id from public.property_queue
      where status = 'pending'
      order by assigned_at
      for update skip locked
      limit 1
   )
   returning * into row;
  return row;
end; $$;

-- 3) Operational jobs (mirrors OperationalJob fields in job_store.py)
create table if not exists public.jobs (
  id                     text primary key,          -- e.g. APG-0704-001
  property_name          text not null,
  assigned_by            text not null default '',
  operator               text not null default '',
  due_date               date,
  drive_url              text not null default '',
  status                 text not null default 'assigned',
  created_on             date not null default current_date,
  facebook_url           text not null default '',
  caption                text not null default '',
  caption_details        text not null default '',
  caption_document_name  text not null default '',
  images                 jsonb not null default '[]'::jsonb,
  variants               jsonb not null default '[]'::jsonb,
  violations             jsonb not null default '[]'::jsonb,
  requires_manual_review boolean not null default false,
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now()
);
create index if not exists jobs_status_idx on public.jobs (status);
alter table public.jobs enable row level security;
create policy "authenticated read jobs" on public.jobs
  for select using (auth.role() = 'authenticated');

-- 4) Job activity log
create table if not exists public.job_activity (
  id         bigserial primary key,
  job_id     text not null references public.jobs(id) on delete cascade,
  at         text not null default '',
  text       text not null default '',
  created_at timestamptz not null default now()
);
create index if not exists job_activity_job_idx on public.job_activity (job_id, id);
alter table public.job_activity enable row level security;
create policy "authenticated read activity" on public.job_activity
  for select using (auth.role() = 'authenticated');

-- 5) Posted log (replaces Google Sheets tracker + Google Docs daily report)
create table if not exists public.posted_log (
  id            bigserial primary key,
  posted_on     date not null,
  property_name text not null,
  post_url      text not null,
  status        text not null default 'Posted',
  posted_by     text not null default '',
  posted_at     timestamptz not null default now()
);
create index if not exists posted_log_on_idx on public.posted_log (posted_on);

-- 6) daily_report view (mirrors the old Google-Docs bullet format)
create or replace view public.daily_report as
  select posted_on,
         string_agg(
           E'\n\u2022 ' || property_name || ' - Posted at '
             || to_char(posted_at at time zone 'Asia/Manila','HH24:MI')
             || E'\n  Link: ' || post_url,
           E'\n' order by posted_at
         ) as report_text
  from public.posted_log
  group by posted_on
  order by posted_on desc;
