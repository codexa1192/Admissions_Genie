-- Add missing security columns to users table
-- These columns are needed for enhanced login security features

-- Add failed_login_attempts column
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0;

-- Add locked_until column
ALTER TABLE users ADD COLUMN IF NOT EXISTS locked_until TIMESTAMP;

-- Add last_failed_login column
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_failed_login TIMESTAMP;

-- Update existing users to have default values
UPDATE users SET failed_login_attempts = 0 WHERE failed_login_attempts IS NULL;

-- Verify columns were added
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'users'
  AND column_name IN ('failed_login_attempts', 'locked_until', 'last_failed_login')
ORDER BY column_name;
