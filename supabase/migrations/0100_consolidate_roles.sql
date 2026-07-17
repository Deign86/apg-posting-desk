-- Migration 0100: Consolidate roles to admin/editor (remove owner/moderator)
-- SINGLE-LINE format: each SQL statement is on one line ending with ;
-- This ensures the apply script splits correctly.

-- 0. Drop all policies on profiles that depend on the role column
DROP POLICY IF EXISTS "profiles_self_update_non_role" ON public.profiles;
DROP POLICY IF EXISTS "profiles_admin_write" ON public.profiles;
DROP POLICY IF EXISTS "profiles_admin_read" ON public.profiles;
DROP POLICY IF EXISTS "profiles_self_read" ON public.profiles;
DROP POLICY IF EXISTS "staff read profiles" ON public.profiles;
DROP POLICY IF EXISTS "user read own profile" ON public.profiles;
DROP POLICY IF EXISTS "user update own profile" ON public.profiles;

-- 0b. Drop trigger on profiles that depends on the role column (syncs role to auth)
DROP TRIGGER IF EXISTS on_profile_role_changed ON public.profiles;

-- 0c. Drop default and check constraint before altering type
ALTER TABLE public.profiles ALTER COLUMN role DROP DEFAULT;
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS profiles_role_check;

-- 1. Convert column to text (safe if already text -- ALTER to same type is a no-op)
ALTER TABLE public.profiles ALTER COLUMN role TYPE TEXT USING role::TEXT;

-- 2. Set safe default for new users
ALTER TABLE public.profiles ALTER COLUMN role SET DEFAULT 'editor';

-- 3. Migrate existing role values: owner->admin, moderator->admin
UPDATE public.profiles SET role = 'admin' WHERE role IN ('owner', 'moderator');

-- 4. Migrate null roles to editor
UPDATE public.profiles SET role = 'editor' WHERE role IS NULL;

-- 5. Add new check constraint
ALTER TABLE public.profiles ADD CONSTRAINT profiles_role_check CHECK (role IN ('admin', 'editor'));

-- 6. Recreate is_admin() -- now only 'admin' role
CREATE OR REPLACE FUNCTION public.is_admin() RETURNS BOOLEAN LANGUAGE SQL STABLE SECURITY DEFINER SET search_path = public AS 'select exists(select 1 from public.profiles where id = auth.uid() and role = ''admin'' and active);';

-- 7. Recreate is_staff() -- now 'admin' or 'editor'
CREATE OR REPLACE FUNCTION public.is_staff() RETURNS BOOLEAN LANGUAGE SQL STABLE SECURITY DEFINER SET search_path = public AS 'select exists(select 1 from public.profiles where id = auth.uid() and role in (''admin'',''editor'') and active);';

-- 8. Drop legacy ENUM type (no longer needed -- column is now TEXT)
DROP TYPE IF EXISTS user_role;

-- 9. Recreate essential RLS policies on profiles
CREATE POLICY "user read own profile" ON public.profiles FOR SELECT TO authenticated USING (id = auth.uid());
CREATE POLICY "user update own profile" ON public.profiles FOR UPDATE TO authenticated USING (id = auth.uid()) WITH CHECK (id = auth.uid());
CREATE POLICY "staff read profiles" ON public.profiles FOR SELECT TO authenticated USING (public.is_staff());
CREATE POLICY "profiles_admin_write" ON public.profiles FOR ALL USING (public.is_admin());
CREATE POLICY "profiles_self_update_non_role" ON public.profiles FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id AND role = (SELECT role FROM public.profiles WHERE id = auth.uid()));

-- 10. Recreate trigger to sync role changes to auth.users metadata
CREATE OR REPLACE TRIGGER on_profile_role_changed AFTER UPDATE OF role ON public.profiles FOR EACH ROW WHEN (OLD.role IS DISTINCT FROM NEW.role) EXECUTE FUNCTION public.sync_role_to_auth();

