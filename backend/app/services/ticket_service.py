"""Ticket service — create, list, detail, update, soft delete."""
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import ProjectMember, ProjectMemberRole
from app.models.ticket import Ticket
from app.schemas.ticket import CreateTicketRequest, UpdateTicketRequest
from app.services.project_service import get_project


async def _assert_member(
    project_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> ProjectMember:
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    membership = result.scalars().first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return membership


async def create_ticket(
    project_id: uuid.UUID,
    payload: CreateTicketRequest,
    reporter_id: uuid.UUID,
    db: AsyncSession,
) -> Ticket:
    # Verify project exists and user is a member
    project = await get_project(project_id, reporter_id, db)

    # If assignee provided, verify they are in the project
    if payload.assignee_id:
        assignee_check = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == payload.assignee_id,
            )
        )
        if not assignee_check.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assignee is not a member of this project.",
            )

    # Generate sequential ticket number for this project
    count_result = await db.execute(
        select(func.count()).select_from(Ticket).where(Ticket.project_id == project_id)
    )
    ticket_number = (count_result.scalar_one() or 0) + 1
    key = f"{project.key}-{ticket_number}"

    ticket = Ticket(
        key=key,
        ticket_number=ticket_number,
        title=payload.title,
        ticket_type=payload.ticket_type,
        priority=payload.priority,
        description=payload.description,
        assignee_id=payload.assignee_id,
        reporter_id=reporter_id,
        project_id=project_id,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def list_tickets(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    skip: int,
    limit: int,
    db: AsyncSession,
) -> tuple[list[Ticket], int]:
    # Verify membership / project existence
    await get_project(project_id, user_id, db)

    base_filter = (
        Ticket.project_id == project_id,
        Ticket.is_deleted.is_(False),
    )

    result = await db.execute(
        select(Ticket).where(*base_filter).offset(skip).limit(limit)
    )
    tickets = list(result.scalars().all())

    count_result = await db.execute(
        select(func.count()).select_from(Ticket).where(*base_filter)
    )
    total = count_result.scalar_one()
    return tickets, total


async def get_ticket(
    ticket_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> Ticket:
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.is_deleted.is_(False))
    )
    ticket = result.scalars().first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

    # Verify the caller is a member of the ticket's project
    await _assert_member(ticket.project_id, user_id, db)
    return ticket


async def update_ticket(
    ticket_id: uuid.UUID,
    payload: UpdateTicketRequest,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> Ticket:
    ticket = await get_ticket(ticket_id, user_id, db)

    # Permission: must be reporter, assignee, or OWNER/ADMIN
    membership = await _assert_member(ticket.project_id, user_id, db)
    is_privileged = membership.role in (ProjectMemberRole.OWNER, ProjectMemberRole.ADMIN)
    is_reporter = ticket.reporter_id == user_id
    is_assignee = ticket.assignee_id == user_id

    if not (is_privileged or is_reporter or is_assignee):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ticket, field, value)

    await db.commit()
    await db.refresh(ticket)
    return ticket


async def delete_ticket(
    ticket_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> None:
    ticket = await get_ticket(ticket_id, user_id, db)

    # Only OWNER or ADMIN can delete
    membership = await _assert_member(ticket.project_id, user_id, db)
    if membership.role not in (ProjectMemberRole.OWNER, ProjectMemberRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only project OWNERs or ADMINs can delete tickets.")

    ticket.is_deleted = True
    await db.commit()
