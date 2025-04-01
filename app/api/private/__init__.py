from fastapi import APIRouter
from api.private.admins import router as admins_router
from api.private.issues import router as issues_router
from api.private.faq import router as faq_router

router = APIRouter()
router.include_router(admins_router)
router.include_router(issues_router)
router.include_router(faq_router)
