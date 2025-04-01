from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from models.issue import IssueCreate, IssueResponse, MessageCreate, MessageResponse
from services.issue_service import IssueService
from api.dependencies import get_issue_service

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("/{telegram_chat_id}", response_model=IssueResponse)
async def check_open_issue(
    telegram_chat_id: str, issue_service: IssueService = Depends(get_issue_service)
):
    """Check if user has an open issue"""
    issue = await issue_service.get_open_issue(telegram_chat_id)

    if not issue:
        raise HTTPException(status_code=404, detail="No open issue found")

    return IssueResponse(issue_id=issue.id, status=issue.status)


@router.post("", response_model=IssueResponse, status_code=201)
async def create_issue(
    issue_data: IssueCreate, issue_service: IssueService = Depends(get_issue_service)
):
    """Create a new issue"""
    # Check if user already has an open issue
    existing_issue = await issue_service.get_open_issue(issue_data.telegram_chat_id)

    if existing_issue:
        raise HTTPException(status_code=400, detail="User already has an open issue")

    # Create new issue
    issue = await issue_service.create_issue(
        issue_data.telegram_chat_id, issue_data.username
    )

    return IssueResponse(issue_id=issue.id, status=issue.status)


@router.post("/{issue_id}/messages", response_model=Optional[MessageResponse])
async def add_user_message(
    issue_id: str,
    message_data: MessageCreate,
    issue_service: IssueService = Depends(get_issue_service),
):
    """Add a message to an issue and get automatic GPT response"""
    # Get issue
    issue = await issue_service.get_issue(issue_id)

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if issue.status == "closed":
        raise HTTPException(status_code=403, detail="Issue is closed")

    # Add message and get response
    result = await issue_service.add_user_message(
        issue_id, issue.username, message_data.message
    )

    return result


@router.put("/{issue_id}/manual", response_model=IssueResponse)
async def switch_to_manual(
    issue_id: str, issue_service: IssueService = Depends(get_issue_service)
):
    """Switch issue to manual support mode"""
    # Get issue
    issue = await issue_service.get_issue(issue_id)

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if issue.status != "open":
        raise HTTPException(
            status_code=400, detail="Issue is already in manual mode or closed"
        )

    # Switch to manual mode
    updated_issue = await issue_service.switch_to_manual(issue_id)

    if not updated_issue:
        raise HTTPException(status_code=500, detail="Failed to switch to manual mode")

    return IssueResponse(issue_id=updated_issue.id, status=updated_issue.status)
