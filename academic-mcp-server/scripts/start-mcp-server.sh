#!/bin/bash

# Academic MCP Server Startup Script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}Academic MCP Server Startup${NC}"
echo "Project directory: $PROJECT_DIR"

# Change to project directory
cd "$PROJECT_DIR"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${RED}Error: package.json not found. Make sure you're in the correct directory.${NC}"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
fi

# Build the project
echo -e "${YELLOW}Building project...${NC}"
npm run build

# Check if build was successful
if [ ! -f "dist/index.js" ]; then
    echo -e "${RED}Error: Build failed. dist/index.js not found.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Build successful${NC}"

# Start the server
echo -e "${BLUE}Starting Academic MCP Server...${NC}"
echo -e "${YELLOW}Server will be available for Claude Desktop integration${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start with production settings
NODE_ENV=production node dist/index.js