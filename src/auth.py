"""Authentication and security utilities for remote MCP server.

This module provides JWT token authentication, API key validation,
and security middleware for protecting the remote MCP endpoints.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sys
from typing import Any

# Check if auth dependencies are available
try:
    from fastapi import Depends, HTTPException, Request, status
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    from jose import JWTError, jwt
    from passlib.context import CryptContext
    from pydantic import BaseModel

    AUTH_DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    # Graceful fallback when auth dependencies are not installed
    print(f"Warning: Auth dependencies not available - {e}", file=sys.stderr)
    print("Install with: make install-web", file=sys.stderr)
    AUTH_DEPENDENCIES_AVAILABLE = False

    # Minimal fallback implementations
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    def Depends(dependency):  # noqa: N802
        """Fallback Depends decorator"""
        return dependency

    class HTTPException(Exception):  # noqa: N818
        def __init__(self, status_code: int, detail: str, headers: dict = None):
            self.status_code = status_code
            self.detail = detail
            self.headers = headers or {}
            super().__init__(detail)

    # Type aliases for when imports fail
    Request = Any
    HTTPAuthorizationCredentials = Any

from src.config import Config


class TokenData(BaseModel):
    """Token payload data model."""

    if AUTH_DEPENDENCIES_AVAILABLE:
        username: str | None = None
        scopes: list[str] = []
    else:

        def __init__(self, username: str | None = None, scopes: list[str] = None):
            self.username = username
            self.scopes = scopes or []


class User(BaseModel):
    """User data model."""

    if AUTH_DEPENDENCIES_AVAILABLE:
        username: str
        scopes: list[str] = []
        is_active: bool = True
    else:

        def __init__(self, username: str, scopes: list[str] = None, is_active: bool = True):
            self.username = username
            self.scopes = scopes or []
            self.is_active = is_active


class AuthErrorMessages:
    """Centralized auth error messages."""

    INVALID_CREDENTIALS = "Could not validate credentials"
    API_KEY_REQUIRED = "API key required"
    INVALID_API_KEY = "Invalid API key"
    AUTH_REQUIRED = "Authentication required. Provide JWT token, API key, or OAuth."
    INACTIVE_USER = "Inactive user"
    DEPENDENCIES_MISSING = "Auth dependencies not available. Install with: make install-web"


def check_auth_dependencies():
    """Check if auth dependencies are available, raise error if not."""
    if not AUTH_DEPENDENCIES_AVAILABLE:
        raise RuntimeError(AuthErrorMessages.DEPENDENCIES_MISSING)


# Auth utilities - conditional implementations
if AUTH_DEPENDENCIES_AVAILABLE:
    # Password hashing context
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    # HTTP Bearer token security
    security = HTTPBearer(auto_error=False)

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)

    def create_access_token(data: dict, expires_delta: timedelta | None = None, config: Config | None = None) -> str:
        """Create a JWT access token."""
        if config is None:
            config = Config.from_env()

        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        return encoded_jwt

    def verify_token(token: str, config: Config | None = None) -> TokenData:
        """Verify and decode a JWT token."""
        if config is None:
            config = Config.from_env()

        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
            username: str | None = payload.get("sub")
            if username is None:
                raise credentials_exception
            scopes: list[str] = payload.get("scopes", [])
            token_data = TokenData(username=username, scopes=scopes)
        except JWTError as jwt_exc:
            raise credentials_exception from jwt_exc

        return token_data

    async def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(security), config: Config = Depends(Config.from_env)
    ) -> User:
        """Get current authenticated user from JWT token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if not credentials:
            raise credentials_exception

        token_data = verify_token(credentials.credentials, config)

        # For this implementation, we'll create a simple user
        # In production, you'd lookup the user from a database
        user = User(username=token_data.username or "anonymous", scopes=token_data.scopes, is_active=True)

        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")

        return user

    async def verify_api_key(request: Request, config: Config = Depends(Config.from_env)) -> bool:
        """Verify API key from request headers."""
        api_key = request.headers.get(config.API_KEY_HEADER)

        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required",
                headers={config.API_KEY_HEADER: "Required"},
            )

        # Simple API key validation - in production, use a database or key management service
        if api_key != config.DEFAULT_API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )

        return True

    class AuthBackend:
        """Base class for authentication backends."""

        async def authenticate(
            self, request: Request, credentials: HTTPAuthorizationCredentials | None, config: Config
        ) -> User | None:
            """Authenticate a user with the given credentials."""
            raise NotImplementedError("Subclasses must implement authenticate method")

    class JWTAuthBackend(AuthBackend):
        """Authentication backend that validates JWT tokens."""

        async def authenticate(
            self, request: Request, credentials: HTTPAuthorizationCredentials | None, config: Config
        ) -> User | None:
            """Authenticate using JWT token."""
            if credentials:
                try:
                    token_data = verify_token(credentials.credentials, config)
                    return User(username=token_data.username or "jwt_user", scopes=token_data.scopes, is_active=True)
                except HTTPException:
                    pass
            return None

    class APIKeyAuthBackend(AuthBackend):
        """Authentication backend that validates API keys."""

        async def authenticate(
            self, request: Request, credentials: HTTPAuthorizationCredentials | None, config: Config
        ) -> User | None:
            """Authenticate using API key from request headers."""
            try:
                await verify_api_key(request, config)
                return User(username="api_key_user", scopes=["read", "write"], is_active=True)
            except HTTPException:
                pass
            return None

    class OAuthBackend(AuthBackend):
        """Google OAuth 2.0 and future SSO backend."""

        async def authenticate(
            self, request: Request, credentials: HTTPAuthorizationCredentials | None, config: Config
        ) -> User | None:
            """Authenticate using OAuth tokens."""
            # Example: Check for OAuth session or token in request
            oauth_token = request.headers.get("X-OAuth-Token")
            if oauth_token:
                # In a real implementation, validate the token with the OAuth provider
                return User(username="oauth_user", scopes=["read", "write", "oauth"], is_active=True)
            return None

    class AuthDependency:
        """Authentication dependency supporting pluggable backends."""

        def __init__(self, require_authentication: bool = True, backends: list[AuthBackend] | None = None):
            self.require_auth = require_authentication
            self.backends = backends or [JWTAuthBackend(), APIKeyAuthBackend(), OAuthBackend()]

        async def __call__(
            self,
            request: Request,
            credentials: HTTPAuthorizationCredentials | None = Depends(security),
            config: Config = Depends(Config.from_env),
        ) -> User | None:
            if not self.require_auth:
                return None

            for backend in self.backends:
                user = await backend.authenticate(request, credentials, config)
                if user:
                    if not user.is_active:
                        raise HTTPException(status_code=400, detail=AuthErrorMessages.INACTIVE_USER)
                    return user

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=AuthErrorMessages.AUTH_REQUIRED,
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Common authentication dependencies
    require_auth = AuthDependency(require_authentication=True)
    optional_auth = AuthDependency(require_authentication=False)

