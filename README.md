# Dynamic Credit Risk Scoring

A machine-learning-based credit risk assessment application built with FastAPI, Python, PostgreSQL, MongoDB, and React/Next.js.

## Key Features

- User authentication with admin and analyst roles.
- Borrower profile management.
- Credit default probability prediction.
- Risk scoring and risk categorization.
- Historical risk assessment records.
- MongoDB-backed risk review notes and review status.
- Interactive API documentation through FastAPI Swagger UI.
- Automated backend tests.

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Machine learning | scikit-learn, pandas, joblib |
| Relational database | PostgreSQL |
| Document database | MongoDB, PyMongo |
| Frontend | Next.js, React |
| Additional frontend | React, Vite |
| Testing | pytest, FastAPI TestClient |

## Project Structure

```text
dynamic-credit-risk-scoring/
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── database.py
│   ├── schemas.py
│   └── mongodb.py
├── frontend/
├── frontend-next/
├── model_experiments/
├── tests/
├── schema.sql
├── requirements.txt
├── train_candidate_model.py
├── compare_models.py
├── final_evaluate.py
├── tune_thresholds.py
├── prepare_credit_risk.py
├── prepare_credit_risk_v2.py
├── .env.example
└── README.md
```

## Prerequisites

- Python and pip
- PostgreSQL
- MongoDB
- Node.js and npm
- The required trained model artifact

## Backend Setup

### 1. Activate the virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

If `.venv` already exists, simply activate it.

### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install pytest httpx
```

### 3. Configure environment variables

Create a local environment file from the example:

```bash
cp .env.example .env
```

Update `.env` with your actual local database credentials and configuration. Never commit this file.

The application uses these configuration variables:

- `DATABASE_URL`: PostgreSQL connection URL.
- `MONGODB_URI`: MongoDB connection URI.
- `MONGODB_DATABASE`: MongoDB database name.
- `CREDIT_RISK_MODEL_PATH`: path to the trained model artifact.

### 4. Set up PostgreSQL

Ensure PostgreSQL is running and the `credit_risk_db` database exists.

For a new, empty database, initialize the schema with:

```bash
psql -d credit_risk_db -f schema.sql
```

Do not rerun this command blindly on an existing database, as the schema contains table and index creation statements.

### 5. Set up MongoDB

Ensure MongoDB is running and accessible using the URI in `.env`.

The configured database is `credit_risk_nosql`, and the risk review collection is `risk_reviews`.

### 6. Start the backend

From the project root:

```bash
uvicorn backend.main:app --reload --port 8000
```

API documentation:

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI specification: http://127.0.0.1:8000/openapi.json

## Frontend Setup

The primary frontend is located in `frontend-next/`.

```bash
cd frontend-next
npm install
npm run dev
```

Open the local URL printed by the development server. Ensure the frontend's API configuration points to the running backend.

A separate React/Vite frontend is also present in `frontend/`.

## Database Design

### PostgreSQL

The supplied `schema.sql` defines five core tables:

| Table | Purpose |
|---|---|
| `users` | User accounts and roles |
| `borrowers` | Borrower profiles and analyst assignments |
| `loans` | Loan information |
| `payment_history` | Individual loan payment records |
| `risk_assessments` | Historical risk predictions and model metadata |

Indexes support common queries, and triggers maintain update timestamps on borrower and loan records.

### MongoDB

Database: `credit_risk_nosql`

Collection: `risk_reviews`

Review documents can store borrower references, assigned analyst information, review type, risk level, notes, completion status, creator, and timestamps.

The documented review routes are:

- `POST /borrowers/{borrower_id}/risk-reviews`
- `GET /borrowers/{borrower_id}/risk-reviews`

Use Swagger UI to verify the active routes and request formats for the current build.

## Machine Learning

The candidate model is a Random Forest classifier using 23 input features from the credit-card-default dataset.

The cleaned dataset contains 29,965 rows after removing 35 exact duplicates from the original 30,000 rows. The recorded candidate training split contains 23,971 rows.

Candidate model metadata:

- Model name: `Random Forest (23-feature candidate)`
- Model version: `2.0-candidate`
- Classification threshold: `0.45`
- Training rows: `23,971`

### Recorded Evaluation Results

On the recorded held-out test split, at threshold `0.50`:

| Metric | Result |
|---|---:|
| ROC-AUC | 0.7730 |
| Accuracy | 0.7921 |
| Default precision | 0.5457 |
| Default recall | 0.5329 |
| Default F1-score | 0.5392 |

At threshold `0.45`, the recorded candidate results were:

| Metric | Result |
|---|---:|
| Accuracy | 0.7766 |
| Default precision | 0.5094 |
| Default recall | 0.5731 |
| Default F1-score | 0.5394 |

A lower classification threshold can increase default detection while also increasing false positives. These are experimental results from a specific test split, not guaranteed real-world performance.

The model requires additional validation, calibration, fairness assessment, and monitoring before use in real lending decisions. Predictions should support human review rather than serve as the sole basis for a credit decision.

### Model Experiment Scripts

- `train_candidate_model.py`: trains the candidate model.
- `compare_models.py`: compares models.
- `final_evaluate.py`: evaluates model performance.
- `tune_thresholds.py`: investigates classification thresholds.
- `prepare_credit_risk.py` and `prepare_credit_risk_v2.py`: prepare the dataset.
- `check_duplicates.py`: checks duplicate records.

Review script settings before running training or evaluation commands, because generated artifacts may be overwritten.

## Testing

From the project root:

```bash
python -m pytest -q
```

The latest recorded test run reported 12 passing tests. One deprecation warning related to Starlette's TestClient/httpx integration did not cause the tests to fail.

Re-run the test suite after changes to authentication, prediction logic, database access, or API integration.

## Security and Data Handling

- Never commit `.env`, passwords, or authentication tokens.
- Keep large `.joblib` model files out of Git.
- Do not commit real borrower information or personally identifiable data.
- Use appropriate database credentials and access controls.
- Treat risk predictions as estimates rather than certainties.
- Use anonymized or synthetic records for demonstrations and tests.

