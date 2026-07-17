-- Migration 0022: Archived website context (extracted from .old_site/)
-- Stores approved summaries from the old Alpha Premier website for AI retrieval.
-- Lower priority than live chatbot_kb facts; used when old-site info is relevant.

create table if not exists public.archived_context (
  id uuid primary key default gen_random_uuid(),
  section text not null,
  title text not null,
  summary text not null,
  source_url text,
  priority int not null default 0,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_archived_context_active on public.archived_context(active);
create index if not exists idx_archived_context_section on public.archived_context(section);

alter table public.archived_context enable row level security;

create policy "archived_context_read_all" on public.archived_context
  for select using (true);

create policy "archived_context_write_admin" on public.archived_context
  for all using (public.is_admin());
