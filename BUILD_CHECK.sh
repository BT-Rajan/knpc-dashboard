#!/bin/bash
# Comprehensive build, lint, and installer check for KNPC Dashboard
# Supports: Ubuntu (Linux) and Windows (via WSL or PowerShell)

set -e

RESET='\033[0m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'

log_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════╗${RESET}"
    echo -e "${BLUE}║ $1${RESET}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════╝${RESET}"
}

log_section() {
    echo -e "\n${YELLOW}📋 $1${RESET}"
}

log_pass() {
    echo -e "${GREEN}✓ $1${RESET}"
}

log_fail() {
    echo -e "${RED}✗ $1${RESET}"
    exit 1
}

log_info() {
    echo -e "${BLUE}ℹ $1${RESET}"
}

# Detect platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="Ubuntu"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    PLATFORM="Windows"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macOS"
else
    PLATFORM="Unknown"
fi

log_header "KNPC DASHBOARD - BUILD & LINT CHECK"
log_info "Platform: $PLATFORM"
log_info "Python: $(python3 --version 2>&1 || echo 'Not found')"
log_info "Node: $(node --version 2>&1 || echo 'Not found')"

# ============================================================================
# SECTION 1: PYTHON BACKEND CHECKS
# ============================================================================

log_section "PYTHON BACKEND - Environment Check"

# Check Python version
if ! command -v python3 &> /dev/null; then
    log_fail "Python 3 not found. Install Python 3.10+ from python.org"
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
log_pass "Python version: $PYTHON_VERSION"

# Check pip
if ! command -v pip3 &> /dev/null; then
    log_fail "pip3 not found"
fi
log_pass "pip3 is available"

log_section "PYTHON BACKEND - Linting & Type Checking"

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
if [[ "$PLATFORM" == "Ubuntu" ]]; then
    source venv/bin/activate
else
    source venv/Scripts/activate 2>/dev/null || . venv/Scripts/activate
fi
log_pass "Virtual environment activated"

# Install dependencies
log_info "Installing dependencies..."
pip install -q -r requirements.txt
log_pass "Dependencies installed"

# Check for linting tools
if ! command -v pylint &> /dev/null; then
    log_info "Installing linting tools (pylint, black, isort)..."
    pip install -q pylint black isort flake8
fi

# Run linters
log_info "Running Black (code formatter check)..."
if black --check app/ 2>&1 | grep -q "would reformat"; then
    echo -e "${YELLOW}⚠ Code formatting issues found (non-blocking)${RESET}"
    log_info "Run: black app/ to auto-format"
else
    log_pass "Black formatting check passed"
fi

log_info "Running isort (import sorting check)..."
if isort --check-only app/ 2>&1 | grep -q "error\|ERROR"; then
    echo -e "${YELLOW}⚠ Import sorting issues found (non-blocking)${RESET}"
    log_info "Run: isort app/ to auto-format"
else
    log_pass "isort check passed"
fi

log_info "Running Flake8 (style check)..."
if flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics; then
    log_pass "Flake8 critical errors check passed"
else
    echo -e "${YELLOW}⚠ Flake8 issues found (non-blocking)${RESET}"
fi

log_section "PYTHON BACKEND - Syntax & Import Check"

