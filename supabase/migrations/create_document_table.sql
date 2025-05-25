/*
  # Create document table and storage bucket

  1. New Tables
    - `document`
      - `id` (serial, primary key)
      - `document_type` (text)
      - `document_url` (text)
      - `created_at` (timestamptz)
  2. Storage
    - Create documentation bucket for storing document files
  3. Security
    - Enable RLS on `document` table
    - Add policies for authenticated users to read, insert, and delete documents
*/

-- Create document table
CREATE TABLE IF NOT EXISTS document (
  id SERIAL PRIMARY KEY,
  document_type TEXT NOT NULL,
  document_url TEXT NOT NULL,
  document_text TEXT,
  team TEXT,
  sha TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE document ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Anyone can read documents"
  ON document
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Anyone can insert documents"
  ON document
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Anyone can delete documents"
  ON document
  FOR DELETE
  TO authenticated
  USING (true);

-- Create storage bucket for documentation
INSERT INTO storage.buckets (id, name, public)
VALUES ('documentation', 'documentation', true)
ON CONFLICT (id) DO NOTHING;

-- Set up storage policy to allow public access to documentation files
CREATE POLICY "Public Access"
  ON storage.objects
  FOR SELECT
  USING (bucket_id = 'documentation');

-- Allow authenticated users to upload files
CREATE POLICY "Authenticated users can upload files"
  ON storage.objects
  FOR INSERT
  TO authenticated
  WITH CHECK (bucket_id = 'documentation');

-- Allow authenticated users to delete files
CREATE POLICY "Authenticated users can delete files"
  ON storage.objects
  FOR DELETE
  TO authenticated
  USING (bucket_id = 'documentation');
