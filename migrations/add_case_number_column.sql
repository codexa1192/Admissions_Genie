-- Add case_number column to admissions table (PHI-FREE mode)
-- This replaces patient_initials which contained PHI

-- Add case_number column
ALTER TABLE admissions ADD COLUMN IF NOT EXISTS case_number TEXT;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_admissions_case_number ON admissions(case_number);

-- Verify column was added
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'admissions'
  AND column_name = 'case_number';
