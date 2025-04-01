from fastapi import APIRouter
from api.public.issues import router as issues_router

router = APIRouter()
router.include_router(issues_router)
