-- Migration 020: Create apg-private bucket and public-read policy
-- Repo A (APG Prototype / posting desk) uploads property assets here.
-- This makes the same images readable by Repo B (Original APG Website) public pages.

INSERT INTO storage.buckets (id, name, public, avif_autodetection, file_size_limit, allowed_mime_types)
VALUES ('apg-private', 'apg-private', true, false, null, null)
ON CONFLICT (id) DO NOTHING;

-- Public can read all objects in apg-private
CREATE POLICY "apg_private_public_read"
ON storage.objects
FOR SELECT
USING (bucket_id = 'apg-private');
