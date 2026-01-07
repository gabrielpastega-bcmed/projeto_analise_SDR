-- Migration: Add OAuth fields and enhanced roles
-- Run with: psql -U user -d database -f 004_add_oauth_and_roles.sql

-- ============================================================
-- 1. Add OAuth fields to users table
-- ============================================================

-- OAuth provider (google, microsoft, etc.)
ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR(20) DEFAULT NULL;

-- OAuth ID from provider
ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_id VARCHAR(255) DEFAULT NULL;

-- Profile picture URL
ALTER TABLE users ADD COLUMN IF NOT EXISTS picture_url VARCHAR(500) DEFAULT NULL;

-- User status (pending, approved, rejected)
ALTER TABLE users ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'approved' NOT NULL;

-- ============================================================
-- 2. Create index for OAuth lookups
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_users_oauth ON users(oauth_provider, oauth_id);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);

-- ============================================================
-- 3. Make password_hash optional (OAuth users don't have passwords)
-- ============================================================

-- Note: In PostgreSQL, we need to drop and recreate the constraint
-- First, let's check if there are any NULL values that would cause issues
-- This is safe because existing users already have password_hash set

ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;

-- ============================================================
-- 4. Update existing role values to new format
-- ============================================================

-- Ensure existing superadmins become admins
UPDATE users SET role = 'admin' WHERE role = 'superadmin';

-- Ensure existing users stay as viewers (most restricted by default)
UPDATE users SET role = 'viewer' WHERE role = 'user';

-- ============================================================
-- 5. Add constraint for valid roles
-- ============================================================

-- Add check constraint for valid roles
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'users_role_check'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_role_check 
        CHECK (role IN ('admin', 'supervisor', 'analyst', 'viewer'));
    END IF;
END $$;

-- ============================================================
-- 6. Add constraint for valid status
-- ============================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'users_status_check'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_status_check 
        CHECK (status IN ('pending', 'approved', 'rejected'));
    END IF;
END $$;

-- ============================================================
-- Verification
-- ============================================================

-- Show updated table structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;
