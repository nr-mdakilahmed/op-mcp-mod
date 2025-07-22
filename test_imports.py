#!/usr/bin/env python3
"""Test script to verify imports are working."""

try:
    import click
    print("✓ click imported successfully")
except ImportError as e:
    print(f"✗ click import failed: {e}")

try:
    import uvicorn
    print("✓ uvicorn imported successfully")
except ImportError as e:
    print(f"✗ uvicorn import failed: {e}")

try:
    from pydantic import Field
    print("✓ pydantic imported successfully")
except ImportError as e:
    print(f"✗ pydantic import failed: {e}")

try:
    from pydantic_settings import BaseSettings
    print("✓ pydantic_settings imported successfully")
except ImportError as e:
    print(f"✗ pydantic_settings import failed: {e}")

try:
    import structlog
    print("✓ structlog imported successfully")
except ImportError as e:
    print(f"✗ structlog import failed: {e}")

print("\nAll imports tested!")
