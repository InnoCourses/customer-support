from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models.admin import AdminCreate, Admin
from services.admin_service import AdminService
from api.dependencies import get_admin_service

router = APIRouter(prefix="/admins", tags=["admins"])


@router.get("", response_model=List[Admin])
async def get_all_admins(admin_service: AdminService = Depends(get_admin_service)):
    """Get all registered admins"""
    return await admin_service.get_all_admins()


@router.post("", response_model=Admin, status_code=201)
async def register_admin(
    admin_data: AdminCreate, admin_service: AdminService = Depends(get_admin_service)
):
    """Register a new admin"""
    admin = await admin_service.create_admin(
        admin_data.telegram_chat_id, admin_data.username
    )

    if not admin:
        raise HTTPException(status_code=400, detail="Admin already registered")

    return admin
