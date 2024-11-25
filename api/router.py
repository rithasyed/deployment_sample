from fastapi import APIRouter
from api.v1 import endpoints_router, symbols_router

router = APIRouter()

router.include_router(endpoints_router,prefix="")
router.include_router(symbols_router,prefix="")
