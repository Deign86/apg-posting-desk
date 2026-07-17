-- Migration 008: Storage bucket RLS policies

CREATE POLICY "offerings_public_read" ON storage.objects
  FOR SELECT USING (bucket_id = 'offerings');
CREATE POLICY "offerings_admin_write" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'offerings' AND public.is_admin());
CREATE POLICY "offerings_admin_update" ON storage.objects
  FOR UPDATE USING (bucket_id = 'offerings' AND public.is_admin());
CREATE POLICY "offerings_admin_delete" ON storage.objects
  FOR DELETE USING (bucket_id = 'offerings' AND public.is_admin());
CREATE POLICY "blogs_public_read" ON storage.objects
  FOR SELECT USING (bucket_id = 'blogs');
CREATE POLICY "blogs_admin_write" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'blogs' AND public.is_admin());
CREATE POLICY "careers_public_read" ON storage.objects
  FOR SELECT USING (bucket_id = 'careers');
CREATE POLICY "careers_admin_write" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'careers' AND public.is_admin());
CREATE POLICY "admins_admin_read" ON storage.objects
  FOR SELECT USING (bucket_id = 'admins' AND public.is_admin());
CREATE POLICY "admins_admin_write" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'admins' AND public.is_admin());
CREATE POLICY "chat_public_read" ON storage.objects
  FOR SELECT USING (bucket_id = 'chat');
CREATE POLICY "chat_authenticated_upload" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'chat'
    AND auth.role() = 'authenticated'
    AND ((metadata->>'size')::bigint < 5242880)
    AND (metadata->>'mimetype' LIKE 'image/%')
  );
