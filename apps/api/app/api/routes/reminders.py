from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import Principal, get_principal, resolve_user_id
from app.api.schemas_phase34 import ReminderCreateBody, ReminderResponse
from app.services.reminder_service import ReminderService

router = APIRouter(prefix="/v1/reminders", tags=["reminders"])


def get_reminder_service(request: Request) -> ReminderService:
    service = getattr(request.app.state, "reminder_service", None)
    if service is None:
        raise HTTPException(status_code=503, detail="Reminder service unavailable")
    return service


@router.post("", response_model=ReminderResponse, status_code=201)
async def create_reminder(
    body: ReminderCreateBody,
    principal: Annotated[Principal, Depends(get_principal)],
    reminders: Annotated[ReminderService, Depends(get_reminder_service)],
) -> ReminderResponse:
    user_id = resolve_user_id(principal, body.user_id)
    reminder = await reminders.schedule(
        clerk_user_id=user_id,
        title=body.title,
        body=body.body,
        due_at=body.due_at,
    )
    return ReminderResponse(
        id=reminder.id,
        user_id=reminder.user_id,
        title=reminder.title,
        body=reminder.body,
        due_at=reminder.due_at,
        status=reminder.status,
        workflow_id=reminder.workflow_id,
    )


@router.get("", response_model=list[ReminderResponse])
async def list_reminders(
    principal: Annotated[Principal, Depends(get_principal)],
    reminders: Annotated[ReminderService, Depends(get_reminder_service)],
    user_id: str | None = None,
) -> list[ReminderResponse]:
    resolved = resolve_user_id(principal, user_id)
    items = await reminders.list_for_user(resolved)
    return [
        ReminderResponse(
            id=item.id,
            user_id=item.user_id,
            title=item.title,
            body=item.body,
            due_at=item.due_at,
            status=item.status,
            workflow_id=item.workflow_id,
        )
        for item in items
    ]
