"""FastAPI router for user authentication endpoints."""

from fastapi import APIRouter, Response
from pydantic import BaseModel
import structlog
import secrets

logger = structlog.get_logger()

router = APIRouter(prefix="/api", tags=["users"])


class UserLoginRequest(BaseModel):
    """User login request."""

    email: str


class UserLoginResponse(BaseModel):
    """User login response."""

    user_id: str
    email: str


@router.post("/users")
async def login_user(request: UserLoginRequest, response: Response) -> UserLoginResponse:
    """Login user with email (demo-only, no password required).

    POST /api/users
    Content-Type: application/json

    Request body:
    {
      "email": "user@example.com"
    }

    Returns:
    {
      "user_id": "user_abc123...",
      "email": "user@example.com"
    }

    Sets HTTP-only cookie: __punk-userid
    """
    # Generate a simple user ID based on email hash
    email_hash = secrets.token_hex(8)
    user_id = f"user_{email_hash}"

    # Set secure HTTP-only cookie (valid for 24 hours)
    response.set_cookie(
        key="__punk-userid",
        value=user_id,
        max_age=86400,  # 24 hours
        secure=False,  # Set to True in production with HTTPS
        httponly=True,
        samesite="lax",
        path="/",
    )

    logger.info("user_logged_in", user_id=user_id, email=request.email)

    return UserLoginResponse(user_id=user_id, email=request.email)


@router.post("/users/logout")
async def logout_user(response: Response) -> dict:
    """Logout user - clear cookie.

    POST /api/users/logout

    Returns:
    {
      "status": "logged_out"
    }

    Clears HTTP-only cookie: __punk-userid
    """
    # Delete the cookie by setting max_age to 0
    response.delete_cookie(
        key="__punk-userid",
        path="/",
    )

    logger.info("user_logged_out")

    return {"status": "logged_out"}


@router.get("/users/profile")
async def get_profile() -> dict:
    """Get current user profile (placeholder).

    GET /api/users/profile

    Returns:
    {
      "user_id": "user_abc123...",
      "email": "user@example.com"
    }
    """
    # In a real system, this would read the __punk-userid cookie
    # and fetch user data from the database
    return {
        "user_id": "user_demo",
        "email": "demo@example.com",
    }
