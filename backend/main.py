
from pathlib import Path

import joblib
import os
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import PyMongoError
from backend.mongodb import risk_reviews


from backend.auth import (
    create_access_token,
    get_current_user,
    get_user_by_email,
    hash_password,
    verify_password,
)
from backend.database import get_db
from backend.models import Borrower, RiskAssessment, User
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


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: str
    role: str


class RiskReviewCreate(BaseModel):
    review_type: str = Field(default="manual_review", max_length=50)
    risk_level: str = Field(default="medium", max_length=20)
    notes: str = Field(min_length=1, max_length=2000)
    reviewed: bool = False


# --------------------------------------------------
# Authentication
# --------------------------------------------------

@app.post("/auth/register", status_code=201)
def register_user(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    email = str(data.email).strip().lower()

    if get_user_by_email(db, email):
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    user = User(
        full_name=data.full_name.strip(),
        email=email,
        password_hash=hash_password(data.password),
        role="analyst",
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    return {
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
    }


@app.post("/auth/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, form_data.username.strip())

    if (
        not user
        or not verify_password(
            form_data.password,
            user.password_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user_id": user.user_id,
        "full_name": user.full_name,
        "role": user.role,
    }


@app.get("/auth/me", response_model=UserResponse)
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return {
        "user_id": current_user.user_id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
    }


# --------------------------------------------------
# CORS
# --------------------------------------------------

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
# Authorization helpers
# --------------------------------------------------

def require_roles(*allowed_roles: str):
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker


def get_accessible_borrower(
    borrower_id: int,
    db: Session,
    current_user: User,
) -> Borrower:
    borrower = db.get(Borrower, borrower_id)

    if borrower is None:
        raise HTTPException(
            status_code=404,
            detail="Borrower not found",
        )

    # Admins can access every borrower. Analysts can access
    # only borrowers assigned to their own user ID.
    if (
        current_user.role != "admin"
        and borrower.managed_by != current_user.user_id
    ):
        # Return 404 to avoid revealing another user's records.
        raise HTTPException(
            status_code=404,
            detail="Borrower not found",
        )

    return borrower


# --------------------------------------------------
# Load the trained machine learning model
# --------------------------------------------------


MODEL_PATH = Path(
    os.getenv(
        "CREDIT_RISK_MODEL_PATH",
        str(Path(__file__).resolve().parent / "credit_risk_model.joblib"),
    )
).expanduser().resolve()

if not MODEL_PATH.exists():
    raise RuntimeError(
        f"Trained model not found at {MODEL_PATH}. "
        "Check CREDIT_RISK_MODEL_PATH or run backend.train_and_save_model."
    )

model_artifact = joblib.load(MODEL_PATH)

required_keys = {
    "model",
    "features",
    "threshold",
    "model_name",
    "model_version",
    "training_rows",
}
missing_keys = required_keys - model_artifact.keys()

if missing_keys:
    raise RuntimeError(
        f"Model artifact is missing required keys: {sorted(missing_keys)}"
    )



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
    current_user: User = Depends(
        require_roles("admin", "analyst")
    ),
):
    # Never trust a client-supplied managed_by value.
    borrower = Borrower(
        full_name=borrower_data.full_name,
        managed_by=current_user.user_id,
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
                "Could not create borrower. Check the borrower "
                "details and ensure the external reference is unique."
            ),
        )

    return borrower


@app.get(
    "/borrowers",
    response_model=list[BorrowerResponse],
)
def list_borrowers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    statement = select(Borrower)

    if current_user.role != "admin":
        statement = statement.where(
            Borrower.managed_by == current_user.user_id
        )

    statement = statement.order_by(Borrower.borrower_id)

    return db.scalars(statement).all()


@app.get(
    "/borrowers/{borrower_id}",
    response_model=BorrowerResponse,
)
def get_borrower(
    borrower_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_accessible_borrower(
        borrower_id,
        db,
        current_user,
    )


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
    current_user: User = Depends(get_current_user),
):
    get_accessible_borrower(
        borrower_id,
        db,
        current_user,
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
    current_user: User = Depends(
        require_roles("admin", "analyst")
    ),
):
    get_accessible_borrower(
        borrower_id,
        db,
        current_user,
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


@app.post("/borrowers/{borrower_id}/risk-reviews", status_code=201)
def create_risk_review(
    borrower_id: int,
    review: RiskReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    borrower = get_accessible_borrower(borrower_id, db, current_user)

    document = {
        "borrower_id": borrower.borrower_id,
        "managed_by": borrower.managed_by,
        "created_by": current_user.user_id,
        "review_type": review.review_type,
        "risk_level": review.risk_level,
        "notes": review.notes,
        "reviewed": review.reviewed,
        "created_at": datetime.now(timezone.utc),
    }

    try:
        result = risk_reviews.insert_one(document)
        document["_id"] = result.inserted_id
        document["created_at"] = document["created_at"].isoformat()
        document["_id"] = str(document["_id"])
        return document
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is temporarily unavailable",
        ) from exc


@app.get("/borrowers/{borrower_id}/risk-reviews")
def list_risk_reviews(
    borrower_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_accessible_borrower(borrower_id, db, current_user)

    try:
        documents = list(
            risk_reviews.find({"borrower_id": borrower_id}).sort(
                "created_at", -1
            )
        )

        for document in documents:
            document["_id"] = str(document["_id"])
            if isinstance(document.get("created_at"), datetime):
                document["created_at"] = document["created_at"].isoformat()

        return documents
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is temporarily unavailable",
        ) from exc
