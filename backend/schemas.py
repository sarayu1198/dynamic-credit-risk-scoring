
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class BorrowerCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=150)
    managed_by: int = Field(gt=0)
    external_reference: str | None = Field(
        default=None, max_length=50
    )


class BorrowerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    borrower_id: int
    managed_by: int
    full_name: str
    external_reference: str | None
    created_at: datetime
    updated_at: datetime


class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assessment_id: int
    borrower_id: int
    default_probability: Decimal
    risk_score: int
    risk_category: str
    model_name: str
    model_version: str
    threshold_used: Decimal | None
    snapshot_id: str | None
    assessed_at: datetime

from pydantic import Field


class PredictionRequest(BaseModel):
    limit_bal: float = Field(gt=0)

    pay_status_sep: int
    pay_status_aug: int
    pay_status_jul: int
    pay_status_jun: int
    pay_status_may: int
    pay_status_apr: int

    bill_amt1: float
    bill_amt2: float
    bill_amt3: float
    bill_amt4: float
    bill_amt5: float
    bill_amt6: float

    pay_amt1: float
    pay_amt2: float
    pay_amt3: float
    pay_amt4: float
    pay_amt5: float
    pay_amt6: float