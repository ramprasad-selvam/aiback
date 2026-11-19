from typing import Any
from pydantic import BaseModel, Field


class ClaimInput(BaseModel):
    raw_document_text: str = ""
    policy_details: dict[str, Any] = Field(default_factory=dict)
    historical_claims: list[dict[str, Any]] = Field(default_factory=list)
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"


class LineItem(BaseModel):
    description: str
    amount: float


class ExtractedData(BaseModel):
    patient_id: str = ""
    provider_name: str = ""
    date_of_service: str = ""
    total_claimed_amount: float = 0.0
    line_items: list[LineItem] = Field(default_factory=list)


class ValidationFlags(BaseModel):
    is_duplicate: bool = False
    is_fraud_suspected: bool = False
    has_policy_mismatch: bool = False
    missing_documents: list[str] = Field(default_factory=list)


class ClaimEvaluation(BaseModel):
    claim_id: str = ""
    extracted_data: ExtractedData = Field(default_factory=ExtractedData)
    validation_flags: ValidationFlags = Field(default_factory=ValidationFlags)
    risk_score: int = Field(default=0, ge=0, le=100)
    recommended_action: str
    reasoning_summary: str
