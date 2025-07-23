#!/usr/bin/env python3
"""
Quick validation script to ensure the uv setup is working correctly.
Run this after: make install-web
"""

import sys
import importlib

# Required packages for the server to function
required_packages = [
    ('mcp', 'mcp'),
    ('httpx', 'httpx'),
    ('click', 'click'), 
    ('anyio', 'anyio'),
    ('pydantic', 'pydantic'),
    ('python-dotenv', 'dotenv'),
    ('fastapi', 'fastapi'),
    ('uvicorn', 'uvicorn'),
    ('structlog', 'structlog'),
    ('cachetools', 'cachetools'),
]

def check_python_version():
    """Check if Python version meets requirements"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} (compatible)")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)")
        return False

def check_package(package_info):
    """Check if a package can be imported"""
    package_name, import_name = package_info
    try:
        importlib.import_module(import_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name} - not found")
        return False

def check_src_modules():
    """Check if our source modules can be imported"""
    src_modules = [
        'src.config',
        'src.main',
        'src.openmetadata.openmetadata_client',
    ]
    
    print("\n📦 Checking source modules:")
    all_good = True
    for module in src_modules:
        try:
            importlib.import_module(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module} - {e}")
            all_good = False
    
    return all_good

def main():
    """Main validation function"""
    print("🔍 OpenMetadata MCP Server - Setup Validation")
    print("=" * 50)
    
    # Check Python version
    python_ok = check_python_version()
    
    # Check required packages
    print("\n📦 Checking required packages:")
    packages_ok = all(check_package(pkg) for pkg in required_packages)
    
    # Check source modules
    modules_ok = check_src_modules()
    
    # Final status
    print("\n" + "=" * 50)
    if python_ok and packages_ok and modules_ok:
        print("🎉 Setup validation PASSED!")
        print("\nYou can now run:")
        print("  make run-web        # HTTP server")
        print("  make run            # stdio for AI assistants") 
        print("  make run-web-auth   # HTTP with authentication")
        return 0
    else:
        print("❌ Setup validation FAILED!")
        print("\nTry running: make install-web")
        return 1

if __name__ == "__main__":
    sys.exit(main())
