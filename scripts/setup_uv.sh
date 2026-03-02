#!/bin/bash

# UV Environment Setup Script (Linux/macOS)

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}   UV Environment Setup (Linux/macOS)${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python3 not found. Please install Python 3.10+${NC}"
    exit 1
fi

echo -e "${GREEN}[1/4] Checking Python...${NC}"
python3 --version

echo ""
echo -e "${GREEN}[2/4] Running UV setup script...${NC}"
python3 scripts/setup_uv.py

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}   Setup Complete!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "Next steps:"
echo -e "  1. Run: ${BLUE}source ./activate_venv.sh${NC}"
echo -e "  2. Run: ${BLUE}python src/agents/patterns/chaining.py${NC}"
echo ""
