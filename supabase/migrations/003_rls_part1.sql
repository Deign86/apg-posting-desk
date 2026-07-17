-- Migration 003: RLS Policies (Part 1 — Core tables)
-- Mirrors firestore.rules from both Vite and Next.js frontends

-- ============ SECURITY HELPER FUNCTIONS ============
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean
LANGUAGE sql
SECURITY DEFINER
SET search_path = ''
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.profiles
        WHERE id = auth.uid()
        AND role IN ('owner', 'admin')
    );
$$;
CREATE OR REPLACE FUNCTION public.is_signed_in()
RETURNS boolean
LANGUAGE sql
AS $$
    SELECT auth.uid() IS NOT NULL;
$$;
-- ============ PROFILES ============
CREATE POLICY "profiles_self_read" ON public.profiles
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY "profiles_admin_read" ON public.profiles
    FOR SELECT USING (public.is_admin());
CREATE POLICY "profiles_admin_write" ON public.profiles
    FOR ALL USING (public.is_admin());
CREATE POLICY "profiles_self_update_non_role" ON public.profiles
    FOR UPDATE USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id AND role = (SELECT role FROM public.profiles WHERE id = auth.uid()));
-- ============ OFFERINGS ============
CREATE POLICY "offerings_public_read" ON public.offerings
    FOR SELECT USING (true);
CREATE POLICY "offerings_admin_insert" ON public.offerings
    FOR INSERT WITH CHECK (public.is_admin());
CREATE POLICY "offerings_admin_update" ON public.offerings
    FOR UPDATE USING (public.is_admin());
CREATE POLICY "offerings_admin_delete" ON public.offerings
    FOR DELETE USING (public.is_admin());
-- ============ OFFERING COMMENTS ============
CREATE POLICY "ocomments_public_read" ON public.offering_comments
    FOR SELECT USING (true);
CREATE POLICY "ocomments_public_create" ON public.offering_comments
    FOR INSERT WITH CHECK (
        user_name IS NOT NULL AND length(user_name) > 0 AND length(user_name) <= 100
        AND comment_text IS NOT NULL AND length(comment_text) > 0 AND length(comment_text) <= 2000
        AND offering_id IS NOT NULL
    );
CREATE POLICY "ocomments_admin_update" ON public.offering_comments
    FOR UPDATE USING (public.is_admin());
CREATE POLICY "ocomments_admin_delete" ON public.offering_comments
    FOR DELETE USING (public.is_admin());
-- ============ OFFERING RATINGS ============
CREATE POLICY "oratings_public_read" ON public.offering_ratings
    FOR SELECT USING (true);
CREATE POLICY "oratings_public_create" ON public.offering_ratings
    FOR INSERT WITH CHECK (rating >= 1 AND rating <= 5 AND offering_id IS NOT NULL);
CREATE POLICY "oratings_admin_update" ON public.offering_ratings
    FOR UPDATE USING (public.is_admin());
CREATE POLICY "oratings_no_delete" ON public.offering_ratings
    FOR DELETE USING (false);
-- ============ OFFERING REACTIONS ============
CREATE POLICY "oreactions_public_read" ON public.offering_reactions
    FOR SELECT USING (true);
CREATE POLICY "oreactions_public_create" ON public.offering_reactions
    FOR INSERT WITH CHECK (reaction_type = 'like' AND offering_id IS NOT NULL);
CREATE POLICY "oreactions_no_update" ON public.offering_reactions
    FOR UPDATE USING (false);
CREATE POLICY "oreactions_public_delete" ON public.offering_reactions
    FOR DELETE USING (true);
