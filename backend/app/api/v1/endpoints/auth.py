import uuid
from datetime import timedelta
import jwt
from fastapi import APIRouter, Depends, status, Request
from pydantic import BaseModel
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
from app.schemas.user import UserRead, user_to_read_schema

router = APIRouter()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new Tenant Company and Admin User",
)
async def register(
    body: RegisterTenantRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    company_repo = CompanyRepository(db)
    user_repo = UserRepository(db)

    # 1. Check if user already exists
    existing_user = await user_repo.get_by_email(body.email)
    if existing_user:
        raise AppException(
            message=f"User with email '{body.email}' already exists.",
            status_code=status.HTTP_409_CONFLICT,
            error_code="USER_ALREADY_EXISTS",
        )

    # 2. Check if company slug already exists
    existing_company = await company_repo.get_by_slug(body.company_slug)
    if existing_company:
        raise AppException(
            message=f"Company slug '{body.company_slug}' is already taken.",
            status_code=status.HTTP_409_CONFLICT,
            error_code="COMPANY_SLUG_TAKEN",
        )

    # 3. Create Tenant Company & Admin User
    company = await company_repo.create(name=body.company_name, slug=body.company_slug)
    hashed_pwd = get_password_hash(body.password)
    user = await user_repo.create(
        email=body.email,
        hashed_password=hashed_pwd,
        full_name=body.full_name,
        company_id=company.id,
        role=UserRole.ADMIN,
    )

    # 4. Commit changes
    await db.commit()

    # 5. Generate Tokens
    claims = {"role": user.role.value, "company_id": str(user.company_id)}
    access_token = create_access_token(subject=user.id, claims=claims)
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_to_read_schema(user),
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
        user=user_to_read_schema(user),
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
            raise UnauthorizedException(message="Invalid refresh token type")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException(message="Invalid refresh token subject")

        user_id = uuid.UUID(user_id_str)
    except Exception as e:
        raise UnauthorizedException(message=f"Invalid or expired refresh token: {e}")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedException(message="User not found or inactive")

    claims = {"role": user.role.value, "company_id": str(user.company_id)}
    new_access_token = create_access_token(subject=user.id, claims=claims)
    new_refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_to_read_schema(user),
    )


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get Current Authenticated User profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    return user_to_read_schema(current_user)


@router.get(
    "/google",
    summary="Initiate Google OAuth2 consent redirection loop for Calendar integration",
)
async def google_oauth_redirect(
    user_id: str,
    request: Request,
):
    # Construct Google OAuth consent redirect URL dynamically
    redirect_uri = f"{request.base_url}api/v1/auth/google/callback"
    client_id = "mock-google-client-id.apps.googleusercontent.com"
    scopes = "https://www.googleapis.com/auth/calendar.events"
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scopes}&"
        f"state={user_id}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    return {"url": auth_url}


@router.get(
    "/google/callback",
    summary="Google OAuth2 authentication callback to store tokens securely",
)
async def google_oauth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    # In a production context, exchange the 'code' using OAuth Client Secret.
    # We will simulate token receipt and commit tokens directly to user profile.
    user_id = uuid.UUID(state)
    import datetime
    expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
    
    await db.execute(
        text("""
            UPDATE users 
            SET google_access_token = :at, google_refresh_token = :rt, google_token_expiry = :exp 
            WHERE id = :uid
        """),
        {
            "at": f"mock_access_token_{uuid.uuid4().hex[:12]}",
            "rt": f"mock_refresh_token_{uuid.uuid4().hex[:12]}",
            "exp": expiry,
            "uid": str(user_id)
        }
    )
    await db.commit()
    
    # HTML redirection back to the frontend Settings panel
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content="""
        <html>
            <body style="background-color: #020617; color: #f8fafc; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; flex-direction: column; gap: 16px;">
                <h2 style="margin:0; color:#10b981;">⚡ Google Calendar Connected!</h2>
                <p style="margin:0; font-size:14px; color:#94a3b8;">You can now close this tab. Returning to dashboard...</p>
                <script>
                    setTimeout(() => {
                        window.close();
                    }, 1500);
                </script>
            </body>
        </html>
    """)


@router.get(
    "/google/status",
    summary="Check connection status of current user's Google Calendar Integration",
)
async def check_google_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        text("SELECT google_access_token FROM users WHERE id = :uid"),
        {"uid": str(current_user.id)}
    )
    token = res.scalar_one_or_none()
    return {"connected": token is not None}


@router.get(
    "/microsoft/connect",
    summary="Initiate Microsoft Graph Outlook OAuth Flow",
)
async def microsoft_connect(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    # Simulated Microsoft Graph OAuth URL redirect
    tenant = "common"
    client_id = "mock_microsoft_client_id"
    redirect_uri = f"{request.base_url}api/v1/auth/microsoft/callback"
    state = str(current_user.id)
    scope = "offline_access Calendars.ReadWrite Mail.Send"
    
    url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&response_mode=query&scope={scope}&state={state}"
    return {"url": url}


@router.get(
    "/microsoft/callback",
    summary="Microsoft OAuth2 authentication callback to store tokens securely",
)
async def microsoft_oauth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    user_id = uuid.UUID(state)
    import datetime
    expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
    
    await db.execute(
        text("""
            UPDATE users 
            SET microsoft_access_token = :at, microsoft_refresh_token = :rt, microsoft_token_expiry = :exp, mail_provider = 'microsoft'
            WHERE id = :uid
        """),
        {
            "at": f"mock_ms_access_token_{uuid.uuid4().hex[:12]}",
            "rt": f"mock_ms_refresh_token_{uuid.uuid4().hex[:12]}",
            "exp": expiry,
            "uid": str(user_id)
        }
    )
    await db.commit()
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content="""
        <html>
            <body style="background-color: #020617; color: #f8fafc; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; flex-direction: column; gap: 16px;">
                <h2 style="margin:0; color:#10b981;">⚡ Outlook Integration Connected!</h2>
                <p style="margin:0; font-size:14px; color:#94a3b8;">You can now close this tab. Returning to dashboard...</p>
                <script>
                    setTimeout(() => {
                        window.close();
                    }, 1500);
                </script>
            </body>
        </html>
    """)


@router.get(
    "/microsoft/status",
    summary="Check connection status of current user's Outlook Integration",
)
async def check_microsoft_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        text("SELECT microsoft_access_token, mail_provider FROM users WHERE id = :uid"),
        {"uid": str(current_user.id)}
    )
    row = res.fetchone()
    connected = row[0] is not None if row else False
    active = row[1] if row else "smtp"
    return {"connected": connected, "active_provider": active}


class ProviderUpdateRequest(BaseModel):
    provider: str

@router.post(
    "/provider",
    summary="Update the active mail provider configuration",
)
async def update_mail_provider(
    body: ProviderUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if body.provider not in ["smtp", "google", "microsoft"]:
        raise HTTPException(status_code=400, detail="Invalid provider flag")
        
    await db.execute(
        text("UPDATE users SET mail_provider = :prov WHERE id = :uid"),
        {"prov": body.provider, "uid": str(current_user.id)}
    )
    await db.commit()
    return {"success": True, "active_provider": body.provider}
