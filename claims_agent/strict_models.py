from typing import Literal

from pydantic import BaseModel, Field


class StrictExtractedData(BaseModel):
    total_claimed_amount: float = 0.0
    invoice_number: str = ""
    date_of_service: str = ""
    icd_codes: list[str] = Field(default_factory=list)


class TriggeredFlag(BaseModel):
    guardrail_name: str
    severity: Literal["LOW", "MEDIUM", "HIGH"]
    reason: str


class StrictClaimEvaluation(BaseModel):
    claim_id: str | None = None
    patient_id: str | None = None
    processing_status: Literal[
        "APPROVED",
        "REJECTED",
        "DUPLICATE_SUSPECTED",
        "REQUIRES_MANUAL_REVIEW",
    ]
    extracted_data: StrictExtractedData = Field(default_factory=StrictExtractedData)
    flags_triggered: list[TriggeredFlag] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    auditor_notes: str
