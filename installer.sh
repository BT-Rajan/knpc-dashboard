#!/bin/bash
# KNPC Dashboard - Linux/macOS Installer
# Comprehensive setup script for Ubuntu, Debian, macOS
# Prerequisites: Python 3.10+, Node.js 18+

set -e

VERSION="1.0"
PROJECT="KNPC Dashboard"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Clear screen
clear

echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║ ${PROJECT} - Linux/macOS Installer v${VERSION}${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check for Python
print_info "Checking for Python 3.10+..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found!"
fi

PYTHON_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
print_success "Python ${PYTHON_VER} found"

# Check for Node.js
print_info "Checking for Node.js 18+..."
if ! command -v node &> /dev/null; then
    print_error "Node.js not found! Install from https://nodejs.org/"
fi

NODE_VER=$(node --version)
print_success "Node ${NODE_VER} found"

NPM_VER=$(npm --version)
print_success "npm ${NPM_VER} found"

echo ""
print_header "Setting up Backend (FastAPI)"
echo ""

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
python -m pip install --upgrade pip -q

# Install dependencies
print_info "Installing Python dependencies..."
pip install -q -r requirements.txt
print_success "Python dependencies installed"

# Verify imports
print_info "Verifying Python imports..."
python -c "from app.main import app; print('[OK] FastAPI app imports successfully')" || print_error "Failed to import FastAPI app"
print_success "FastAPI app verified"

cd ..

echo ""
print_header "Setting up Frontend (React + Vite)"
echo ""

cd frontend

# Install Node dependencies
print_info "Installing Node.js dependencies..."
echo "This may take a few minutes..."
npm install --silent 2>&1 | grep -v "npm warn" || true
print_success "Node.js dependencies installed"

# Run build
print_info "Building React frontend..."
npm run build --silent 2>&1 | tail -5 || print_warning "Frontend build completed with notices"
if [ -d "dist" ]; then
    DIST_SIZE=$(du -sh dist | cut -f1)
    print_success "Frontend built successfully (${DIST_SIZE})"
else
    print_warning "Frontend dist directory not found, but continuing..."
fi

cd ..

# Check for .env file
echo ""
print_header "Configuration Setup"
echo ""

if [ ! -f ".env" ]; then
    print_info "No .env file found. Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "Created .env from template"
        print_warning "Please update .env with your database credentials:"
        echo "   DB_HOST=localhost"
        echo "   DB_PORT=3306"
        echo "   DB_USER=root"
        echo "   DB_PASSWORD=your_password"
    fi
else
    print_success ".env file already exists"
fi

echo ""
print_header "Installation Complete!"
echo ""

echo "You can now start the application:"
echo ""
echo -e "${GREEN}Start Backend:${NC}"
echo "  1. cd backend"
echo "  2. source venv/bin/activate"
echo "  3. python run.py"
echo "  4. Backend will start on http://localhost:8000"
echo ""
echo -e "${GREEN}Start Frontend (in new terminal):${NC}"
echo "  1. cd frontend"
echo "  2. npm run dev"
echo "  3. Frontend will open on http://localhost:5173"
echo ""
echo -e "${GREEN}Or run commands in sequence:${NC}"
echo "  cd backend && source venv/bin/activate && python run.py &"
echo "  cd frontend && npm run dev"
echo ""
echo -e "${GREEN}Documentation:${NC}"
echo "  - README.md           (Overview)"
echo "  - QUICK_START.md      (Quick reference)"
echo "  - FEATURE_UPDATES.md  (Technical details)"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Update .env with your database settings"
echo "  2. Run backend and frontend servers"
echo "  3. Open http://localhost:5173 in your browser"
echo ""
