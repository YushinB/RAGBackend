#!/usr/bin/env python3
"""
Development Environment Status Check

This script verifies that the development environment is properly configured.
"""

import subprocess
import sys
from pathlib import Path


def check_tool(command: str, name: str) -> bool:
    """Check if a development tool is working."""
    try:
        subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        print(f"✅ {name}: Working")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {name}: Failed - {e}")
        return False
    except FileNotFoundError:
        print(f"❌ {name}: Not found")
        return False


def check_files_exist() -> bool:
    """Check that required configuration files exist."""
    required_files = [
        "requirements.txt",
        "pyproject.toml",
        ".pre-commit-config.yaml",
        "pytest.ini",
        "ruff.toml",
        ".env.example",
        ".gitignore",
    ]

    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)

    if missing:
        print(f"❌ Missing files: {', '.join(missing)}")
        return False
    else:
        print("✅ All configuration files present")
        return True


def main():
    """Main status check function."""
    print("🔍 RAG Python Backend - Development Environment Status")
    print("=" * 60)

    all_good = True

    # Check virtual environment
    if Path("venv").exists():
        print("✅ Virtual environment: Created")
    else:
        print("❌ Virtual environment: Missing")
        all_good = False

    # Check configuration files
    if not check_files_exist():
        all_good = False

    # Check development tools
    tools_to_check = [
        ("python --version", "Python"),
        ("pip --version", "pip"),
        ("black --version", "Black"),
        ("ruff --version", "Ruff"),
        ("mypy --version", "MyPy"),
        ("pytest --version", "Pytest"),
        ("pre-commit --version", "Pre-commit"),
    ]

    for command, name in tools_to_check:
        if not check_tool(command, name):
            all_good = False

    # Check application initialization
    print("\n🧪 Testing application...")
    if check_tool("python -m src.core.app", "Application initialization"):
        print("✅ Application: Initializes successfully")
    else:
        print("❌ Application: Initialization failed")
        all_good = False

    # Summary
    print("\n" + "=" * 60)
    if all_good:
        print("🎉 Development environment is ready!")
        print("\n📝 Quick start commands:")
        print("  - Activate venv: .\\venv\\Scripts\\Activate.ps1  # Windows")
        print("  - Activate venv: source venv/bin/activate     # Linux/Mac")
        print("  - Run tests: pytest")
        print("  - Format code: black src/")
        print("  - Lint code: ruff check src/")
        print("  - Run app: python -m src.core.app")
    else:
        print("⚠️  Development environment has issues.")
        print("Please check the errors above and run setup script again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