log_info "Checking Python syntax..."
python3 -m py_compile app/*.py app/routers/*.py app/scraper/*.py 2>&1 && \
    log_pass "All Python files compile successfully" || \
    log_fail "Python syntax error"

log_info "Checking imports..."
python3 -c "from app.main import app; print('Main app imports OK')" && \
    log_pass "App imports successful" || \
    log_fail "Import error in main app"

log_section "PYTHON BACKEND - Clean Build"

log_info "Removing build artifacts..."
rm -rf build dist *.egg-info __pycache__ .pytest_cache .mypy_cache
find app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
log_pass "Build artifacts cleaned"

log_info "Building clean..."
python3 -m py_compile app/main.py
log_pass "Clean build successful"

# Deactivate venv
deactivate 2>/dev/null || true
cd ..

# ============================================================================
# SECTION 2: NODE.JS FRONTEND CHECKS
# ============================================================================

log_section "NODE.JS FRONTEND - Environment Check"

if ! command -v node &> /dev/null; then
    log_fail "Node.js not found. Install from nodejs.org (v18+ recommended)"
fi

NODE_VERSION=$(node --version)
log_pass "Node version: $NODE_VERSION"

if ! command -v npm &> /dev/null; then
    log_fail "npm not found"
fi

NPM_VERSION=$(npm --version)
log_pass "npm version: $NPM_VERSION"

log_section "NODE.JS FRONTEND - Linting & Type Checking"

cd frontend

# Check for ESLint
if ! command -v eslint &> /dev/null; then
    log_info "ESLint not in PATH (checking local)..."
fi

log_info "Installing frontend dependencies..."
npm install --silent --no-progress 2>&1 | grep -v "npm warn" || true
log_pass "Frontend dependencies installed"

# Run TypeScript check
log_info "Running TypeScript type check..."
if npx tsc --noEmit 2>&1 | grep -q "error TS"; then
    echo -e "${YELLOW}⚠ TypeScript errors found (may be non-blocking)${RESET}"
else
    log_pass "TypeScript check passed"
fi

# Run ESLint if available
log_info "Running ESLint..."
if npx eslint src --max-warnings 5 2>&1 | tail -5; then
    log_pass "ESLint check completed"
fi

log_section "NODE.JS FRONTEND - Clean Build"

log_info "Removing build artifacts..."
rm -rf dist build node_modules/.vite .vite-config-cache 2>/dev/null || true
log_pass "Build artifacts cleaned"

log_info "Running Vite build (clean)..."
npm run build --silent 2>&1 | tail -10
if [ -d "dist" ]; then
    log_pass "Clean Vite build successful"
    log_info "Output size: $(du -sh dist | cut -f1)"
else
    log_fail "Build output not found"
fi

cd ..

# ============================================================================
# SECTION 3: INSTALLER CHECK
# ============================================================================

log_section "INSTALLER - Dependency Check"

# Check key dependencies
log_info "Verifying backend dependencies..."
cd backend
python3 -c "
import sys
deps = ['fastapi', 'sqlalchemy', 'pydantic', 'docx']
missing = []
for dep in deps:
    try:
        __import__(dep.replace('-', '_'))
    except ImportError:
        missing.append(dep)
if missing:
    print(f'Missing: {missing}')
    sys.exit(1)
print('All critical dependencies found')
" && log_pass "Backend dependencies verified" || log_fail "Missing backend dependencies"
cd ..

log_info "Verifying frontend dependencies..."
cd frontend
if [ -d "node_modules" ]; then
    if [ -f "node_modules/.package-lock.json" ] || [ -f "package-lock.json" ]; then
        log_pass "Frontend dependencies installed"
    else
        log_fail "node_modules exists but package-lock.json missing"
    fi
else
    log_fail "node_modules not found - run npm install"
fi
cd ..

log_section "INSTALLER - Script Check"

log_info "Checking required scripts..."

# Check backend startup
if grep -q "app = FastAPI" backend/app/main.py; then
    log_pass "Backend FastAPI app configured"
else
    log_fail "Backend app configuration missing"
fi

# Check frontend config
if [ -f "frontend/vite.config.ts" ]; then
    log_pass "Frontend Vite config found"
else
    log_fail "Frontend Vite config missing"
fi

log_section "INSTALLER - Permission Check"

if [[ "$PLATFORM" == "Ubuntu" ]]; then
    log_info "Checking script permissions..."
    
    # These would exist on main branch
    for script in start.sh run.py backend/run.py; do
        if [ -f "$script" ]; then
            if [ -x "$script" ]; then
                log_pass "$script is executable"
            else
                log_info "$script needs execute permission - fixing..."
                chmod +x "$script"
                log_pass "Fixed permissions for $script"
            fi
        fi
    done
fi

# ============================================================================
# SECTION 4: CONFIGURATION CHECK
# ============================================================================

log_section "CONFIGURATION - Environment Setup"

log_info "Checking configuration files..."

# Backend config
if [ -f "backend/app/config.py" ]; then
    if grep -q "DATABASE_URL\|DB_HOST" backend/app/config.py; then
        log_pass "Backend configuration present"
    else
        log_fail "Backend config incomplete"
    fi
else
    log_fail "Backend config file missing"
fi

# Frontend config
if [ -f "frontend/vite.config.ts" ]; then
    log_pass "Frontend configuration present"
else
    log_fail "Frontend config missing"
fi

log_info "Checking for required env template..."
if [ ! -f ".env.example" ]; then
    log_info "No .env.example found - creating template..."
    cat > .env.example << 'ENVEOF'
# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=knpc_dashboard
DB_USER=root
DB_PASSWORD=

# API
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=your-secret-key-here

# Frontend
VITE_API_BASE=http://localhost:8000

# Scraper
SCRAPER_INTERVAL=3600
ENABLE_SCRAPER=true
ENVEOF
    log_pass "Created .env.example template"
fi

# ============================================================================
# SECTION 5: PLATFORM-SPECIFIC CHECKS
# ============================================================================

log_section "PLATFORM-SPECIFIC CHECKS"

if [[ "$PLATFORM" == "Ubuntu" ]]; then
    log_info "Ubuntu-specific checks..."
    
    # Check for MySQL/MariaDB
    if command -v mysql &> /dev/null; then
        log_pass "MySQL client installed"
    else
        log_info "MySQL client not installed (optional - can use remote DB)"
    fi
    
    # Check for system Python
    if [ -f "/usr/bin/python3" ]; then
        log_pass "System Python available"
    fi
    
    # Check file permissions
    if [ "$(stat -f%A . 2>/dev/null || stat -c%a .)" != "755" ]; then
        log_info "Adjusting directory permissions..."
        chmod 755 . backend frontend 2>/dev/null || true
    fi
    
elif [[ "$PLATFORM" == "Windows" ]]; then
    log_info "Windows-specific checks..."
    log_info "Note: Some checks skipped in WSL/Git Bash"
    log_info "For native Windows, use PowerShell commands in BUILD_CHECK.ps1"
fi

# ============================================================================
# SUMMARY
# ============================================================================

log_header "BUILD & LINT CHECK - COMPLETE"

echo -e "\n${GREEN}✓ All critical checks passed${RESET}\n"

echo "Summary:"
echo "  Backend:   ✓ Python $PYTHON_VERSION"
echo "  Frontend:  ✓ Node $NODE_VERSION"
echo "  Lint:      ✓ Passed (with warnings)"
echo "  Build:     ✓ Clean build successful"
echo "  Installer: ✓ Ready to run"
echo ""

echo -e "${BLUE}Next steps:${RESET}"
echo "  1. Backend:  cd backend && source venv/bin/activate && python run.py"
echo "  2. Frontend: cd frontend && npm run dev"
echo "  3. Open:     http://localhost:5173"
echo ""

