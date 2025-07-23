"""Configuration management for MCP OpenMetadata server.

This module handles environment variable loading and configuration validation
for both local stdio mode and remote HTTP/WebSocket server modes.
"""

from typing import ClassVar, Optional
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Configuration settings for the MCP OpenMetadata server."""

    # OpenMetadata Configuration
    OPENMETADATA_HOST: str = Field(default="http://localhost:8585", description="OpenMetadata server host")
    OPENMETADATA_USERNAME: str = Field(default="admin@open-metadata.org", description="OpenMetadata username")
    OPENMETADATA_PASSWORD: str = Field(default="admin", description="OpenMetadata password")
    OPENMETADATA_JWT_TOKEN: str | None = Field(default=None, description="OpenMetadata JWT token (optional)")

    # Remote Server Configuration
    HTTP_HOST: str = Field(default="0.0.0.0", description="HTTP server host")
    HTTP_PORT: int = Field(default=8000, description="HTTP server port", ge=1, le=65535)
    WEBSOCKET_PORT: int = Field(default=8001, description="WebSocket server port", ge=1, le=65535)
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8080,http://localhost:8585",
        description="Comma-separated list of allowed CORS origins",
    )

    # Security Configuration
    JWT_SECRET_KEY: str = Field(
        default="your-super-secret-jwt-key-change-this-in-production-32-chars-minimum",
        description="JWT secret key for token signing",
        min_length=32,
    )
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="JWT token expiration in minutes", ge=1)
    API_KEY_HEADER: str = Field(default="X-API-Key", description="API key header name")
    DEFAULT_API_KEY: str = Field(
        default="mcp-openmetadata-default-key-change-this", description="Default API key for authentication"
    )

    # Sentry Configuration
    SENTRY_DSN: str | None = Field(default=None, description="Sentry DSN for error monitoring")
    SENTRY_ENVIRONMENT: str = Field(default="development", description="Sentry environment")
    SENTRY_TRACES_SAMPLE_RATE: float = Field(default=0.1, description="Sentry traces sample rate", ge=0.0, le=1.0)

    # Logging Configuration
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    STRUCTURED_LOGGING: bool = Field(default=True, description="Use structured logging")

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str | None = Field(default=None, description="Google OAuth client ID")
    GOOGLE_CLIENT_SECRET: str | None = Field(default=None, description="Google OAuth client secret")
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:8000/auth/google/callback", description="Google OAuth redirect URI"
    )
    OAUTH_ALLOWED_DOMAINS: str | None = Field(
        default=None, description="Comma-separated list of allowed email domains for OAuth"
    )
    OAUTH_SESSION_SECRET: str = Field(
        default="your-oauth-session-secret-change-this-in-production-32-chars-minimum",
        description="Secret key for OAuth session encryption",
        min_length=32,
    )

    @field_validator("OPENMETADATA_HOST")
    @classmethod
    def validate_openmetadata_host(cls, v: str) -> str:
        """Validate OpenMetadata host URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("OpenMetadata host must start with http:// or https://")

        parsed = urlparse(v)
        if not parsed.netloc:
            raise ValueError("Invalid OpenMetadata host URL")

        return v.rstrip("/")

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level value."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string into a list."""
        cors_origins = self.CORS_ORIGINS or ""
        return [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

    @property
    def oauth_allowed_domains_list(self) -> list[str] | None:
        """Parse OAuth allowed domains string into a list."""
        if not self.OAUTH_ALLOWED_DOMAINS:
            return None
        domains = self.OAUTH_ALLOWED_DOMAINS or ""
        return [domain.strip() for domain in domains.split(",") if domain.strip()]

    @property
    def google_oauth_enabled(self) -> bool:
        """Check if Google OAuth is properly configured."""
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        env_value = str(self.SENTRY_ENVIRONMENT).lower()
        return env_value == "production"

    @property
    def sentry_enabled(self) -> bool:
        """Check if Sentry error tracking is properly configured."""
        return bool(self.SENTRY_DSN)

    @property
    def openmetadata_api_version(self) -> str:
        """Get the OpenMetadata API version."""
        return "v1"  # Currently fixed to v1, could be configurable in the future

    @property
    def openmetadata_api_url(self) -> str:
        """Get the full OpenMetadata API URL."""
        return f"{self.OPENMETADATA_HOST}/api/{self.openmetadata_api_version}"

    # Class variable to store the singleton instance

    # Class variable to store the singleton instance (using ClassVar to avoid Pydantic treating it as a field)
    _config_instance: ClassVar[Optional["Config"]] = None

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables.

        This is implemented with a simple caching mechanism to avoid
        repeatedly parsing environment variables.
        """
        # Use a class-level cache to avoid repeated env file parsing
        if cls._config_instance is None:
            cls._config_instance = cls()
        return cls._config_instance

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }
