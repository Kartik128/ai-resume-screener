import uuid
from datetime import timedelta
import jwt
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterTenantRequest,
    TokenResponse,
)
from app.schemas.user import UserRead

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Company Tenant and Admin User",
)
async def register_tenant(
    body: RegisterTenantRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    company_repo = CompanyRepository(db)
    user_repo = UserRepository(db)

    # 1. Check existing company slug or user email
    existing_company = await company_repo.get_by_slug(body.company_slug)
    if existing_company:
        raise AppException(
            message=f"Company with slug '{body.company_slug}' already exists.",
            status_code=status.HTTP_409_CONFLICT,
            error_code="COMPANY_SLUG_EXISTS",
        )

    existing_user = await user_repo.get_by_email(body.email)
    if existing_user:
        raise AppException(
            message=f"User with email '{body.email}' already exists.",
            status_code=status.HTTP_409_CONFLICT,
            error_code="USER_EMAIL_EXISTS",
        )

    # 2. Create Company
    company = await company_repo.create(name=body.company_name, slug=body.company_slug)

    # 3. Create First User as Admin
    hashed_pwd = get_password_hash(body.password)
    user = await user_repo.create(
        email=body.email,
        hashed_password=hashed_pwd,
        full_name=body.full_name,
        company_id=company.id,
        role=UserRole.ADMIN,
    )

    # 4. Generate Tokens
    claims = {"role": user.role.value, "company_id": str(user.company_id)}
    access_token = create_access_token(subject=user.id, claims=claims)
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserRead.model_validate(user),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate User and return JWT Tokens",
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(body.email)

    if not user or not verify_password(body.password, user.hashed_password):
        raise UnauthorizedException(message="Invalid email or password")

    if not user.is_active:
        raise UnauthorizedException(message="Account is deactivated")

    user = await user_repo.update_last_login(user.id) or user

    claims = {"role": user.role.value, "company_id": str(user.company_id)}
    access_token = create_access_token(subject=user.id, claims=claims)
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserRead.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Issue new Access Token using Refresh Token",
)
async def refresh_tokens(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise UnauthorizedException(message="Invalid token type for refresh")
        user_id = uuid.UUID(payload.get("sub"))
    except jwt.PyJWTError:
        raise UnauthorizedException(message="Expired or invalid refresh token")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedException(message="User is invalid or deactivated")

    claims = {"role": user.role.value, "company_id": str(user.company_id)}
    new_access_token = create_access_token(subject=user.id, claims=claims)
    new_refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserRead.model_validate(user),
    )


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get current logged-in user profile",
)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
