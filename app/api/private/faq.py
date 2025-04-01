from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models.faq import FAQCreate, FAQUpdate, FAQResponse
from services.faq_service import FAQService
from api.dependencies import get_faq_service

router = APIRouter(prefix="/faq", tags=["faq"])


@router.get("", response_model=List[FAQResponse])
async def get_all_faqs(faq_service: FAQService = Depends(get_faq_service)):
    """Get all FAQ entries"""
    faqs = await faq_service.get_all_faqs()

    return [
        FAQResponse(id=faq.id, question=faq.question, answer=faq.answer) for faq in faqs
    ]


@router.post("", response_model=FAQResponse, status_code=201)
async def create_faq(
    faq_data: FAQCreate, faq_service: FAQService = Depends(get_faq_service)
):
    """Create a new FAQ entry"""
    faq = await faq_service.create_faq(faq_data.question, faq_data.answer)

    if not faq:
        raise HTTPException(status_code=400, detail="Failed to create FAQ")

    return FAQResponse(id=faq.id, question=faq.question, answer=faq.answer)


@router.put("/{faq_id}", response_model=FAQResponse)
async def update_faq(
    faq_id: str, faq_data: FAQUpdate, faq_service: FAQService = Depends(get_faq_service)
):
    """Update an existing FAQ entry"""
    faq = await faq_service.update_faq(faq_id, faq_data.question, faq_data.answer)

    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    return FAQResponse(id=faq.id, question=faq.question, answer=faq.answer)


@router.delete("/{faq_id}")
async def delete_faq(faq_id: str, faq_service: FAQService = Depends(get_faq_service)):
    """Delete an FAQ entry"""
    deleted = await faq_service.delete_faq(faq_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="FAQ not found")

    return {"message": "Deleted"}
