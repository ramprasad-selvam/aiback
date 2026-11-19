import json

from claims_agent import evaluate_claim
from claims_agent.strict_models import StrictClaimEvaluation


def complete_text(invoice="INV-1"):
    return f"""
Claim ID: CLM-001
Invoice Number: {invoice}
Patient ID: PT-100
Patient Name: Test Patient
Provider Name: Northside Clinic
Provider ID: NPI-1234567890
Date of Service: 2026-11-18
Diagnosis: ICD-10 J06.9
Line Item: Office visit - $150.00
Line Item: X-ray - $75.00
Total Claimed Amount: $225.00
"""


def test_complete_claim_is_approved():
    result = evaluate_claim({
        "raw_document_text": complete_text(),
        "policy_details": {
            "covered_diagnosis_codes": ["J06.9"],
            "line_item_allowable_thresholds": {"office visit": 200, "x-ray": 100},
        },
        "historical_claims": [],
    })

    StrictClaimEvaluation.model_validate(result)
    assert result["processing_status"] == "APPROVED"
    assert result["claim_id"] == "CLM-001"
    assert result["patient_id"] == "PT-100"
    assert result["extracted_data"] == {
        "total_claimed_amount": 225.0,
        "invoice_number": "INV-1",
        "date_of_service": "2026-11-18",
        "icd_codes": ["J06.9"],
    }


def test_duplicate_invoice_is_duplicate_status():
    result = evaluate_claim({
        "raw_document_text": complete_text("INV-42"),
        "policy_details": {},
        "historical_claims": [{"invoice_number": "INV-42", "patient_id": "PT-100"}],
    })

    assert result["processing_status"] == "DUPLICATE_SUSPECTED"
    assert any(f["guardrail_name"] == "Duplicate Detection" for f in result["flags_triggered"])


def test_missing_fields_require_manual_review():
    result = evaluate_claim({"raw_document_text": "Unreadable claim image; no labeled values."})

    StrictClaimEvaluation.model_validate(result)
    assert result["processing_status"] == "REQUIRES_MANUAL_REVIEW"
    assert "Patient Name" in result["missing_documents"]
    assert "Claim Amount" in result["missing_documents"]
    assert "Provider ID" in result["missing_documents"]


def test_regional_rate_and_diagnosis_conflict_are_rejected():
    result = evaluate_claim({
        "raw_document_text": """
Invoice Number: INV-5
Claim ID: CLM-5
Patient ID: PT-5
Patient Name: Test Patient
Provider ID: P123
Provider Name: Test Clinic
Date of Service: 2026-11-18
Diagnosis: ICD-10 J06.9
Treatment: chemotherapy
Total Claimed Amount: $2000.00
Line Item: chemotherapy - $2000.00
""",
        "policy_details": {"standard_regional_rates": {"chemotherapy": 1000}},
        "historical_claims": [],
    })

    assert result["processing_status"] == "REJECTED"
    names = {flag["guardrail_name"] for flag in result["flags_triggered"]}
    assert "Regional Rate Deviation" in names
    assert "Diagnosis-Treatment Conflict" in names


def test_output_is_json_serializable_and_has_no_legacy_keys():
    result = evaluate_claim({})
    json.dumps(result)
    assert set(result) == {
        "claim_id", "patient_id", "processing_status", "extracted_data",
        "flags_triggered", "missing_documents", "auditor_notes",
    }
