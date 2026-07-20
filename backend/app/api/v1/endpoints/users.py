from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_roles
from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserRead

router = APIRouter()


@router.get(
    "/",
    response_model=List[UserRead],
    status_code=status.HTTP_200_OK,
    summary="List all users in the tenant company (Admin & SuperAdmin only)",
)
async def list_company_users(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> List[UserRead]:
    user_repo = UserRepository(db)
    users = await user_repo.get_all_by_company(current_user.company_id)
    return [UserRead.model_validate(u) for u in users]


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user within the tenant (Admin only)",
)
async def create_user_in_tenant(
    body: UserCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    user_repo = UserRepository(db)

    # Ensure admin can only create users within their own company (unless superadmin)
    if current_user.role != UserRole.SUPER_ADMIN and body.company_id != current_user.company_id:
        body.company_id = current_user.company_id

    existing = await user_repo.get_by_email(body.email)
    if existing:
        raise AppException(
            message=f"User with email '{body.email}' already exists.",
            status_code=status.HTTP_409_CONFLICT,
            error_code="USER_EMAIL_EXISTS",
        )

    user = await user_repo.create(
        email=body.email,
        hashed_password=get_password_hash(body.password),
        full_name=body.full_name,
        company_id=body.company_id,
        role=body.role,
    )

    return UserRead.model_validate(user)
