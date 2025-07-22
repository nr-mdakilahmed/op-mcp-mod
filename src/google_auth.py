"""Google OAuth authentication module for MCP OpenMetadata server."""

import secrets
from typing import Optional, Dict, Any

from fastapi import HTTPException, Request, status
import google.auth.transport.requests
import google.oauth2.id_token
from google_auth_oauthlib.flow import Flow

from src.config import Config
from src.auth import User, create_access_token
from src.monitoring import get_logger

logger = get_logger("mcp.google_auth")


class GoogleOAuthHandler:
    """Handles Google OAuth authentication flow."""
    
    def __init__(self, config: Config):
        self.config = config
        self.flow = None
        
        if config.google_oauth_enabled:
            self._initialize_flow()
    
    def _initialize_flow(self):
        """Initialize Google OAuth flow."""
        try:
            # Create client configuration for OAuth flow
            client_config = {
                "web": {
                    "client_id": self.config.GOOGLE_CLIENT_ID,
                    "client_secret": self.config.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.config.GOOGLE_REDIRECT_URI]
                }
            }
            
            self.flow = Flow.from_client_config(
                client_config,
                scopes=[
                    "openid",
                    "email",
                    "profile"
                ]
            )
            self.flow.redirect_uri = self.config.GOOGLE_REDIRECT_URI
            
            logger.info("Google OAuth flow initialized", 
                       client_id=self.config.GOOGLE_CLIENT_ID[:10] + "...",
                       redirect_uri=self.config.GOOGLE_REDIRECT_URI)
            
        except Exception as e:
            logger.error("Failed to initialize Google OAuth flow", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth configuration error"
            ) from e
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Get Google OAuth authorization URL."""
        if not self.flow:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth not configured"
            )
        
        if not state:
            state = secrets.token_urlsafe(32)
        
        authorization_url, _ = self.flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )
        
        logger.info("Generated Google OAuth authorization URL", state=state)
        return authorization_url
    
    async def handle_callback(self, request: Request) -> Dict[str, Any]:
        """Handle Google OAuth callback and return user info."""
        if not self.flow:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth not configured"
            )
        
        # Get authorization code from callback
        code = request.query_params.get('code')
        error = request.query_params.get('error')
        # state = request.query_params.get('state')  # For future use in CSRF protection
        
        if error:
            logger.error("Google OAuth error", error=error)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OAuth error: {error}"
            )
        
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing authorization code"
            )
        
        try:
            # Exchange authorization code for tokens
            self.flow.fetch_token(code=code)
            
            # Get user info from ID token
            credentials = self.flow.credentials
            request_adapter = google.auth.transport.requests.Request()
            
            id_info = google.oauth2.id_token.verify_oauth2_token(
                id_token=credentials.id_token,
                request=request_adapter,
                audience=self.config.GOOGLE_CLIENT_ID
            )
            
            # Extract user information
            user_info = {
                "id": id_info.get("sub"),
                "email": id_info.get("email"),
                "name": id_info.get("name"),
                "picture": id_info.get("picture"),
                "email_verified": id_info.get("email_verified", False)
            }
            
            # Validate user email domain if restrictions are configured
            if self.config.oauth_allowed_domains_list:
                email = user_info.get("email", "")
                domain = email.split("@")[-1] if "@" in email else ""
                
                if domain not in self.config.oauth_allowed_domains_list:
                    logger.warning("OAuth login attempt from unauthorized domain",
                                 email=email, domain=domain,
                                 allowed_domains=self.config.oauth_allowed_domains_list)
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Email domain '{domain}' is not authorized"
                    )
            
            # Require verified email
            if not user_info.get("email_verified"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email address must be verified"
                )
            
            logger.info("Google OAuth login successful",
                       email=user_info.get("email"),
                       name=user_info.get("name"))
            
            return user_info
            
        except google.auth.exceptions.GoogleAuthError as e:
            logger.error("Google OAuth authentication failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            ) from e
        except Exception as e:
            logger.error("Unexpected error during OAuth callback", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error"
            ) from e
    
    def create_user_from_google_info(self, user_info: Dict[str, Any]) -> User:
        """Create a User object from Google user info."""
        return User(
            username=user_info.get("email", "unknown"),
            scopes=["read", "write"],  # Default scopes for OAuth users
            is_active=True
        )
    
    def create_jwt_token_for_user(self, user_info: Dict[str, Any]) -> str:
        """Create JWT token for authenticated Google user."""
        token_data = {
            "sub": user_info.get("email"),
            "email": user_info.get("email"),
            "name": user_info.get("name"),
            "picture": user_info.get("picture"),
            "auth_method": "google_oauth",
            "scopes": ["read", "write"]
        }
        
        return create_access_token(data=token_data, config=self.config)


# Global OAuth handler instance
_oauth_handler: Optional[GoogleOAuthHandler] = None


def get_oauth_handler(config: Config) -> GoogleOAuthHandler:
    """Get or create Google OAuth handler instance."""
    # Using module-level variable to maintain singleton pattern
    # pylint: disable=global-statement
    global _oauth_handler
    
    if _oauth_handler is None:
        _oauth_handler = GoogleOAuthHandler(config)
    
    return _oauth_handler


async def verify_google_oauth_user(user_info: Dict[str, Any], config: Config) -> User:
    """Verify and create user from Google OAuth info."""
    oauth_handler = get_oauth_handler(config)
    return oauth_handler.create_user_from_google_info(user_info)
