from typing import Any

from ..models import ClaimInput
from ..orchestration import evaluate_claim


class ClaimsService:
    """Application service boundary for claim evaluation."""

    def evaluate(self, payload: ClaimInput | dict[str, Any]) -> dict[str, Any]:
        return evaluate_claim(payload)
