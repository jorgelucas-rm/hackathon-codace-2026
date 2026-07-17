from fastapi import APIRouter

from src.app.controller.auth_controller import router as auth_router
from src.app.controller.company_controller import (
    admin_router as companies_admin_router,
    router as companies_router,
)
from src.app.controller.user_controller import (
    admin_router as users_admin_router,
    router as users_router,
)

router = APIRouter()
admin_router = APIRouter(prefix="/admin")

router.include_router(auth_router)

router.include_router(users_router)
admin_router.include_router(users_admin_router)

router.include_router(companies_router)
admin_router.include_router(companies_admin_router)
