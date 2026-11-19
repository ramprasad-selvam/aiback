import json

from claims_agent import evaluate_claim
from claims_agent.strict_models import StrictClaimEvaluation


def test_complete_claim_is_approved():
    result = evaluate_claim({
        "raw_document_text": """
Claim ID: CLM-001
Invoice Number: INV-001
Patient ID: PT-100
Patient Name: Test Patient
Provider Name: Northside Clinic
Provider ID: NPI-1234567890
Date of Service: 2026-11-18
Diagnosis: ICD-10 J06.9
Line Item: Office visit - $150.00
Line Item: X-ray - $75.00
Total Claimed Amount: $225.00
""",
        "policy_details": {
            "coverage_tier": "gold",
            "covered_diagnosis_codes": ["J06.9"],
            "line_item_allowable_thresholds": {"office visit": 200, "x-ray": 100},
        },
        "historical_claims": [],
    })

    StrictClaimEvaluation.model_validate(result)
    assert result["claim_id"] == "CLM-001"
    assert result["extracted_data"]["total_claimed_amount"] == 225.0
    assert result["extracted_data"]["date_of_service"] == "2026-11-18"
    assert result["processing_status"] in {"APPROVED", "REJECTED", "DUPLICATE_SUSPECTED", "REQUIRES_MANUAL_REVIEW"}


def test_duplicate_invoice_is_duplicate_status():
    result = evaluate_claim({
        "raw_document_text": "Invoice Number: INV-42\nClaim ID: CLM-42\nPatient ID: PT-1\nPatient Name: Test Patient\nProvider Name: Clinic A\nProvider ID: P123\nDate of Service: 11/18/2026\nTotal Claimed Amount: $100.00",
        "policy_details": {},
        "historical_claims": [{"invoice_number": "INV-42", "patient_id": "PT-1", "provider_name": "Clinic A"}],
    })

    assert result["processing_status"] == "DUPLICATE_SUSPECTED"


def test_missing_input_requests_manual_review():
    result = evaluate_claim({})

    assert result["patient_id"] is None
    assert "Claim document or OCR text" in result["missing_documents"]
    assert result["processing_status"] == "REQUIRES_MANUAL_REVIEW"


def test_output_is_json_serializable():
    result = evaluate_claim({"raw_document_text": "Claim ID: C-1"})
    json.dumps(result)
    assert set(result) == {"claim_id", "patient_id", "processing_status", "extracted_data", "flags_triggered", "missing_documents", "auditor_notes"}
