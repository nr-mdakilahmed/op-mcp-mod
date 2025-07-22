"""Authentication and security utilities for remote MCP server.

This module provides JWT token authentication, API key validation,
and security middleware for protecting the remote MCP endpoints.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from src.config import Config


class TokenData(BaseModel):
    """Token payload data model."""
    username: Optional[str] = None
    scopes: list[str] = []


class User(BaseModel):
    """User data model."""
    username: str
    scopes: list[str] = []
    is_active: bool = True


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


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None, config: Optional[Config] = None) -> str:
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


def verify_token(token: str, config: Optional[Config] = None) -> TokenData:
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
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
        scopes: list[str] = payload.get("scopes", [])
        token_data = TokenData(username=username, scopes=scopes)
    except JWTError as jwt_exc:
        raise credentials_exception from jwt_exc
    
    return token_data


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    config: Config = Depends(Config.from_env)
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
    user = User(
        username=token_data.username or "anonymous",
        scopes=token_data.scopes,
        is_active=True
    )
    
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


class AuthErrorMessages:
    INVALID_CREDENTIALS = "Could not validate credentials"
    API_KEY_REQUIRED = "API key required"
    INVALID_API_KEY = "Invalid API key"
    AUTH_REQUIRED = "Authentication required. Provide JWT token, API key, or OAuth."
    INACTIVE_USER = "Inactive user"


class AuthBackend:
    """Base class for authentication backends."""
    async def authenticate(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials], config: Config) -> Optional[User]:
        raise NotImplementedError()


class JWTAuthBackend(AuthBackend):
    """Authentication backend that validates JWT tokens."""
    
    async def authenticate(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials], config: Config) -> Optional[User]:
        """Authenticate using JWT token.
        
        Args:
            request: The FastAPI request object
            credentials: HTTP authorization credentials (Bearer token)
            config: Application configuration
            
        Returns:
            User object if authentication succeeds, None otherwise
        """
        if credentials:
            try:
                token_data = verify_token(credentials.credentials, config)
                return User(
                    username=token_data.username or "jwt_user",
                    scopes=token_data.scopes,
                    is_active=True
                )
            except HTTPException:
                pass
        return None


class APIKeyAuthBackend(AuthBackend):
    """Authentication backend that validates API keys."""
    
    async def authenticate(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials], config: Config) -> Optional[User]:
        """Authenticate using API key from request headers.
        
        Args:
            request: The FastAPI request object
            credentials: HTTP authorization credentials (not used for API key auth)
            config: Application configuration
            
        Returns:
            User object if authentication succeeds, None otherwise
        """
        try:
            await verify_api_key(request, config)
            return User(
                username="api_key_user",
                scopes=["read", "write"],
                is_active=True
            )
        except HTTPException:
            pass
        return None


class OAuthBackend(AuthBackend):
    """Google OAuth 2.0 and future SSO backend."""
    
    async def authenticate(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials], config: Config) -> Optional[User]:
        """Authenticate using OAuth tokens.
        
        Args:
            request: The FastAPI request object
            credentials: HTTP authorization credentials (not used for OAuth)
            config: Application configuration
            
        Returns:
            User object if authentication succeeds, None otherwise
        """
        # Example: Check for OAuth session or token in request
        # This is a placeholder. Actual implementation should verify OAuth session/cookie/token.
        oauth_token = request.headers.get("X-OAuth-Token")
        if oauth_token:
            # In a real implementation, validate the token with the OAuth provider
            # For example, for Google OAuth:
            # - Call Google's tokeninfo endpoint
            # - Verify token validity, expiration, and audience
            # - Extract user information from the validated token
            return User(
                username="oauth_user",
                scopes=["read", "write", "oauth"],
                is_active=True
            )
        return None

# To add more backends, subclass AuthBackend and append to AUTH_BACKENDS
AUTH_BACKENDS = [JWTAuthBackend(), APIKeyAuthBackend(), OAuthBackend()]

class AuthDependency:
    """Authentication dependency supporting pluggable backends."""
    def __init__(self, require_authentication: bool = True, backends: Optional[list[AuthBackend]] = None):
        self.require_auth = require_authentication
        self.backends = backends or AUTH_BACKENDS

    async def __call__(
        self,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        config: Config = Depends(Config.from_env)
    ) -> Optional[User]:
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
