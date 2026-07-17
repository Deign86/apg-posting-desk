-- Migration 0023: Facebook context (approved post summaries)
-- Stores approved Facebook page content summaries for AI chatbot retrieval.
-- Lower authority than live data and archived website context.

create table if not exists public.facebook_context (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  summary text not null,
  post_url text,
  author text,
  posted_at timestamptz,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_facebook_context_active on public.facebook_context(active);

alter table public.facebook_context enable row level security;

create policy "facebook_context_read_all" on public.facebook_context
  for select using (true);

create policy "facebook_context_write_admin" on public.facebook_context
  for all using (public.is_admin());
