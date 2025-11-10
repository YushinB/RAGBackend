# Development Environment Setup Guide

This guide walks you through setting up the complete development environment for the RAG Python Backend project.

## Prerequisites

- Python 3.11 or higher
- Git
- PowerShell (Windows) or Bash (Linux/Mac)

## Quick Setup

### Option 1: Automated Setup (Windows)
```powershell
# Run the automated setup script
.\scripts\setup_dev_env.ps1

# Optional: Clean existing environment first
.\scripts\setup_dev_env.ps1 -Clean
```

### Option 2: Manual Setup

1. **Create Virtual Environment**
```bash
python -m venv venv

# Activate (Windows)
.\venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source venv/bin/activate
```

2. **Install Dependencies**
```bash
# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install core dependencies
pip install fastapi uvicorn[standard] pydantic pydantic-settings python-dotenv pyyaml httpx

# Install development tools
pip install black ruff mypy pre-commit pytest pytest-asyncio pytest-cov pytest-timeout isort
```

3. **Configure Pre-commit Hooks**
```bash
pre-commit install
pre-commit autoupdate
```

## Verify Setup

```bash
# Run status check
python scripts/check_dev_env.py

# Test application
python -m src.core.app
```

## Development Workflow

### Code Quality Tools

```bash
# Format code
black src/

# Lint code
ruff check src/ --fix

# Type checking
mypy src/

# Run tests
pytest

# Run all quality checks
pre-commit run --all-files
```

### Git Workflow

Pre-commit hooks are automatically installed and will run on each commit:
- Code formatting (Black)
- Linting (Ruff)
- Import sorting (isort)
- Basic file checks

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and update with your settings:

```bash
cp .env.example .env
# Edit .env with your configuration
```

### Key Settings

- `SECRET_KEY`: Application secret key (change in production)
- `LLM_API_KEY`: Your LLM provider API key
- `LLM_API_ENDPOINT`: LLM API endpoint URL
- `POSTGRES_PASSWORD`: Database password
- `REDIS_PASSWORD`: Redis password (if required)

## Project Structure

```
RAG-Python-Backend/
├── src/                    # Main application source
│   ├── api/               # FastAPI routes
│   ├── core/              # Core configuration and utilities
│   ├── models/            # Data models
│   ├── processors/        # Document processing
│   └── ...
├── tests/                 # Test suite
├── scripts/               # Setup and utility scripts
├── config/                # Configuration files
├── data/                  # Data storage
└── logs/                  # Application logs
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure virtual environment is activated
2. **Permission Errors**: Run PowerShell as Administrator (Windows)
3. **Pre-commit Fails**: Update hooks with `pre-commit autoupdate`

### Reset Environment

```bash
# Windows
Remove-Item -Recurse -Force venv
.\scripts\setup_dev_env.ps1 -Clean

# Linux/Mac
rm -rf venv
python scripts/setup_dev_env.py
```

## IDE Configuration

### VS Code

Install recommended extensions:
- Python
- Pylance
- Black Formatter
- Ruff
- GitLens

### PyCharm

Configure interpreters:
- Python Interpreter: `./venv/Scripts/python.exe`
- Enable Black formatting
- Enable Ruff linting

## Next Steps

1. Read the main [README.md](README.md) for project overview
2. Check [docs/Detailed_Design.md](docs/Detailed_Design.md) for architecture
3. Review [docs/milestone_1/](docs/milestone_1/) for current tasks
4. Start development with the configured environment

## Support

- Check existing documentation in `docs/`
- Review configuration files for examples
- Use the status check script to verify setup
