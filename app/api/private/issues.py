from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models.issue import IssueResponse, MessageCreate, IssueWithMessages, Issue
from services.issue_service import IssueService
from api.dependencies import get_issue_service

router = APIRouter(prefix="/issues", tags=["issues"])


@router.get("", response_model=List[IssueResponse])
async def get_all_issues(issue_service: IssueService = Depends(get_issue_service)):
    """Get all issues (open and closed)"""
    issues = await issue_service.get_all_issues()

    return [IssueResponse(issue_id=issue.id, status=issue.status) for issue in issues]


@router.get("/manual", response_model=List[IssueResponse])
async def get_manual_issues(issue_service: IssueService = Depends(get_issue_service)):
    """Get only issues in manual mode"""
    issues = await issue_service.get_manual_issues()

    return [IssueResponse(issue_id=issue.id, status=issue.status) for issue in issues]


@router.get("/{issue_id}", response_model=Issue)
async def get_issue(
    issue_id: str, issue_service: IssueService = Depends(get_issue_service)
):
    """Get a specific issue by ID"""
    issue = await issue_service.get_issue(issue_id)

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    return issue


@router.get("/{issue_id}/messages", response_model=IssueWithMessages)
async def get_issue_messages(
    issue_id: str, issue_service: IssueService = Depends(get_issue_service)
):
    """Get all messages in an issue"""
    issue = await issue_service.get_issue(issue_id)
    issue_messages = await issue_service.get_messages(issue_id)

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    return IssueWithMessages(issue_id=issue.id, messages=issue_messages.messages)


@router.post("/{issue_id}/messages")
async def add_admin_message(
    issue_id: str,
    message_data: MessageCreate,
    issue_service: IssueService = Depends(get_issue_service),
):
    """Add admin message to an issue"""
    # Get issue
    issue = await issue_service.get_issue(issue_id)

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    # Add admin message
    updated_issue = await issue_service.add_admin_message(
        issue_id, "Admin", message_data.message
    )

    if not updated_issue:
        raise HTTPException(status_code=500, detail="Failed to add message")

    return {"message": "Message sent"}


@router.post("/{issue_id}/close")
async def close_issue(
    issue_id: str, issue_service: IssueService = Depends(get_issue_service)
):
    """Close an issue"""
    # Get issue
    issue = await issue_service.get_issue(issue_id)

    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if issue.status == "closed":
        raise HTTPException(status_code=400, detail="Issue is already closed")

    # Close issue
    updated_issue = await issue_service.close_issue(issue_id)

    if not updated_issue:
        raise HTTPException(status_code=500, detail="Failed to close issue")

    return {"status": "closed"}
