from decimal import Decimal, InvalidOperation
import re

from ..models import ExtractedData, LineItem
from ..tools.parsing_tool import ParsingTool
from ..tools.groq_tool import GroqExtractorTool


_MONEY = r"(?:[$€£]?\s*)(\d+(?:,\d{3})*(?:\.\d{1,2})?)"


class ExtractionAgent:
    def __init__(self) -> None:
        self.parser = ParsingTool()
        self.groq = GroqExtractorTool()

    def run(self, state: dict) -> dict:
        text = state.get("raw_document_text", "") or ""
        claim_id = self.parser.extract_labeled(text, ("Claim ID", "Claim Number", "Invoice Number", "Invoice/Claim ID"))
        patient_id = self.parser.extract_labeled(text, ("Patient ID", "Member ID", "Subscriber ID"))
        provider_name = self.parser.extract_labeled(text, ("Provider Name", "Facility Name", "Provider"))
        dos = self.parser.normalize_date(self.parser.extract_labeled(text, ("Date of Service", "Service Date", "DOS")))

        line_items: list[LineItem] = []
        pattern = r"(?im)^\s*(?:Line\s*Item|Item)\s*[:=-]?\s*(.+?)\s*[-:]?\s*" + _MONEY + r"\s*$"
        for match in re.finditer(pattern, text):
            description = match.group(1).strip(" :-")
            if description:
                line_items.append(LineItem(description=description, amount=self._money(match.group(2))))

        total_match = re.search(r"(?im)^\s*(?:Total\s*(?:Claimed)?\s*Amount|Claim(?:ed)?\s*Total|Grand\s*Total)\s*[:=-]\s*" + _MONEY + r"\s*$", text)
        total = self._money(total_match.group(1)) if total_match else sum(item.amount for item in line_items)

        groq_data = self.groq.extract(text, state.get("groq_api_key"), state.get("groq_model", "openai/gpt-oss-120b")) if text else None
        if groq_data:
            claim_id = claim_id or groq_data.get("claim_id") or groq_data.get("invoice_number")
            patient_id = patient_id or groq_data.get("patient_id")
            provider_name = provider_name or groq_data.get("provider_name")
            if not dos:
                groq_date = groq_data.get("date_of_service")
                dos = self.parser.normalize_date(str(groq_date)) if isinstance(groq_date, str) else ""
            if not line_items:
                for item in groq_data.get("line_items", []) or []:
                    if isinstance(item, dict) and item.get("description") is not None:
                        try:
                            amount = float(item.get("amount", 0) or 0)
                        except (TypeError, ValueError):
                            amount = 0.0
                        line_items.append(LineItem(description=str(item["description"]), amount=amount))
            if total == 0:
                try:
                    total = float(groq_data.get("total_claimed_amount", 0) or 0)
                except (TypeError, ValueError):
                    total = 0.0

        extracted = ExtractedData(
            patient_id=str(patient_id or ""), provider_name=str(provider_name or ""),
            date_of_service=dos, total_claimed_amount=round(total, 2), line_items=line_items,
        )
        return {
            **state,
            "claim_id": claim_id,
            "extracted_data": extracted.model_dump(),
            "validation_flags": {
                "is_duplicate": False,
                "is_fraud_suspected": False,
                "has_policy_mismatch": False,
                "missing_documents": [],
            },
            "reasoning": [],
        }

    @staticmethod
    def _money(value: str) -> float:
        try:
            return float(Decimal(value.replace("$", "").replace(",", "").strip()))
        except (InvalidOperation, ValueError):
            return 0.0