else:
    # Fallback implementations when auth dependencies are not available
    security = None

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        check_auth_dependencies()

    def get_password_hash(password: str) -> str:
        check_auth_dependencies()

    def create_access_token(data: dict, expires_delta: timedelta | None = None, config: Config | None = None) -> str:
        check_auth_dependencies()

    def verify_token(token: str, config: Config | None = None) -> TokenData:
        check_auth_dependencies()

    async def get_current_user(*args, **kwargs) -> User:
        check_auth_dependencies()

    async def verify_api_key(*args, **kwargs) -> bool:
        check_auth_dependencies()

    class AuthBackend:
        """Base class for authentication backends."""

        async def authenticate(self, request: Any, credentials: Any, config: Config) -> User | None:
            check_auth_dependencies()

    class JWTAuthBackend(AuthBackend):
        pass

    class APIKeyAuthBackend(AuthBackend):
        pass

    class OAuthBackend(AuthBackend):
        pass

    class AuthDependency:
        def __init__(self, require_authentication: bool = True, backends: Any = None):
            self.require_auth = require_authentication
            self.backends = backends or []

        async def __call__(self, *args, **kwargs) -> User | None:
            check_auth_dependencies()

    require_auth = AuthDependency(require_authentication=True)
    optional_auth = AuthDependency(require_authentication=False)


def is_auth_available() -> bool:
    """Check if authentication dependencies are available."""
    return AUTH_DEPENDENCIES_AVAILABLE
