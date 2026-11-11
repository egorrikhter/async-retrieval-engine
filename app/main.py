from fastapi import FastAPI

from app.routers.healthcheck import router as healthcheck_router

app = FastAPI()

app.include_router(healthcheck_router)
