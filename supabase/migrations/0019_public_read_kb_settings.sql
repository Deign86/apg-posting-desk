-- Migration 0019: Public read policies for chatbot_kb and site_settings
-- These tables have no public SELECT policy, so the client (anon key) cannot
-- read them. The server context build uses the service-role key (bypasses RLS),
-- so the LLM itself works either way — but this blocks:
--   1. The keyword-fallback KB load in Chatbot.jsx (loadKB())
--   2. The admin Settings page display of site_settings

create policy "chatbot_kb_public_read" on public.chatbot_kb
  for select using (active = true);

create policy "site_settings_public_read" on public.site_settings
  for select using (true);
