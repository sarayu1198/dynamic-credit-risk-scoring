-- Run once against the existing credit_risk_db database.
-- Adds a one-to-one link between a borrower profile and its login account.

ALTER TABLE borrowers
    ADD COLUMN IF NOT EXISTS user_id BIGINT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'borrowers_user_id_fkey'
          AND conrelid = 'borrowers'::regclass
    ) THEN
        ALTER TABLE borrowers
            ADD CONSTRAINT borrowers_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(user_id)
            ON DELETE SET NULL;
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS borrowers_user_id_unique
    ON borrowers(user_id)
    WHERE user_id IS NOT NULL;

-- Replace the old role CHECK constraint (which allowed only admin/analyst).
DO $$
DECLARE
    role_check_name TEXT;
BEGIN
    FOR role_check_name IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'users'::regclass
          AND contype = 'c'
          AND pg_get_constraintdef(oid) ILIKE '%role%'
    LOOP
        EXECUTE format('ALTER TABLE users DROP CONSTRAINT %I', role_check_name);
    END LOOP;
END $$;

ALTER TABLE users
    ADD CONSTRAINT users_role_check
    CHECK (role IN ('admin', 'analyst', 'borrower'));

-- Existing user rows and borrower profiles are intentionally left unchanged.
