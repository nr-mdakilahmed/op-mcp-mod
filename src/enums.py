from enum import Enum


class APIType(str, Enum):
    """OpenMetadata API categories for modular server configuration."""

    # Core Entities
    TABLE = "table"
    DATABASE = "database"
    SCHEMA = "schema"
    COLUMN = "column"

    # Data Assets
    DASHBOARD = "dashboard"
    CHART = "chart"
    PIPELINE = "pipeline"
    TOPIC = "topic"

    # Data Quality
    DATAQUALITYTESTS = "dataqualitytests"
    TESTCASES = "testcases"
    METRICS = "metrics"
    PROFILER = "profiler"

    # Governance
    CLASSIFICATION = "classification"
    TAG = "tag"
    GLOSSARY = "glossary"
    POLICY = "policy"

    # Lineage & Usage
    LINEAGE = "lineage"
    USAGE = "usage"
    COST = "cost"

    # System Management
    SERVICES = "services"
    INGESTION = "ingestion"
    WEBHOOKS = "webhooks"
    BOTS = "bots"
