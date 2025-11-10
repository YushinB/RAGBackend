#!/usr/bin/env python3
"""
Development Environment Setup Script

This script sets up the complete development environment for the RAG Python Backend.
It creates virtual environment, installs dependencies, and configures development tools.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(
    command: str, description: str, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a command with proper error handling and logging."""
    print(f"\n🔄 {description}")
    print(f"   Running: {command}")

    try:
        result = subprocess.run(
            command, shell=True, check=check, capture_output=True, text=True
        )

        if result.returncode == 0:
            print(f"✅ {description} - Success")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"❌ {description} - Failed")
            if result.stderr.strip():
                print(f"   Error: {result.stderr.strip()}")

        return result

    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed with error: {e}")
        if e.stderr:
            print(f"   Error details: {e.stderr}")
        raise


def check_python_version():
    """Check if Python version meets requirements."""
    print("🔍 Checking Python version...")

    if sys.version_info < (3, 13):
        print(f"❌ Python 3.13+ required, found {sys.version}")
        sys.exit(1)

    print(f"✅ Python {sys.version} meets requirements")


def setup_virtual_environment():
    """Set up Python virtual environment."""
    venv_path = Path("venv")

    if venv_path.exists():
        print("📁 Virtual environment already exists")
        return

    run_command("python -m venv venv", "Creating virtual environment")


def install_dependencies():
    """Install all project dependencies."""
    # Determine activation script based on OS
    if os.name == "nt":  # Windows
        python_exe = "venv\\Scripts\\python.exe"
        pip_exe = "venv\\Scripts\\pip.exe"
    else:  # Unix/Linux/Mac
        python_exe = "venv/bin/python"
        pip_exe = "venv/bin/pip"

    # Upgrade pip
    run_command(f"{python_exe} -m pip install --upgrade pip", "Upgrading pip")

    # Install setuptools and wheel
    run_command(f"{pip_exe} install setuptools wheel", "Installing build tools")

    # Install core dependencies
    core_deps = [
        "fastapi",
        "uvicorn[standard]",
        "pydantic",
        "pydantic-settings",
        "python-dotenv",
        "pyyaml",
        "httpx",
    ]
    run_command(
        f"{pip_exe} install {' '.join(core_deps)}", "Installing core dependencies"
    )

    # Install development tools
    dev_deps = [
        "black",
        "ruff",
        "mypy",
        "pre-commit",
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-timeout",
        "isort",
    ]
    run_command(
        f"{pip_exe} install {' '.join(dev_deps)}", "Installing development tools"
    )


def configure_pre_commit():
    """Configure and install pre-commit hooks."""
    if os.name == "nt":  # Windows
        pre_commit_exe = "venv\\Scripts\\pre-commit.exe"
    else:
        pre_commit_exe = "venv/bin/pre-commit"

    run_command(f"{pre_commit_exe} install", "Installing pre-commit hooks")
    run_command(f"{pre_commit_exe} autoupdate", "Updating pre-commit hooks")


def validate_setup():
    """Validate the development environment setup."""
    if os.name == "nt":  # Windows
        python_exe = "venv\\Scripts\\python.exe"
    else:
        python_exe = "venv/bin/python"

    print("\n🧪 Validating setup...")

    # Test imports
    test_imports = ["fastapi", "uvicorn", "pydantic", "pytest", "black", "ruff", "mypy"]

    for package in test_imports:
        result = run_command(
            f"{python_exe} -c \"import {package}; print(f'{package} imported successfully')\"",
            f"Testing {package} import",
            check=False,
        )

        if result.returncode != 0:
            print(f"⚠️  Warning: {package} import failed")


def print_next_steps():
    """Print instructions for next steps."""
    print("\n🎉 Development environment setup complete!")
    print("\n📝 Next steps:")
    print("1. Activate the virtual environment:")

    if os.name == "nt":  # Windows
        print("   .\\venv\\Scripts\\Activate.ps1")
    else:
        print("   source venv/bin/activate")

    print("\n2. Test the setup:")
    print("   python -m src.core.app")
    print("   pytest --version")
    print("   black --version")
    print("   ruff --version")

    print("\n3. Start development:")
    print("   - Follow the project README.md")
    print("   - Run tests: pytest")
    print("   - Format code: black src/")
    print("   - Lint code: ruff check src/")

    print("\n4. Commit workflow:")
    print("   - Pre-commit hooks will automatically run on git commit")
    print("   - Manual check: pre-commit run --all-files")


def main():
    """Main setup function."""
    print("🚀 RAG Python Backend - Development Environment Setup")
    print("=" * 60)

    try:
        check_python_version()
        setup_virtual_environment()
        install_dependencies()
        configure_pre_commit()
        validate_setup()
        print_next_steps()

    except Exception as e:
        print(f"\n💥 Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
