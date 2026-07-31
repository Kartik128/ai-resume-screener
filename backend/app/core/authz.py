import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User, UserRole

# Define standard permissions
class Permissions:
    ORG_READ = "organization.read"
    ORG_MANAGE = "organization.manage"
    USERS_INVITE = "users.invite"
    USERS_MANAGE = "users.manage"
    JOBS_CREATE = "jobs.create"
    JOBS_READ = "jobs.read"
    JOBS_UPDATE = "jobs.update"
    CANDIDATES_READ = "candidates.read"
    CANDIDATES_DOWNLOAD = "candidates.download"
    CANDIDATES_EXPORT = "candidates.export"
    CANDIDATES_UPDATE_STAGE = "candidates.update_stage"
    AI_EVALUATE = "ai.evaluate"
    SCORECARDS_MANAGE = "scorecards.manage"
    INTERVIEWS_FEEDBACK_WRITE = "interviews.feedback_write"
    REPORTS_READ = "reports.read"
    AUDIT_LOGS_READ = "audit_logs.read"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"


# Centralized authorization manager
class AuthzManager:
    def __init__(self, user: User, db: AsyncSession):
        self.user = user
        self.db = db

    async def check_permission(
        self,
        permission: str,
        job_id: Optional[uuid.UUID] = None,
        candidate_id: Optional[uuid.UUID] = None
    ) -> bool:
        # Super admin always has bypass access
        if self.user.role == UserRole.SUPER_ADMIN:
            return True

        # 1. Organization Owner has absolute authority within the company
        if self.user.role == UserRole.ADMIN:
            # Check owner level restrictions
            if permission == Permissions.DATA_DELETE or permission == Permissions.AUDIT_LOGS_READ or permission == Permissions.ORG_MANAGE:
                # In this simplified model, global admins act as Organization Owners
                return True
            # General admin access
            return permission not in []

        # 2. Candidate Job scope verification
        if candidate_id and not job_id:
            # Retrieve associated job ID for candidate
            cand_res = await self.db.execute(
                text("SELECT job_id FROM applications WHERE candidate_id = :cid AND company_id = :comp"),
                {"cid": str(candidate_id), "comp": str(self.user.company_id)}
            )
            row = cand_res.fetchone()
            if row:
                job_id = uuid.UUID(row[0])

        # 3. Check Job Requisition assignments
        assignment_role = None
        if job_id:
            res = await self.db.execute(
                text("""
                    SELECT role, expires_at FROM job_assignments 
                    WHERE company_id = :comp AND user_id = :uid AND job_id = :jid
                """),
                {"comp": str(self.user.company_id), "uid": str(self.user.id), "jid": str(job_id)}
            )
            row = res.fetchone()
            if row:
                role, expires = row[0], row[1]
                # Expiration validation (temporary permissions)
                if expires:
                    expiry_dt = datetime.fromisoformat(expires) if isinstance(expires, str) else expires
                    if expiry_dt.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                        return False # Expired access
                assignment_role = role

        # Fallback to user global role if no specific job assignment exists
        effective_role = assignment_role or self.user.role.value

        # Global Role-based mapping
        if effective_role == "hr_admin" or effective_role == "admin":
            return permission not in [Permissions.DATA_DELETE, Permissions.ORG_MANAGE]
        elif effective_role == "recruiter":
            return permission in [
                Permissions.ORG_READ, Permissions.JOBS_CREATE, Permissions.JOBS_READ,
                Permissions.JOBS_UPDATE, Permissions.CANDIDATES_READ, Permissions.CANDIDATES_DOWNLOAD,
                Permissions.CANDIDATES_UPDATE_STAGE, Permissions.AI_EVALUATE,
                Permissions.SCORECARDS_MANAGE, Permissions.INTERVIEWS_FEEDBACK_WRITE
            ]
        elif effective_role == "hiring_manager":
            return permission in [
                Permissions.ORG_READ, Permissions.JOBS_READ, Permissions.CANDIDATES_READ,
                Permissions.INTERVIEWS_FEEDBACK_WRITE
            ]
        elif effective_role == "interviewer":
            return permission in [
                Permissions.CANDIDATES_READ, Permissions.INTERVIEWS_FEEDBACK_WRITE
            ]
        elif effective_role == "viewer":
            return permission in [Permissions.ORG_READ, Permissions.JOBS_READ, Permissions.CANDIDATES_READ]

        return False


# Dependency injector for permission enforcement
def require_permission(permission: str):
    async def dependency(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> AuthzManager:
        # Try to extract job_id or candidate_id from request path/query
        job_id = None
        candidate_id = None

        path_params = request.path_params
        if "job_id" in path_params:
            try:
                job_id = uuid.UUID(path_params["job_id"])
            except ValueError:
                pass
        if "candidate_id" in path_params:
            try:
                candidate_id = uuid.UUID(path_params["candidate_id"])
            except ValueError:
                pass

        authz = AuthzManager(current_user, db)
        allowed = await authz.check_permission(permission, job_id=job_id, candidate_id=candidate_id)

        # Log log attempts inside DB
        await log_audit_event(
            db=db,
            company_id=current_user.company_id,
            actor_id=current_user.id,
            action=permission,
            object_type="API_Resource",
            object_id=job_id or candidate_id,
            result="SUCCESS" if allowed else "DENIED",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Insufficient privileges for this resource"
            )
        return authz

    return dependency


# Centralized audit logging utility
async def log_audit_event(
    db: AsyncSession,
    company_id: uuid.UUID,
    actor_id: Optional[uuid.UUID],
    action: str,
    object_type: str,
    object_id: Optional[uuid.UUID],
    result: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    before_state: Optional[str] = None,
    after_state: Optional[str] = None
):
    await db.execute(
        text("""
            INSERT INTO audit_events 
              (id, company_id, actor_id, action, object_type, object_id, result, ip_address, user_agent, before_state, after_state)
            VALUES 
              (:id, :comp, :actor, :act, :obj_type, :obj_id, :res, :ip, :ua, :before, :after)
        """),
        {
            "id": str(uuid.uuid4()),
            "comp": str(company_id),
            "actor": str(actor_id) if actor_id else None,
            "act": action,
            "obj_type": object_type,
            "obj_id": str(object_id) if object_id else None,
            "res": result,
            "ip": ip_address,
            "ua": user_agent,
            "before": before_state,
            "after": after_state
        }
    )
    await db.commit()
