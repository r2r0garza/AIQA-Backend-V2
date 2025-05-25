/*
  # Create document_type table

  1. New Tables
    - `document_type`
      - `id` (serial, primary key)
      - `name` (text, unique)
      - `category` (text)
      - `created_at` (timestamptz)
  2. Security
    - Enable RLS on `document_type` table
    - Add policies for authenticated users to read, insert, update, and delete document types
  3. Initial Data
    - Insert default document types
*/

-- Create document_type table
CREATE TABLE IF NOT EXISTS document_type (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE document_type ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Anyone can read document types"
  ON document_type
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Anyone can insert document types"
  ON document_type
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Anyone can update document types"
  ON document_type
  FOR UPDATE
  TO authenticated
  USING (true);

CREATE POLICY "Anyone can delete document types"
  ON document_type
  FOR DELETE
  TO authenticated
  USING (true);

-- Insert default document types
INSERT INTO document_type (name, category)
VALUES 
  ('User Story Creator Template', 'agent'),
  ('Acceptance Criteria Creator Template', 'agent'),
  ('Test Cases Generator Template', 'agent'),
  ('Automation Script Generator Template', 'agent'),
  ('Test Data Generator Template', 'agent'),
  ('HIPAA Documentation', 'general'),
  ('ISTQB Documentation', 'general'),
  ('Project Guidelines', 'general'),
  ('API Documentation', 'general'),
  ('Technical Specifications', 'general'),
  ('User Manuals', 'general'),
  ('Requirements Documentation', 'general')
ON CONFLICT (name) DO NOTHING;
