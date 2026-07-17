-- Migration 0018: Chat Logs table for chatbot conversation logging
-- Promoted from scripts/migrate.sql into a proper migration file so that
-- supabase db push creates the table automatically.
-- The server's handleAiChat() writes conversation turns here (fire-and-forget).

create table if not exists public.chat_logs (
  id uuid primary key default gen_random_uuid(),
  session_id text,
  user_identifier text,
  role text not null check (role in ('user','assistant','system')),
  content text not null,
  model text,
  created_at timestamptz not null default now()
);

create index if not exists idx_chat_logs_created_at on public.chat_logs(created_at desc);
create index if not exists idx_chat_logs_session on public.chat_logs(session_id);

alter table public.chat_logs enable row level security;

-- Only admin/owner can read chat logs
create policy "chat_logs_admin_read" on public.chat_logs
  for select using (public.is_admin());
-- The server inserts via service-role client, which bypasses RLS.

