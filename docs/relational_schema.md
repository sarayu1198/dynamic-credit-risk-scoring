# Relational Schema — Dynamic Credit Risk Scoring

## 1. Overview

The Dynamic Credit Risk Scoring system uses PostgreSQL to store user accounts, borrower profiles, loans, payment history, and historical risk assessments. The schema enforces entity integrity, referential integrity, domain constraints, and data consistency through primary keys, foreign keys, unique indexes, CHECK constraints, and triggers.

## 2. Relational Schema Notation

**USERS**(
- `user_id` **PK**
- `full_name`
- `email`
- `password_hash`
- `role`
- `created_at`
)

**BORROWERS**(
- `borrower_id` **PK**
- `managed_by` **FK** → USERS(`user_id`)
- `full_name`
- `external_reference` **UNIQUE**
- `created_at`
- `updated_at`
)

**LOANS**(
- `loan_id` **PK**
- `borrower_id` **FK** → BORROWERS(`borrower_id`)
- `principal_amount`
- `interest_rate`
- `issue_date`
- `maturity_date`
- `status`
- `created_at`
- `updated_at`
)

**PAYMENT_HISTORY**(
- `payment_id` **PK**
- `loan_id` **FK** → LOANS(`loan_id`)
- `due_date`
- `paid_date`
- `amount_due`
- `amount_paid`
- `status`
- `created_at`
)

**RISK_ASSESSMENTS**(
- `assessment_id` **PK**
- `borrower_id` **FK** → BORROWERS(`borrower_id`)
- `default_probability`
- `risk_score`
- `risk_category`
- `model_name`
- `model_version`
- `threshold_used`
- `snapshot_id`
- `assessed_at`
)

## 3. Primary Keys and Foreign Keys

| Relation | Primary Key | Foreign Key |
|---|---|---|
| `users` | `user_id` | None |
| `borrowers` | `borrower_id` | `managed_by` → `users.user_id` |
| `loans` | `loan_id` | `borrower_id` → `borrowers.borrower_id` |
| `payment_history` | `payment_id` | `loan_id` → `loans.loan_id` |
| `risk_assessments` | `assessment_id` | `borrower_id` → `borrowers.borrower_id` |

## 4. Relationships and Cardinality

1. **Users to Borrowers (1:N):** One user can manage multiple borrower profiles. Each borrower profile is managed by one user.
2. **Borrowers to Loans (1:N):** One borrower can have multiple loans. Each loan belongs to one borrower.
3. **Loans to Payment History (1:N):** One loan can have multiple payment records. Each payment record belongs to one loan.
4. **Borrowers to Risk Assessments (1:N):** One borrower can have multiple risk assessments over time. Each assessment belongs to one borrower.

## 5. Integrity Constraints

### Entity Integrity
- Every table has a primary key.
- Primary keys are generated using PostgreSQL identity columns and cannot be NULL.

### Referential Integrity
- `borrowers.managed_by` references `users.user_id`.
- `loans.borrower_id` references `borrowers.borrower_id`.
- `payment_history.loan_id` references `loans.loan_id`.
- `risk_assessments.borrower_id` references `borrowers.borrower_id`.
- Foreign keys use `ON DELETE RESTRICT`, preventing deletion of referenced parent records while dependent records exist.

### Domain Integrity
- User roles are restricted to `admin` and `analyst`.
- Loan principal amounts must be greater than zero.
- Interest rates must be between 0 and 100 when provided.
- Loan statuses are restricted to `active`, `closed`, and `defaulted`.
- Maturity dates cannot precede issue dates.
- Payment amounts cannot be negative.
- Payment statuses are restricted to `pending`, `paid`, `partial`, and `late`.
- Default probabilities and thresholds must be between 0 and 1 when provided.
- Risk scores must be between 0 and 100.
- Risk categories are restricted to `lower`, `moderate`, and `higher`.
- User email addresses are unique regardless of letter case through a unique index on `LOWER(email)`.

## 6. Indexes

The schema defines the following indexes to support common queries:

- `users_email_lower_unique`: Enforces case-insensitive uniqueness for user email addresses.
- `idx_borrowers_managed_by`: Supports queries filtering borrowers by their managing user.
- `idx_loans_borrower`: Supports queries retrieving loans belonging to a borrower.
- `idx_payments_loan_due_date`: Supports payment queries by loan and due date.
- `idx_assessments_borrower_date`: Supports retrieving a borrower's risk assessments in descending assessment-date order.

## 7. Triggers and Automatic Timestamp Updates

The `set_updated_at()` PostgreSQL trigger function automatically sets `updated_at` to the current timestamp whenever a borrower or loan record is updated.

The function is used by:
- `trg_borrowers_updated_at` on the `borrowers` table.
- `trg_loans_updated_at` on the `loans` table.

## 8. Design Summary

The schema separates user management, borrower profiles, loan records, payment transactions, and risk assessment history into five relations. This separation reduces unnecessary duplication and supports consistent storage of financial and assessment data.

The foreign-key relationships preserve links between related records, while domain constraints validate important financial values and status fields. Indexes improve common lookup operations, and triggers automate timestamp maintenance.
