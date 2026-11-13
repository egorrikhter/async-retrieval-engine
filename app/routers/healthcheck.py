from fastapi import APIRouter, status

from app.models import HealthCheck

router = APIRouter()


@router.get("/healthcheck", status_code=status.HTTP_200_OK, response_model=HealthCheck)
async def get_health() -> HealthCheck:
    return HealthCheck(status="OK")
