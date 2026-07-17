from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.app.controller import admin_router, router
from src.infra.exception import DomainException, global_exception_handler
from src.infra.middleware import Middleware
from src.infra.middleware.rate_limiter import limiter

app = FastAPI(title="API - Hackathon Codace 2026", version="0.1.0")
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
