from ..database.historical_claim_repository import HistoricalClaimRepository
from ..tools.groq_tool import GroqExtractorTool


class ClaimAgentFactory:
    """Composes claim-processing dependencies for an evaluation run."""

    def __init__(self) -> None:
        self.groq_tool = GroqExtractorTool()

    def historical_claim_repository(self, claims: list[dict] | None = None) -> HistoricalClaimRepository:
        return HistoricalClaimRepository(claims)
