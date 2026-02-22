"""Tickets router — /api/v1/projects/{project_id}/tickets and /api/v1/tickets/*"""
import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.ticket import CreateTicketRequest, TicketResponse, UpdateTicketRequest
from app.services import ticket_service

# Mounted under /projects for creation & listing
project_tickets_router = APIRouter(tags=["tickets"])

# Mounted under /tickets for detail, update, delete
tickets_router = APIRouter(prefix="/tickets", tags=["tickets"])


@project_tickets_router.post(
    "/{project_id}/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    project_id: uuid.UUID,
    payload: CreateTicketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    ticket = await ticket_service.create_ticket(project_id, payload, current_user.id, db)
    return TicketResponse.model_validate(ticket)


@project_tickets_router.get(
    "/{project_id}/tickets",
    response_model=PaginatedResponse[TicketResponse],
)
async def list_tickets(
    project_id: uuid.UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedResponse[TicketResponse]:
    tickets, total = await ticket_service.list_tickets(project_id, current_user.id, skip, limit, db)
    return PaginatedResponse(
        items=[TicketResponse.model_validate(t) for t in tickets],
        total=total,
        skip=skip,
        limit=limit,
    )


@tickets_router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    ticket = await ticket_service.get_ticket(ticket_id, current_user.id, db)
    return TicketResponse.model_validate(ticket)


@tickets_router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    payload: UpdateTicketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    ticket = await ticket_service.update_ticket(ticket_id, payload, current_user.id, db)
    return TicketResponse.model_validate(ticket)


@tickets_router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await ticket_service.delete_ticket(ticket_id, current_user.id, db)
