import re
from datetime import datetime


class ParsingTool:
    @staticmethod
    def extract_labeled(text: str, labels: tuple[str, ...]) -> str:
        pattern = r"(?im)^\s*(?:" + "|".join(re.escape(label) for label in labels) + r")\s*[:=-]\s*(.+?)\s*$"
        match = re.search(pattern, text)
        return match.group(1).strip() if match else ""

    @staticmethod
    def normalize_date(value: str) -> str:
        if not value:
            return ""
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"):
            try:
                return datetime.strptime(value, fmt).date().isoformat()
            except ValueError:
                continue
        return ""

    @staticmethod
    def extract_icd_codes(text: str) -> list[str]:
        matches = re.findall(r"(?i)\b[A-TV-Z][0-9][0-9A-Z](?:\.[0-9A-Z]{1,4})?\b", text)
        return list(dict.fromkeys(code.upper() for code in matches))
