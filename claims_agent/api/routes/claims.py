from fastapi import APIRouter

from ...models import ClaimInput
from ...services.claims_service import ClaimsService


router = APIRouter(prefix="/claims", tags=["claims"])
service = ClaimsService()


@router.post("/evaluate")
async def evaluate(payload: ClaimInput) -> dict:
    return service.evaluate(payload)
