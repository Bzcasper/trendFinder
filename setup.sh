#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Trend Finder Setup Script ===${NC}\n"

# Create backup directory for old files
echo -e "${CYAN}Creating backup directory...${NC}"
BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup existing files if they exist
if [ -f src/services/crawler.py ]; then
  echo -e "${CYAN}Backing up existing crawler.py...${NC}"
  cp src/services/crawler.py $BACKUP_DIR/
fi

if [ -f src/services/generateDraft.ts ]; then
  echo -e "${CYAN}Backing up existing generateDraft.ts...${NC}"
  cp src/services/generateDraft.ts $BACKUP_DIR/
fi

if [ -f src/services/sendDraft.ts ]; then
  echo -e "${CYAN}Backing up existing sendDraft.ts...${NC}"
  cp src/services/sendDraft.ts $BACKUP_DIR/
fi

# Create directories if they don't exist
echo -e "${CYAN}Creating directory structure...${NC}"
mkdir -p src/utils
mkdir -p src/services
mkdir -p debug
mkdir -p backup

# Create Python virtual environment
echo -e "${CYAN}Setting up Python virtual environment...${NC}"
if command -v python3 &> /dev/null; then
    python3 -m venv venv
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        echo -e "${RED}Failed to create virtual environment.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Virtual environment created and activated!${NC}"
else
    echo -e "${RED}Python 3 not found. Please install Python 3.${NC}"
    exit 1
fi

# Install Python dependencies
echo -e "\n${CYAN}Installing Python dependencies...${NC}"
pip install -U pip
pip install -r requirements.txt

# Install Playwright browsers
echo -e "\n${CYAN}Installing Playwright browsers...${NC}"
python -m playwright install chromium
python -m playwright install-deps chromium

# Install Node.js dependencies
echo -e "\n${CYAN}Installing Node.js dependencies...${NC}"
npm install
npm install colorama axios

# Install TypeScript globally if not installed
if ! command -v tsc &> /dev/null; then
    echo -e "\n${CYAN}Installing TypeScript globally...${NC}"
    npm install -g typescript
fi

# Check for .env file
if [ ! -f .env ]; then
    echo -e "\n${CYAN}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env file! Please update with your credentials.${NC}"
else
    echo -e "\n${GREEN}.env file already exists.${NC}"
fi

# Build the TypeScript files
echo -e "\n${CYAN}Building TypeScript files...${NC}"
tsc

echo -e "\n${GREEN}Setup complete!${NC}"
echo -e "To run the application:"
echo -e "1. Make sure your Python virtual environment is activated:"
echo -e "   ${CYAN}source venv/bin/activate${NC} (Linux/macOS) or ${CYAN}venv\\Scripts\\activate${NC} (Windows)"
echo -e "2. Run the application with: ${CYAN}npm start${NC}"
echo -e ""
echo -e "If you encounter issues with Twitter/X API or Slack webhooks, check your .env file."