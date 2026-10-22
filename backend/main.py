
from pathlib import Path

import joblib
import pandas as pd

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Borrower, RiskAssessment
from backend.schemas import (
    BorrowerCreate,
    BorrowerResponse,
    PredictionRequest,
    RiskAssessmentResponse,
)

# --------------------------------------------------
# Application setup
# --------------------------------------------------

app = FastAPI(
    title="Dynamic Credit Risk Scoring API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Load the trained machine learning model
# --------------------------------------------------

MODEL_PATH = Path(__file__).resolve().parent / "credit_risk_model.joblib"

if not MODEL_PATH.exists():
    raise RuntimeError(
        f"Trained model not found at {MODEL_PATH}. "
        "Run backend.train_and_save_model first."
    )

model_artifact = joblib.load(MODEL_PATH)


# --------------------------------------------------
# Health checks
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Dynamic Credit Risk Scoring API is running"
    }


@app.get("/health/db")
def database_health(db: Session = Depends(get_db)):
    database_name = db.execute(
        text("SELECT current_database()")
    ).scalar_one()

    return {
        "status": "connected",
        "database": database_name,
    }


# --------------------------------------------------
# Borrower endpoints
# --------------------------------------------------

@app.post(
    "/borrowers",
    response_model=BorrowerResponse,
    status_code=201,
)
def create_borrower(
    borrower_data: BorrowerCreate,
    db: Session = Depends(get_db),
):
    borrower = Borrower(
        full_name=borrower_data.full_name,
        managed_by=borrower_data.managed_by,
        external_reference=borrower_data.external_reference,
    )

    db.add(borrower)

    try:
        db.commit()
        db.refresh(borrower)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                "Could not create borrower. Check that the user "
                "exists and the external reference is unique."
            ),
        )

    return borrower


@app.get("/borrowers", response_model=list[BorrowerResponse])
def list_borrowers(db: Session = Depends(get_db)):
    statement = select(Borrower).order_by(Borrower.borrower_id)
    return db.scalars(statement).all()


@app.get(
    "/borrowers/{borrower_id}",
    response_model=BorrowerResponse,
)
def get_borrower(
    borrower_id: int,
    db: Session = Depends(get_db),
):
    borrower = db.get(Borrower, borrower_id)

    if borrower is None:
        raise HTTPException(
            status_code=404,
            detail="Borrower not found",
        )

    return borrower


# --------------------------------------------------
# Risk assessment history
# --------------------------------------------------

@app.get(
    "/borrowers/{borrower_id}/assessments",
    response_model=list[RiskAssessmentResponse],
)
def get_risk_history(
    borrower_id: int,
    db: Session = Depends(get_db),
):
    borrower = db.get(Borrower, borrower_id)

    if borrower is None:
        raise HTTPException(
            status_code=404,
            detail="Borrower not found",
        )

    statement = (
        select(RiskAssessment)
        .where(RiskAssessment.borrower_id == borrower_id)
        .order_by(RiskAssessment.assessed_at.desc())
    )

    return db.scalars(statement).all()


# --------------------------------------------------
# Generate and save a risk assessment
# --------------------------------------------------

@app.post("/borrowers/{borrower_id}/assess")
def assess_borrower(
    borrower_id: int,
    request: PredictionRequest,
    db: Session = Depends(get_db),
):
    borrower = db.get(Borrower, borrower_id)

    if borrower is None:
        raise HTTPException(
            status_code=404,
            detail="Borrower not found",
        )

    features = request.model_dump()

    # Keep feature ordering consistent with model training.
    input_df = pd.DataFrame(
        [features],
        columns=model_artifact["features"],
    )

    probability = float(
        model_artifact["model"].predict_proba(input_df)[0][1]
    )

    risk_score = round(probability * 100)

    if risk_score < 30:
        risk_category = "lower"
    elif risk_score < 60:
        risk_category = "moderate"
    else:
        risk_category = "higher"

    threshold = float(model_artifact["threshold"])
    predicted_default = probability >= threshold

    assessment = RiskAssessment(
        borrower_id=borrower_id,
        default_probability=round(probability, 6),
        risk_score=risk_score,
        risk_category=risk_category,
        model_name=model_artifact["model_name"],
        model_version=model_artifact["model_version"],
        threshold_used=threshold,
    )

    db.add(assessment)

    try:
        db.commit()
        db.refresh(assessment)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Failed to save the risk assessment.",
        )

    return {
        "assessment_id": assessment.assessment_id,
        "borrower_id": borrower_id,
        "default_probability": probability,
        "risk_score": risk_score,
        "risk_category": risk_category,
        "predicted_default": predicted_default,
        "threshold_used": threshold,
        "model_name": assessment.model_name,
        "model_version": assessment.model_version,
        "assessed_at": assessment.assessed_at,
    }
