import uuid
from typing import Callable, List
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository

security_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise UnauthorizedException(message="Invalid token type")
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException(message="Invalid token claims")
        user_id = uuid.UUID(user_id_str)
    except jwt.PyJWTError:
        raise UnauthorizedException(message="Could not validate credentials or token expired")
    except ValueError:
        raise UnauthorizedException(message="Invalid user identifier format")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException(message="User no longer exists")
    if not user.is_active:
        raise ForbiddenException(message="User account is deactivated")
    if not user.company.is_active:
        raise ForbiddenException(message="Company tenant account is deactivated")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


def require_roles(allowed_roles: List[UserRole]) -> Callable:
    """Dependency factory for Role-Based Access Control (RBAC)."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and current_user.role != UserRole.SUPER_ADMIN:
            raise ForbiddenException(
                message=f"Role '{current_user.role.value}' does not have permission for this resource"
            )
        return current_user

    return role_checker
