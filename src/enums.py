"""API type enumerations for OpenMetadata MCP server.

This module defines the API categories available in the OpenMetadata server,
enabling modular configuration of which API groups to expose.
"""

from enum import Enum


class APIType(str, Enum):
    """OpenMetadata API categories for modular server configuration.

    Each enum value corresponds to a specific OpenMetadata API group
    that can be independently enabled or disabled in the server.
    """

    # Core Entities - Fundamental data assets
    TABLE = "table"
    DATABASE = "database"
    SCHEMA = "databaseschema"  # Maps to databaseSchemas endpoint

    # Data Assets - Various data representations
    DASHBOARD = "dashboard"
    CHART = "chart"
    PIPELINE = "pipeline"
    TOPIC = "topic"
    METRICS = "metrics"
    CONTAINER = "container"
    REPORT = "report"
    ML_MODEL = "mlmodel"

    # Users & Teams - Identity and access management
    USER = "user"
    TEAM = "team"

    # Governance & Classification - Data governance tools
    CLASSIFICATION = "classification"
    GLOSSARY = "glossary"
    TAG = "tag"

    # System & Operations - Platform management
    BOT = "bot"
    SERVICES = "services"
    EVENT = "event"

    # Analytics & Monitoring - Usage and performance
    LINEAGE = "lineage"
    USAGE = "usage"
    SEARCH = "search"

    # Data Quality - Testing and validation
    TEST_CASE = "test_case"
    TEST_SUITE = "test_suite"

    # Access Control & Security - Permissions and policies
    POLICY = "policy"
    ROLE = "role"

    # Domain Management - Business domain organization
    DOMAIN = "domain"

    @classmethod
    def get_core_apis(cls) -> list[str]:
        """Get the core API types that are enabled by default.

        Returns:
            List of core API type values
        """
        return [
            cls.TABLE.value,
            cls.DATABASE.value,
            cls.SCHEMA.value,
            cls.DASHBOARD.value,
            cls.CHART.value,
            cls.PIPELINE.value,
            cls.TOPIC.value,
            cls.METRICS.value,
            cls.CONTAINER.value,
        ]

    @classmethod
    def get_all_apis(cls) -> list[str]:
        """Get all available API types.

        Returns:
            List of all API type values
        """
        return [api.value for api in cls]

    @classmethod
    def get_governance_apis(cls) -> list[str]:
        """Get governance-related API types.

        Returns:
            List of governance API type values
        """
        return [
            cls.CLASSIFICATION.value,
            cls.GLOSSARY.value,
            cls.TAG.value,
            cls.POLICY.value,
            cls.ROLE.value,
        ]

    @classmethod
    def get_analytics_apis(cls) -> list[str]:
        """Get analytics and monitoring API types.

        Returns:
            List of analytics API type values
        """
        return [
            cls.LINEAGE.value,
            cls.USAGE.value,
            cls.SEARCH.value,
            cls.TEST_CASE.value,
            cls.TEST_SUITE.value,
        ]

    # Future Expansion - Commented out for upcoming features
    # These will be implemented in future versions
    #
    # API_COLLECTION = "api_collection"
    # API_ENDPOINT = "api_endpoint"
    # APP = "app"
    # FEED = "feed"
    # PERSONA = "persona"
    # QUERY = "query"
    # SEARCH_INDEX = "search_index"
    # STORED_PROCEDURE = "stored_procedure"
    # SUGGESTION = "suggestion"
    # WEBHOOK = "webhook"
