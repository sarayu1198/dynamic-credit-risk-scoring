
-- ==========================================
-- DYNAMIC CREDIT RISK SCORING
-- PostgreSQL Database Schema
-- ==========================================

-- 1. USER ACCOUNTS
CREATE TABLE users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'analyst'
        CHECK (role IN ('admin', 'analyst')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX users_email_lower_unique
    ON users (LOWER(email));


-- 2. BORROWER PROFILES
CREATE TABLE borrowers (
    borrower_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    managed_by BIGINT NOT NULL
        REFERENCES users(user_id) ON DELETE RESTRICT,
    full_name VARCHAR(150) NOT NULL,
    external_reference VARCHAR(50) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- 3. LOANS
CREATE TABLE loans (
    loan_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    borrower_id BIGINT NOT NULL
        REFERENCES borrowers(borrower_id) ON DELETE RESTRICT,
    principal_amount NUMERIC(14, 2) NOT NULL
        CHECK (principal_amount > 0),
    interest_rate NUMERIC(6, 3)
        CHECK (interest_rate >= 0 AND interest_rate <= 100),
    issue_date DATE NOT NULL,
    maturity_date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'closed', 'defaulted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (maturity_date IS NULL OR maturity_date >= issue_date)
);


-- 4. INDIVIDUAL LOAN PAYMENTS
CREATE TABLE payment_history (
    payment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    loan_id BIGINT NOT NULL
        REFERENCES loans(loan_id) ON DELETE RESTRICT,
    due_date DATE NOT NULL,
    paid_date DATE,
    amount_due NUMERIC(14, 2) NOT NULL
        CHECK (amount_due >= 0),
    amount_paid NUMERIC(14, 2) NOT NULL DEFAULT 0
        CHECK (amount_paid >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'paid', 'partial', 'late')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- 5. HISTORICAL RISK ASSESSMENTS
CREATE TABLE risk_assessments (
    assessment_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    borrower_id BIGINT NOT NULL
        REFERENCES borrowers(borrower_id) ON DELETE RESTRICT,
    default_probability NUMERIC(7, 6) NOT NULL
        CHECK (default_probability >= 0 AND default_probability <= 1),
    risk_score SMALLINT NOT NULL
        CHECK (risk_score BETWEEN 0 AND 100),
    risk_category VARCHAR(20) NOT NULL
        CHECK (risk_category IN ('lower', 'moderate', 'higher')),
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    threshold_used NUMERIC(5, 4)
        CHECK (threshold_used >= 0 AND threshold_used <= 1),
    snapshot_id VARCHAR(100),
    assessed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ==========================================
-- INDEXES FOR COMMON QUERIES
-- ==========================================

CREATE INDEX idx_borrowers_managed_by
    ON borrowers(managed_by);

CREATE INDEX idx_loans_borrower
    ON loans(borrower_id);

CREATE INDEX idx_payments_loan_due_date
    ON payment_history(loan_id, due_date);

CREATE INDEX idx_assessments_borrower_date
    ON risk_assessments(borrower_id, assessed_at DESC);


-- ==========================================
-- AUTOMATIC UPDATED_AT TIMESTAMPS
-- ==========================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_borrowers_updated_at
BEFORE UPDATE ON borrowers
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_loans_updated_at
BEFORE UPDATE ON loans
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
