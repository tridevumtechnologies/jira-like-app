"""Project service — create, list, detail."""
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectMember, ProjectMemberRole
from app.schemas.project import CreateProjectRequest


async def create_project(
    payload: CreateProjectRequest, owner_id: uuid.UUID, db: AsyncSession
) -> Project:
    # Check key uniqueness
    existing = await db.execute(select(Project).where(Project.key == payload.key))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project key is already in use.",
            headers={"code": "PROJECT_KEY_TAKEN"},
        )

    project = Project(
        name=payload.name,
        key=payload.key,
        description=payload.description,
        owner_id=owner_id,
    )
    db.add(project)
    await db.flush()  # populate project.id before adding member

    # Auto-add creator as OWNER
    membership = ProjectMember(
        project_id=project.id,
        user_id=owner_id,
        role=ProjectMemberRole.OWNER,
    )
    db.add(membership)
    await db.commit()
    await db.refresh(project)
    return project


async def list_projects(user_id: uuid.UUID, db: AsyncSession) -> tuple[list[Project], int]:
    """Return all projects where the user is a member."""
    subq = select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)

    result = await db.execute(select(Project).where(Project.id.in_(subq)))
    projects = list(result.scalars().all())

    count_result = await db.execute(
        select(func.count()).select_from(Project).where(Project.id.in_(subq))
    )
    total = count_result.scalar_one()
    return projects, total


async def get_project(
    project_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> Project:
    """Return project detail; 403 if not member; 404 if not found."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    member = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    if not member.scalars().first():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return project


async def get_membership(
    project_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> ProjectMember | None:
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
        )
    )
    return result.scalars().first()
