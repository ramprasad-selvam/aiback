import re


class FraudAgent:
    def run(self, state: dict) -> dict:
        text = state.get("raw_document_text", "") or ""
        extracted = state["extracted_data"]
        fraudulent = False
        evidence = []

        npi_match = re.search(r"(?i)\b(?:Provider\s*)?NPI\s*[:=-]?\s*(\d{10})\b", text)
        provider_npi = npi_match.group(1) if npi_match else ""
        if provider_npi and (len(provider_npi) != 10 or not provider_npi.isdigit()):
            fraudulent = True
            evidence.append("The extracted provider NPI is malformed.")

        amounts = [float(item["amount"]) for item in extracted.get("line_items", [])]
        if len(amounts) >= 3 and len([amount for amount in amounts if amount >= 1000]) >= 2:
            fraudulent = True
            evidence.append("Multiple unusually high line-item amounts were detected.")

        if re.search(r"(?i)(?:corrected|void|reissue|resubmit|conflict|adjusted)", text) and re.search(r"(?i)(?:altered|whiteout|suspicious)", text):
            fraudulent = True
            evidence.append("The source text contains indicators of a corrected or altered document.")

        if not extracted.get("date_of_service"):
            evidence.append("The date of service could not be normalized; this is insufficient evidence alone for fraud.")

        flags = dict(state["validation_flags"])
        flags["is_fraud_suspected"] = fraudulent
        return {**state, "validation_flags": flags, "reasoning": state["reasoning"] + evidence}
