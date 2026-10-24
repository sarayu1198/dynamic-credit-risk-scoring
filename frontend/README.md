# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## Hybrid SQL and NoSQL Database Architecture

### Overview

The Dynamic Credit Risk Scoring application uses a hybrid database architecture combining PostgreSQL and MongoDB.

- **PostgreSQL:** Stores structured application data, including user accounts, borrowers, and formal risk assessments.
- **MongoDB:** Stores flexible risk-review documents that may contain manual review notes, risk levels, review status, model-version metadata, and timestamps.

### MongoDB Database Design

**Database:** `credit_risk_nosql`

**Collection:** `risk_reviews`

| Field | Purpose |
|---|---|
| `_id` | MongoDB-generated document identifier |
| `borrower_id` | References the borrower in PostgreSQL |
| `managed_by` | Identifies the borrower’s assigned analyst |
| `created_by` | Identifies the user who created the review |
| `review_type` | Type of review |
| `risk_level` | Risk category recorded in the review |
| `notes` | Review observations |
| `reviewed` | Indicates whether the review has been completed |
| `created_at` | Review creation timestamp |

MongoDB's flexible document structure allows additional review metadata to be stored without requiring every field to be part of a fixed relational table.

### API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/borrowers/{borrower_id}/risk-reviews` | Creates a risk-review document in MongoDB |
| GET | `/borrowers/{borrower_id}/risk-reviews` | Retrieves risk reviews for an accessible borrower |

Both endpoints require authentication and reuse the application's borrower-access authorization logic. Administrators can access all borrowers, while analysts can access only borrowers assigned to them.

### Verification

The integration was tested through the FastAPI Swagger interface and the MongoDB shell.

- POST returned HTTP 201 Created.
- GET returned HTTP 200 OK.
- The MongoDB shell confirmed that API-created review documents were persisted in `credit_risk_nosql.risk_reviews`.

### Design Rationale

PostgreSQL remains the source of truth for structured application records, while MongoDB supports supplementary review information with a flexible schema. This separation demonstrates how relational and document databases can serve different data-management requirements within one application.
