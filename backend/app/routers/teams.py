from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
from pydantic import BaseModel

from app.database import get_db
from app.models.team import Team, TeamMember
from app.models.project import Project
from app.models.user import User
from app.auth import require_admin, get_current_user

router = APIRouter(tags=["teams"])


# ---------- Schemas ----------

class TeamMemberOut(BaseModel):
    id: int
    user_id: int
    name: Optional[str] = None
    designation: Optional[str] = None

    class Config:
        from_attributes = True


class TeamOut(BaseModel):
    id: int
    project_id: int
    name: str
    team_lead_id: Optional[int] = None
    team_lead_name: Optional[str] = None
    members: List[TeamMemberOut] = []

    class Config:
        from_attributes = True


class TeamUpdate(BaseModel):
    team_lead_id: Optional[int] = None


class TeamMemberAdd(BaseModel):
    user_id: int


# ---------- Helpers ----------

def _serialize_team(team: Team) -> dict:
    return {
        "id": team.id,
        "project_id": team.project_id,
        "name": team.name,
        "team_lead_id": team.team_lead_id,
        "team_lead_name": team.team_lead.name if team.team_lead else None,
        "members": [
            {
                "id": m.id,
                "user_id": m.user_id,
                "name": m.user.name if m.user else None,
                "designation": getattr(m.user, "designation", None) if m.user else None,
            }
            for m in team.members
        ],
    }


async def _load_project_teams(db: AsyncSession, project_id: int) -> List[Team]:
    res = await db.execute(
        select(Team)
        .options(
            selectinload(Team.members).selectinload(TeamMember.user),
            selectinload(Team.team_lead),
        )
        .where(Team.project_id == project_id)
        .order_by(Team.id)
    )
    return list(res.scalars().all())


async def _user_already_on_project(db: AsyncSession, project_id: int, user_id: int) -> bool:
    res = await db.execute(
        select(TeamMember.id)
        .join(Team, Team.id == TeamMember.team_id)
        .where(Team.project_id == project_id, TeamMember.user_id == user_id)
        .limit(1)
    )
    return res.scalar_one_or_none() is not None


# ---------- Admin endpoints ----------

@router.get("/projects/{project_id}/teams")
async def list_project_teams(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    teams = await _load_project_teams(db, project_id)
    return [_serialize_team(t) for t in teams]


@router.post("/projects/{project_id}/teams", status_code=201)
async def create_project_team(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    proj = (await db.execute(select(Project).where(Project.id == project_id))).scalar_one_or_none()
    if not proj:
        raise HTTPException(404, "Project not found")

    count = (await db.execute(
        select(func.count(Team.id)).where(Team.project_id == project_id)
    )).scalar_one()
    team = Team(project_id=project_id, name=f"Team {count + 1}")
    db.add(team)
    await db.commit()
    await db.refresh(team)

    res = await db.execute(
        select(Team)
        .options(
            selectinload(Team.members).selectinload(TeamMember.user),
            selectinload(Team.team_lead),
        )
        .where(Team.id == team.id)
    )
    return _serialize_team(res.scalar_one())


@router.patch("/projects/{project_id}/teams/{team_id}")
async def update_team(
    project_id: int,
    team_id: int,
    data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    team = (await db.execute(
        select(Team).where(Team.id == team_id, Team.project_id == project_id)
    )).scalar_one_or_none()
    if not team:
        raise HTTPException(404, "Team not found")

    if data.team_lead_id is not None:
        # team lead must be a member of this team
        is_member = (await db.execute(
            select(TeamMember.id)
            .where(TeamMember.team_id == team_id, TeamMember.user_id == data.team_lead_id)
        )).scalar_one_or_none()
        if not is_member:
            raise HTTPException(400, "Team lead must be a member of this team")
        team.team_lead_id = data.team_lead_id
    else:
        team.team_lead_id = None

    await db.commit()
    res = await db.execute(
        select(Team)
        .options(
            selectinload(Team.members).selectinload(TeamMember.user),
            selectinload(Team.team_lead),
        )
        .where(Team.id == team_id)
    )
    return _serialize_team(res.scalar_one())


@router.delete("/projects/{project_id}/teams/{team_id}", status_code=204)
async def delete_team(
    project_id: int,
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    team = (await db.execute(
        select(Team).where(Team.id == team_id, Team.project_id == project_id)
    )).scalar_one_or_none()
    if not team:
        raise HTTPException(404, "Team not found")
    await db.delete(team)
    await db.commit()

    # Renumber remaining teams sequentially so display stays Team 1, 2, 3...
    remaining = (await db.execute(
        select(Team).where(Team.project_id == project_id).order_by(Team.id)
    )).scalars().all()
    for i, t in enumerate(remaining, 1):
        t.name = f"Team {i}"
    await db.commit()


@router.post("/projects/{project_id}/teams/{team_id}/members", status_code=201)
async def add_team_member(
    project_id: int,
    team_id: int,
    data: TeamMemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    team = (await db.execute(
        select(Team).where(Team.id == team_id, Team.project_id == project_id)
    )).scalar_one_or_none()
    if not team:
        raise HTTPException(404, "Team not found")

    user = (await db.execute(select(User).where(User.id == data.user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    if await _user_already_on_project(db, project_id, data.user_id):
        raise HTTPException(400, "Employee is already on another team for this project")

    member = TeamMember(team_id=team_id, user_id=data.user_id)
    db.add(member)
    await db.commit()

    res = await db.execute(
        select(Team)
        .options(
            selectinload(Team.members).selectinload(TeamMember.user),
            selectinload(Team.team_lead),
        )
        .where(Team.id == team_id)
    )
    return _serialize_team(res.scalar_one())


@router.delete("/projects/{project_id}/teams/{team_id}/members/{member_id}", status_code=204)
async def remove_team_member(
    project_id: int,
    team_id: int,
    member_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_admin),
):
    member = (await db.execute(
        select(TeamMember)
        .join(Team, Team.id == TeamMember.team_id)
        .where(TeamMember.id == member_id, Team.id == team_id, Team.project_id == project_id)
    )).scalar_one_or_none()
    if not member:
        raise HTTPException(404, "Member not found")

    # If this user was the team lead, clear it
    team = (await db.execute(select(Team).where(Team.id == team_id))).scalar_one()
    if team.team_lead_id == member.user_id:
        team.team_lead_id = None

    await db.delete(member)
    await db.commit()


# ---------- Employee endpoint ----------

@router.get("/me/projects/{project_id}/team")
async def get_my_team_for_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return the team (with members) the current user belongs to on this project,
    or null if they're not on any team for it."""
    res = await db.execute(
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .options(
            selectinload(Team.members).selectinload(TeamMember.user),
            selectinload(Team.team_lead),
        )
        .where(Team.project_id == project_id, TeamMember.user_id == current_user.id)
        .limit(1)
    )
    team = res.scalar_one_or_none()
    if not team:
        return None
    return _serialize_team(team)
