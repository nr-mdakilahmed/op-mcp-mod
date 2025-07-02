from enum import Enum


class APIType(str, Enum):
    """OpenMetadata API categories for modular server configuration."""

    # Core Entities
    TABLE = "table"
    DATABASE = "database"
    SCHEMA = "databaseschema"  # Maps to databaseSchemas endpoint

    # Data Assets
    DASHBOARD = "dashboard"
    CHART = "chart"
    PIPELINE = "pipeline"
    TOPIC = "topic"
    METRICS = "metrics"
    CONTAINER = "container"

    # Users & Teams
    USER = "user"
    TEAM = "team"

    # Governance & Classification
    CLASSIFICATION = "classification"
    GLOSSARY = "glossary"

    # System & Operations
    BOT = "bot"

    # Analytics & Monitoring
    LINEAGE = "lineage"
    USAGE = "usage"

    # Additional API groups available in OpenMetadata (not yet implemented)
    API_COLLECTION = "apicollection"
    API_ENDPOINT = "apiendpoint"
    APP = "app"
    DATA_PRODUCT = "dataproduct"
    DOC_STORE = "docstore"
    DOMAIN = "domain"
    EVENT = "event"
    FEED = "feed"
    ML_MODEL = "mlmodel"
    PERMISSION = "permission"
    PERSONA = "persona"
    POLICY = "policy"
    QUERY = "query"
    REPORT = "report"
    ROLE = "role"
    SEARCH_INDEX = "searchindex"
    STORED_PROCEDURE = "storedprocedure"
    SUGGESTION = "suggestion"
    TAG = "tag"
