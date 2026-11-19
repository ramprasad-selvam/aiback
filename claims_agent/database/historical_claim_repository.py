from copy import deepcopy
from typing import Any


class HistoricalClaimRepository:
    """Small in-memory repository; replace with SQL/NoSQL implementation later."""

    def __init__(self, claims: list[dict[str, Any]] | None = None) -> None:
        self._claims = deepcopy(claims or [])

    def find_by_patient_or_provider(self, patient_id: str = "", provider_name: str = "") -> list[dict[str, Any]]:
        return [
            deepcopy(claim)
            for claim in self._claims
            if (patient_id and claim.get("patient_id") == patient_id)
            or (provider_name and str(claim.get("provider_name", "")).casefold() == provider_name.casefold())
        ]
