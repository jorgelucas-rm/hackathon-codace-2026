import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.app.controller import admin_router, router
from src.app.jobs.notification_job import run_loop
from src.app.service.sport_service import seed_sports
from src.app.service.user_service import seed_avatars
from src.db.seed_demo import seed_demo
from src.environments import MINIO_DEFAULT_BUCKET, SEED_DEMO
from src.infra.exception import DomainException, global_exception_handler
from src.infra.middleware import Middleware
from src.infra.middleware.rate_limiter import limiter
from src.infra.storage import get_minio_client
from src.infra.storage.database import session_maker


@asynccontextmanager
async def lifespan(_: FastAPI):
    session = session_maker()
    try:
        seed_sports(session)
        if SEED_DEMO:
            seed_demo(session)
    finally:
        session.close()

    seed_avatars(get_minio_client(), MINIO_DEFAULT_BUCKET)

    job_task = asyncio.create_task(run_loop(session_maker))
    try:
        yield
    finally:
        job_task.cancel()


app = FastAPI(title="API - Hackathon Codace 2026", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter

app.add_exception_handler(RateLimitExceeded, global_exception_handler)
app.add_exception_handler(RequestValidationError, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, global_exception_handler)
app.add_exception_handler(DomainException, global_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

Middleware().register_middlewares(app)

app.include_router(router=router, prefix="/api")
app.include_router(router=admin_router, prefix="/api")


@app.get("/api")
async def get_root():
    return "v0.1"
