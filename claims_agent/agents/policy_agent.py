import re


class PolicyAgent:
    def run(self, state: dict) -> dict:
        extracted = state["extracted_data"]
        policy = state.get("policy_details", {}) or {}
        text = state.get("raw_document_text", "") or ""
        mismatch = False
        evidence = []

        diagnosis_codes = re.findall(r"(?i)\b[A-TV-Z][0-9][0-9A-Z](?:\.[0-9A-Z]{1,4})?\b", text)
        covered = policy.get("covered_diagnosis_codes")
        if covered:
            covered_norm = {str(code).upper() for code in covered}
            if not diagnosis_codes or not any(code.upper() in covered_norm for code in diagnosis_codes):
                mismatch = True
                evidence.append("No extracted diagnosis code is listed as covered by the policy tier.")

        exclusions = {str(value).casefold() for value in policy.get("exclusions", [])}
        for item in extracted.get("line_items", []):
            if any(exclusion and exclusion in str(item["description"]).casefold() for exclusion in exclusions):
                mismatch = True
                evidence.append(f"Line item '{item['description']}' appears to match a policy exclusion.")

        thresholds = policy.get("line_item_allowable_thresholds", {}) or {}
        for item in extracted.get("line_items", []):
            for key, threshold in thresholds.items():
                if str(key).casefold() in str(item["description"]).casefold():
                    try:
                        limit = float(threshold)
                    except (TypeError, ValueError):
                        continue
                    if float(item["amount"]) > limit:
                        mismatch = True
                        evidence.append(f"Line item '{item['description']}' exceeds the allowable threshold of {limit:.2f}.")

        flags = dict(state["validation_flags"])
        flags.update({"has_policy_mismatch": mismatch})
        return {**state, "validation_flags": flags, "reasoning": state["reasoning"] + evidence}
