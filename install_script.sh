#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Trend Finder Setup Script${NC}\n"

# Create Python virtual environment
echo "Setting up Python virtual environment..."
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
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
pip install -U pip
pip install crawl4ai 'playwright>=1.40.0' aiohttp

# Install Playwright browsers
echo -e "\n${YELLOW}Installing Playwright browsers...${NC}"
python -m playwright install

# Run Crawl4AI setup
echo -e "\n${YELLOW}Running Crawl4AI setup...${NC}"
python -c "
try:
    from crawl4ai.doctor import run_doctor_checks
    print('Running Crawl4AI diagnostics...')
    run_doctor_checks()
    print('Crawl4AI setup complete!')
except ImportError:
    print('Error: Crawl4AI not properly installed.')
    exit(1)
"

# Install Node.js dependencies
echo -e "\n${YELLOW}Installing Node.js dependencies...${NC}"
npm install

# Check for .env file
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env file! Please update with your credentials.${NC}"
else
    echo -e "\n${GREEN}.env file already exists.${NC}"
fi

echo -e "\n${GREEN}Setup complete!${NC}"
echo "1. Edit your .env file with your API keys and configuration"
echo "2. Run 'source venv/bin/activate' to activate the Python environment"
echo "3. Run 'npm start' to start the application"
