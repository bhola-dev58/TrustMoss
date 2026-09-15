"""
auth.py — Enterprise JWT/OAuth2 Authentication & RBAC Layer for TrustMoss.

Enforces OWASP API Security standards:
1. Cryptographically signed JWT tokens (HS256).
2. Role-Based Access Control (RBAC):
   - 'agent': can execute queries and voice turns.
   - 'reviewer': can review and resolve HITL queue items.
   - 'admin': full governance, rollback, and index versioning permissions.
3. Configurable strict vs dev mode via AUTH_STRICT env variable.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

load_dotenv()
logger = logging.getLogger("trustmoss.auth")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "trustmoss_enterprise_secret_key_2026_x89a7f")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))
AUTH_STRICT = os.getenv("AUTH_STRICT", "false").lower() == "true"

security = HTTPBearer(auto_error=False)


class TokenRequest(BaseModel):
    client_id: str
    client_secret: str
    role: str = "agent"  # 'agent', 'reviewer', 'admin'


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    role: str
    client_id: str


def create_access_token(
    identity: str,
    role: str = "agent",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT token with claims."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": identity,
        "role": role,
        "iss": "trustmoss-gateway",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    encoded_jwt = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """Validate and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
            issuer="trustmoss-gateway",
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> dict:
    """
    FastAPI dependency for authenticating users/agents.
    In dev mode (AUTH_STRICT=false), allows unauthenticated requests as dev-admin.
    In strict mode (AUTH_STRICT=true), enforces valid signed JWT bearer tokens.
    """
    if not credentials:
        if AUTH_STRICT:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization bearer token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Default unauthenticated identity for local dev
        return {"sub": "dev-user", "role": "admin", "mode": "dev_permissive"}

    token = credentials.credentials
    payload = decode_access_token(token)
    return payload


def require_roles(allowed_roles: List[str]):
    """Role-Based Access Control (RBAC) dependency factory."""

    async def role_checker(user: dict = Depends(get_current_user)):
        user_role = user.get("role", "agent")
        if user_role not in allowed_roles and "admin" not in user_role:
            logger.warning(
                "Access denied for user=%s with role=%s. Required: %s",
                user.get("sub"),
                user_role,
                allowed_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: requires role in {allowed_roles}",
            )
        return user

    return role_checker
