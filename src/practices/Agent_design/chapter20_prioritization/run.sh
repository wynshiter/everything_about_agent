#!/bin/bash

# Chapter 20: Prioritization (优先级) - Practice Script

set -e

echo "=================================================="
echo "   Chapter 20: Prioritization (优先级) - Practice"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo -e "${RED}Error: Python is not found in PATH.${NC}"
    echo "Please install Python 3.10+"
    exit 1
fi

PYTHON_CMD=$(command -v python3 || command -v python)
echo "Using Python: $PYTHON_CMD"

# Check for Ollama (optional but recommended)
echo ""
echo "Checking Ollama service..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: Ollama service not detected at localhost:11434${NC}"
    echo "Please ensure Ollama is running: ollama serve"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}Ollama service is running${NC}"
fi

# Navigate to script directory
cd "$(dirname "$0")"

# Set Python path for imports
export PYTHONPATH="$(dirname "$0")/../../../..:$PYTHONPATH"

# Run the practice script
echo ""
echo "Starting practice..."
echo "--------------------------------------------------"
$PYTHON_CMD chapter20_prioritization_practice.py

echo ""
echo "--------------------------------------------------"
echo -e "${GREEN}Practice completed successfully!${NC}"

