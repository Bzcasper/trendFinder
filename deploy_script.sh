#!/bin/bash
# Deploy script for Trend Finder

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Trend Finder Deployment Script${NC}\n"

# Check for Modal CLI
echo "Checking for Modal CLI..."
if ! command -v modal &> /dev/null; then
    echo -e "${RED}Modal CLI not found. Installing...${NC}"
    pip install modal
else
    echo -e "${GREEN}Modal CLI found!${NC}"
fi

# Log in to Modal if needed
echo "Checking Modal authentication..."
modal token new --check &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Not logged in to Modal. Please log in:${NC}"
    modal token new
else
    echo -e "${GREEN}Already logged in to Modal!${NC}"
fi

# Deploy the Modal API
echo -e "\n${YELLOW}Deploying Modal API...${NC}"
modal deploy modal_server.py

if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}Modal API deployed successfully!${NC}"
    echo -e "\n${YELLOW}Important:${NC}"
    echo "1. Copy the Modal API URL from above"
    echo "2. Update your .env file with the URL and token"
    echo "3. Make sure your sources.json file is configured"
    echo -e "\nRun npm start to test the application locally"
else
    echo -e "\n${RED}Failed to deploy Modal API. Please check errors above.${NC}"
fi

# Check for .env file
if [ ! -f .env ]; then
    echo -e "\n${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env file! Please update with your credentials.${NC}"
else
    echo -e "\n${GREEN}.env file already exists.${NC}"
fi

# Install npm dependencies
echo -e "\n${YELLOW}Installing npm dependencies...${NC}"
npm install

echo -e "\n${GREEN}Deployment setup complete!${NC}"
echo "You can now run the application with: npm start"
