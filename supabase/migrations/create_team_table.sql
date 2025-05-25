/*
  # Create team table

  1. New Tables
    - `team`
      - `id` (serial, primary key)
      - `name` (text, unique)
      - `created_at` (timestamptz)
  2. Security
    - Enable RLS on `team` table
    - Add policies for authenticated users to read, insert, update, and delete document types
  3. Initial Data
    - Insert default document types
*/

-- Create team table
CREATE TABLE IF NOT EXISTS team (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable Row Level Security
ALTER TABLE team ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Anyone can read document types"
  ON team
  FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Anyone can insert document types"
  ON team
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Anyone can update document types"
  ON team
  FOR UPDATE
  TO authenticated
  USING (true);

CREATE POLICY "Anyone can delete document types"
  ON team
  FOR DELETE
  TO authenticated
  USING (true);
