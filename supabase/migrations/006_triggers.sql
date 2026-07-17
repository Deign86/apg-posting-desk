-- Migration 004: Triggers & Auto-Profile Creation
-- Creates automatic profile row when a new auth.users sign up

-- Handler function: creates a profile row for every new auth user
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, display_name, role)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data ->> 'display_name', NEW.email),
        'moderator'
    );
    -- Mirror initial role into raw_app_meta_data for client-side access
    UPDATE auth.users
    SET raw_app_meta_data = 
        COALESCE(raw_app_meta_data, '{}'::jsonb) || '{"role":"moderator"}'::jsonb
    WHERE id = NEW.id;
    RETURN NEW;
END;
$$;
-- Trigger: fires on auth.users INSERT
CREATE OR REPLACE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();
-- Function: sync profile role back to auth.users raw_app_meta_data
CREATE OR REPLACE FUNCTION public.sync_role_to_auth()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    UPDATE auth.users
    SET raw_app_meta_data = 
        COALESCE(raw_app_meta_data, '{}'::jsonb) || jsonb_build_object('role', NEW.role)
    WHERE id = NEW.id;
    RETURN NEW;
END;
$$;
-- Trigger: syncs when profiles.role changes
CREATE OR REPLACE TRIGGER on_profile_role_changed
    AFTER UPDATE OF role ON public.profiles
    FOR EACH ROW
    WHEN (OLD.role IS DISTINCT FROM NEW.role)
    EXECUTE FUNCTION public.sync_role_to_auth();
