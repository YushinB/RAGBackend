# RAG Python Backend - Development Environment Setup (PowerShell)
# This script sets up the complete development environment for Windows

param(
    [switch]$Clean = $false
)

Write-Host "🚀 RAG Python Backend - Development Environment Setup" -ForegroundColor Cyan
Write-Host "=" * 60

# Check Python version
Write-Host "🔍 Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found. Please install Python 3.11+ first." -ForegroundColor Red
    exit 1
}

$version = $pythonVersion -replace "Python ", ""
$majorMinor = $version.Split('.')[0..1] -join '.'
if ([version]$majorMinor -lt [version]"3.11") {
    Write-Host "❌ Python 3.11+ required, found $pythonVersion" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Python $pythonVersion meets requirements" -ForegroundColor Green

# Clean existing environment if requested
if ($Clean -and (Test-Path "venv")) {
    Write-Host "🧹 Cleaning existing virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "venv"
}

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "📁 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "📁 Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "📦 Upgrading pip..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel

# Install core dependencies
Write-Host "📦 Installing core dependencies..." -ForegroundColor Yellow
$coreDeps = @(
    "fastapi", "uvicorn[standard]", "pydantic", "pydantic-settings",
    "python-dotenv", "pyyaml", "httpx"
)
& ".\venv\Scripts\pip.exe" install $coreDeps

# Install development tools
Write-Host "🛠️ Installing development tools..." -ForegroundColor Yellow
$devDeps = @(
    "black", "ruff", "mypy", "pre-commit",
    "pytest", "pytest-asyncio", "pytest-cov", "pytest-timeout",
    "isort"
)
& ".\venv\Scripts\pip.exe" install $devDeps

# Install pre-commit hooks
Write-Host "🔗 Installing pre-commit hooks..." -ForegroundColor Yellow
& ".\venv\Scripts\pre-commit.exe" install
& ".\venv\Scripts\pre-commit.exe" autoupdate

# Test setup
Write-Host "🧪 Testing setup..." -ForegroundColor Yellow

$testPackages = @("fastapi", "uvicorn", "pydantic", "pytest", "black", "ruff", "mypy")
foreach ($package in $testPackages) {
    try {
        & ".\venv\Scripts\python.exe" -c "import $package; print('$package: OK')"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $package imported successfully" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Warning: $package import failed" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "⚠️ Warning: $package import test failed" -ForegroundColor Yellow
    }
}

Write-Host "`n🎉 Development environment setup complete!" -ForegroundColor Cyan
Write-Host "`n📝 Next steps:" -ForegroundColor Yellow
Write-Host "1. Virtual environment is activated"
Write-Host "2. Test the application: python -m src.core.app"
Write-Host "3. Run tests: pytest"
Write-Host "4. Format code: black src/"
Write-Host "5. Lint code: ruff check src/"
Write-Host "6. Pre-commit hooks will run automatically on git commit"

Write-Host "`n🔧 Development commands:" -ForegroundColor Yellow
Write-Host "- Activate venv: .\venv\Scripts\Activate.ps1"
Write-Host "- Deactivate: deactivate"
Write-Host "- Install new packages: pip install <package>"
Write-Host "- Run pre-commit manually: pre-commit run --all-files"
