#!/bin/bash

# Quick test script for recommendation service only
# Tests: Build, Run, API with real dataset songs

set -e  # Exit on error

echo "========================================================================"
echo "  RECOMMENDATION SERVICE - QUICK TEST"
echo "========================================================================"
echo ""

cd /home/caiogrossi/mlops-assignment

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create virtual environment
VENV_DIR=".quick_test_venv"
echo -e "${BLUE}Creating virtual environment...${NC}"
python3 -m venv $VENV_DIR

# Activate virtual environment
source $VENV_DIR/bin/activate

# Install dependencies
echo -e "${BLUE}Installing dependencies in venv...${NC}"
pip install -q --upgrade pip
pip install -q requests

# Run only recommendation service tests
echo ""
python3 tests/test_recommendation_service.py

# Cleanup
echo ""
echo -e "${BLUE}Cleaning up virtual environment...${NC}"
deactivate
rm -rf $VENV_DIR

echo ""
echo -e "${GREEN}Test completed!${NC}"
