from ..tools.parsing_tool import ParsingTool


class DuplicateAgent:
    def run(self, state: dict) -> dict:
        extracted = state["extracted_data"]
        claim_id = state.get("claim_id", "")
        dos = extracted.get("date_of_service", "")
        invoice = ParsingTool.extract_labeled(state.get("raw_document_text", ""), ("Invoice Number", "Invoice/Claim ID"))
        duplicate = False
        evidence = []

        for prior in state.get("historical_claims", []) or []:
            prior_id = str(prior.get("invoice_number") or prior.get("claim_id") or prior.get("invoice_id") or "")
            prior_dos = ParsingTool.normalize_date(str(prior.get("date_of_service") or prior.get("dos") or prior.get("service_date") or ""))
            if claim_id and prior_id and claim_id.casefold() == prior_id.casefold() or invoice and prior_id and invoice.casefold() == prior_id.casefold():
                duplicate = True
                evidence.append("The invoice/claim identifier matches a historical claim.")
                break
            if dos and prior_dos == dos:
                prior_patient = str(prior.get("patient_id") or "")
                prior_provider = str(prior.get("provider_name") or "")
                patient_match = prior_patient and prior_patient == extracted.get("patient_id")
                provider_match = not prior_provider or prior_provider.casefold() == str(extracted.get("provider_name", "")).casefold()
                try:
                    amount_match = prior.get("total_claimed_amount") is not None and abs(float(prior["total_claimed_amount"]) - float(extracted.get("total_claimed_amount", 0))) < 0.005
                except (TypeError, ValueError):
                    amount_match = False
                if patient_match and provider_match and amount_match:
                    duplicate = True
                    evidence.append("A historical claim has the exact patient, date of service, and claimed amount combination.")
                    break

        return {**state, "validation_flags": {"is_duplicate": duplicate}, "reasoning": evidence}
