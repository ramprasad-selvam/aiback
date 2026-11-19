class DecisionAgent:
    def run(self, state: dict) -> dict:
        flags = state["validation_flags"]
        risk = 30 if flags["is_duplicate"] else 0
        risk += 35 if flags["is_fraud_suspected"] else 0
        risk += 20 if flags["has_policy_mismatch"] else 0
        risk += 10 * min(len(flags["missing_documents"]), 3)

        extracted = state["extracted_data"]
        if not extracted.get("patient_id") or not extracted.get("provider_name") or not extracted.get("date_of_service"):
            risk += 10
        risk = min(risk, 100)

        if flags["is_fraud_suspected"] or flags["is_duplicate"]:
            action = "REJECT" if flags["is_fraud_suspected"] and risk >= 70 else "FLAG_FOR_HUMAN_REVIEW"
        elif flags["missing_documents"]:
            action = "REQUEST_DOCUMENTS"
        elif flags["has_policy_mismatch"]:
            action = "FLAG_FOR_HUMAN_REVIEW"
        else:
            action = "APPROVE"

        summary = " ".join(state["reasoning"]) or "The claim passed the available automated checks."
        return {**state, "risk_score": risk, "recommended_action": action, "reasoning_summary": summary}
