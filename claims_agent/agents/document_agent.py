import re


class DocumentAgent:
    def run(self, state: dict) -> dict:
        text = state.get("raw_document_text", "") or ""
        policy = state.get("policy_details", {}) or {}
        missing = []

        if not text.strip(): missing.append("Claim document or OCR text")
        if not state.get("claim_id"): missing.append("Invoice or claim identifier")
        if not state["extracted_data"].get("patient_id"): missing.append("Patient ID")
        if not state["extracted_data"].get("provider_name"): missing.append("Provider name")

        lower = text.casefold()
        if re.search(r"(?i)\b(?:admission|surgery|inpatient|hospital)\b", lower) and not re.search(r"(?i)discharge\s+(?:summary|report)", lower):
            missing.append("Discharge summary")
        if re.search(r"(?i)\b(?:pharmacy|prescription|medication|drug)\b", lower) and not re.search(r"(?i)itemized\s+(?:pharmacy|medication|drug)|pharmacy\s+bill", lower):
            missing.append("Itemized pharmacy bill")

        for document in policy.get("mandatory_documents", []):
            name = str(document)
            if name.casefold() not in lower:
                missing.append(name)

        flags = dict(state["validation_flags"])
        flags["missing_documents"] = list(dict.fromkeys(missing))
        evidence = ["Mandatory or inferred supporting documents are missing."] if missing else ["No inferred mandatory documents are missing."]
        return {**state, "validation_flags": flags, "reasoning": state["reasoning"] + evidence}
