import re
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from ..agents.extraction_agent import ExtractionAgent
from ..agents.duplicate_agent import DuplicateAgent
from ..agents.policy_agent import PolicyAgent
from ..agents.fraud_agent import FraudAgent
from ..agents.document_agent import DocumentAgent
from ..agents.decision_agent import DecisionAgent
from ..models import ClaimInput
from ..strict_models import StrictClaimEvaluation, StrictExtractedData, TriggeredFlag
from ..tools.parsing_tool import ParsingTool


class ClaimState(TypedDict, total=False):
    raw_document_text: str
    policy_details: dict[str, Any]
    historical_claims: list[dict[str, Any]]
    extracted_data: dict[str, Any]
    claim_id: str
    validation_flags: dict[str, Any]
    reasoning: list[str]
    groq_api_key: str | None
    groq_model: str
    risk_score: int
    recommended_action: str
    reasoning_summary: str


def evaluate_claim(payload: ClaimInput | dict[str, Any]) -> dict[str, Any]:
    data = payload if isinstance(payload, ClaimInput) else ClaimInput.model_validate(payload)

    extraction = ExtractionAgent()
    duplicate = DuplicateAgent()
    policy = PolicyAgent()
    fraud = FraudAgent()
    documents = DocumentAgent()
    decision = DecisionAgent()

    graph = StateGraph(ClaimState)
    graph.add_node("extract", extraction.run)
    graph.add_node("duplicate", duplicate.run)
    graph.add_node("policy", policy.run)
    graph.add_node("fraud", fraud.run)
    graph.add_node("documents", documents.run)
    graph.add_node("decision", decision.run)
    graph.add_edge(START, "extract")
    graph.add_edge("extract", "duplicate")
    graph.add_edge("duplicate", "policy")
    graph.add_edge("policy", "fraud")
    graph.add_edge("fraud", "documents")
    graph.add_edge("documents", "decision")
    graph.add_edge("decision", END)

    result = graph.compile().invoke({
        "raw_document_text": data.raw_document_text,
        "policy_details": data.policy_details,
        "historical_claims": data.historical_claims,
        "groq_api_key": data.groq_api_key,
        "groq_model": data.groq_model,
    })

    extracted = result["extracted_data"]
    flags = result["validation_flags"]
    text = data.raw_document_text
    claim_id = str(result.get("claim_id", "")).strip() or None
    patient_id = str(extracted.get("patient_id", "")).strip() or None
    invoice_number = ParsingTool.extract_labeled(text, ("Invoice Number", "Invoice/Claim ID")) or claim_id

    missing: list[str] = []
    if not text.strip(): missing.append("Claim document or OCR text")
    if not ParsingTool.extract_labeled(text, ("Patient Name", "Patient")): missing.append("Patient Name")
    if not patient_id: missing.append("Patient ID")
    if not extracted.get("total_claimed_amount"): missing.append("Claim Amount")
    if not extracted.get("date_of_service"): missing.append("Date of Service")
    if not re.search(r"(?i)\b(?:Provider\s*)?(?:ID|NPI)\s*[:=-]?\s*[A-Z0-9-]+", text): missing.append("Provider ID")
    if not invoice_number: missing.append("Invoice Number")
    for document in flags["missing_documents"]:
        if document not in missing:
            missing.append(document)

    triggered: list[TriggeredFlag] = []
    if flags["is_duplicate"]:
        triggered.append(TriggeredFlag(guardrail_name="Duplicate Detection", severity="HIGH", reason="The invoice or exact patient/date/amount combination matches an existing historical claim."))
    if missing:
        triggered.append(TriggeredFlag(guardrail_name="Missing Data", severity="HIGH", reason="Mandatory claim fields or supporting documents are missing or illegible: " + ", ".join(missing) + "."))
    if flags["is_fraud_suspected"]:
        triggered.append(TriggeredFlag(guardrail_name="Fraud and Anomaly Detection", severity="HIGH", reason=result["reasoning_summary"]))
    if flags["has_policy_mismatch"]:
        triggered.append(TriggeredFlag(guardrail_name="Policy Mismatch", severity="MEDIUM", reason=result["reasoning_summary"]))

    icd_codes = ParsingTool.extract_icd_codes(text)
    standard_rates = data.policy_details.get("standard_regional_rates", {}) or {}
    for item in extracted.get("line_items", []):
        description = str(item["description"])
        amount = float(item["amount"])
        for service, standard in standard_rates.items():
            if str(service).casefold() in description.casefold():
                try:
                    standard_amount = float(standard)
                except (TypeError, ValueError):
                    continue
                if standard_amount > 0 and abs(amount - standard_amount) / standard_amount > 0.30:
                    triggered.append(TriggeredFlag(guardrail_name="Regional Rate Deviation", severity="HIGH", reason=f"The billed amount for '{description}' deviates more than 30% from the regional standard."))

    conflict_patterns = (
        (r"\bfracture\b|\bbroken\s+bone\b", r"^S"),
        (r"\bchemotherapy\b|\bcancer\s+treatment\b", r"^[CD]"),
        (r"\bpregnancy\b|\bobstetric\b", r"^O"),
    )
    for treatment_pattern, compatible in conflict_patterns:
        if re.search(treatment_pattern, text, re.IGNORECASE) and icd_codes and not any(re.match(compatible, code) for code in icd_codes):
            triggered.append(TriggeredFlag(guardrail_name="Diagnosis-Treatment Conflict", severity="HIGH", reason="The extracted treatment description conflicts with the extracted ICD-10 code range."))

    if flags["is_duplicate"]:
        status = "DUPLICATE_SUSPECTED"
    elif missing:
        status = "REQUIRES_MANUAL_REVIEW"
    elif any(flag.severity == "HIGH" for flag in triggered):
        status = "REJECTED"
    elif triggered:
        status = "REQUIRES_MANUAL_REVIEW"
    else:
        status = "APPROVED"

    evaluation = StrictClaimEvaluation(
        claim_id=claim_id,
        patient_id=patient_id,
        processing_status=status,
        extracted_data=StrictExtractedData(
            total_claimed_amount=round(float(extracted.get("total_claimed_amount", 0) or 0), 2),
            invoice_number=invoice_number or "",
            date_of_service=str(extracted.get("date_of_service", "") or ""),
            icd_codes=icd_codes,
        ),
        flags_triggered=triggered,
        missing_documents=list(dict.fromkeys(missing)),
        auditor_notes=result["reasoning_summary"] or "The claim was evaluated using available document text, policy metadata, and historical records.",
    )
    return evaluation.model_dump(mode="json")
