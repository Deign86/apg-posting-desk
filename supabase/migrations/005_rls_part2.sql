-- Migration 003: RLS Policies (Part 2 — Services, Careers, Blogs, Inquiries, Chat)

-- ============ SERVICES ============
CREATE POLICY "services_public_read" ON public.services
    FOR SELECT USING (true);
CREATE POLICY "services_admin_write" ON public.services
    FOR ALL USING (public.is_admin());
-- ============ CAREERS ============
CREATE POLICY "careers_public_read" ON public.careers
    FOR SELECT USING (true);
CREATE POLICY "careers_admin_write" ON public.careers
    FOR ALL USING (public.is_admin());
-- ============ BLOGS ============
CREATE POLICY "blogs_public_read" ON public.blogs
    FOR SELECT USING (true);
CREATE POLICY "blogs_admin_write" ON public.blogs
    FOR ALL USING (public.is_admin());
-- ============ INQUIRIES ============
CREATE POLICY "inquiries_public_create" ON public.inquiries
    FOR INSERT WITH CHECK (
        name IS NOT NULL AND length(name) > 0 AND length(name) <= 200
        AND (email IS NULL OR email ~ '^[^@]+@[^@]+\.[^@]+$')
        AND (message IS NULL OR (length(message) > 0 AND length(message) <= 5000))
    );
CREATE POLICY "inquiries_admin_select" ON public.inquiries
    FOR SELECT USING (public.is_admin());
CREATE POLICY "inquiries_admin_update" ON public.inquiries
    FOR UPDATE USING (public.is_admin());
CREATE POLICY "inquiries_admin_delete" ON public.inquiries
    FOR DELETE USING (public.is_admin());
-- ============ CHAT SESSIONS ============
CREATE POLICY "chat_sessions_admin_all" ON public.chat_sessions
    FOR ALL USING (public.is_admin());
CREATE POLICY "chat_sessions_visitor_read" ON public.chat_sessions
    FOR SELECT USING (
        auth.uid() IS NULL
        AND visitor_session_token = current_setting('app.visitor_session_token', true)
    );
CREATE POLICY "chat_sessions_visitor_create" ON public.chat_sessions
    FOR INSERT WITH CHECK (
        visitor_name IS NOT NULL AND length(visitor_name) <= 100
    );
-- ============ CHAT MESSAGES ============
CREATE POLICY "chat_messages_admin_all" ON public.chat_messages
    FOR ALL USING (public.is_admin());
CREATE POLICY "chat_messages_visitor_read" ON public.chat_messages
    FOR SELECT USING (
        auth.uid() IS NULL
        AND EXISTS (
            SELECT 1 FROM public.chat_sessions
            WHERE id = chat_messages.session_id
            AND visitor_session_token = current_setting('app.visitor_session_token', true)
        )
    );
CREATE POLICY "chat_messages_visitor_create" ON public.chat_messages
    FOR INSERT WITH CHECK (
        message IS NOT NULL AND length(message) > 0 AND length(message) <= 5000
        AND sender_type IN ('visitor', 'admin')
    );
