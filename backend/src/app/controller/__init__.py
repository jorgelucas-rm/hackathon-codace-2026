from fastapi import APIRouter

from src.app.controller.auth_controller import router as auth_router
from src.app.controller.availability_controller import router as availability_router
from src.app.controller.booking_admin_controller import (
    blocks_router as booking_blocks_router,
    bookings_admin_router as booking_admin_router,
    manual_bookings_router as manual_bookings_router,
)
from src.app.controller.booking_controller import (
    me_router as bookings_me_router,
    router as bookings_router,
)
from src.app.controller.company_controller import (
    admin_router as companies_admin_router,
    router as companies_router,
)
from src.app.controller.company_schedule_controller import (
    router as company_schedule_router,
)
from src.app.controller.court_controller import (
    me_router as courts_me_router,
    router as courts_router,
)
from src.app.controller.group_controller import router as groups_router
from src.app.controller.payment_controller import router as payments_router
from src.app.controller.sport_controller import router as sports_router
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

router.include_router(courts_me_router)
router.include_router(courts_router)
router.include_router(sports_router)

router.include_router(bookings_router)
router.include_router(bookings_me_router)
router.include_router(availability_router)
router.include_router(payments_router)

router.include_router(groups_router)

router.include_router(company_schedule_router)
router.include_router(booking_blocks_router)
router.include_router(manual_bookings_router)
router.include_router(booking_admin_router)
