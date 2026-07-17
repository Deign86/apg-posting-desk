-- Migration 007: Create storage buckets
INSERT INTO storage.buckets (id, name, public, avif_autodetection, file_size_limit, allowed_mime_types)
VALUES
  ('offerings', 'offerings', true, false, null, null),
  ('blogs', 'blogs', true, false, null, null),
  ('careers', 'careers', true, false, null, null),
  ('admins', 'admins', false, false, null, null),
  ('chat', 'chat', false, false, null, null)
ON CONFLICT (id) DO NOTHING;
