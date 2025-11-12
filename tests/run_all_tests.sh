#!/bin/bash

# Run all tests for Music Recommendation System
# This script runs both training and recommendation service tests

set -e  # Exit on error

echo "========================================================================"
echo "  MUSIC RECOMMENDATION SYSTEM - TEST SUITE"
echo "========================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "tests/test_recommendation_service.py" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    echo "Usage: cd /home/caiogrossi/mlops-assignment && bash tests/run_all_tests.sh"
    exit 1
fi

# Check if models directory exists
if [ ! -d "/home/caiogrossi/project2-pv/models" ]; then
    echo -e "${YELLOW}Warning: Models directory not found at /home/caiogrossi/project2-pv/models${NC}"
    echo "Some tests may fail without a trained model"
fi

# Check if model is trained
if [ ! -f "/home/caiogrossi/project2-pv/models/metadata.json" ]; then
    echo -e "${YELLOW}Warning: No metadata.json found - model may not be trained${NC}"
    echo "Train a model first for complete test coverage"
    echo ""
fi

# Create virtual environment
VENV_DIR=".test_venv"
echo -e "${BLUE}Creating virtual environment...${NC}"
python3 -m venv $VENV_DIR

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source $VENV_DIR/bin/activate

# Install test dependencies
echo -e "${GREEN}Installing test dependencies in venv...${NC}"
pip install -q --upgrade pip
pip install -q -r tests/requirements.txt

# Function to cleanup venv on exit
cleanup() {
    echo ""
    echo -e "${BLUE}Cleaning up virtual environment...${NC}"
    deactivate 2>/dev/null || true
    rm -rf $VENV_DIR
    echo -e "${GREEN}Virtual environment removed${NC}"
}

# Register cleanup function to run on exit
trap cleanup EXIT

echo ""
echo "========================================================================"
echo "  STEP 1: TRAINING SERVICE TESTS"
echo "========================================================================"
echo ""

if python3 tests/test_training_service.py; then
    echo -e "${GREEN}✓ Training service tests PASSED${NC}"
    TRAINING_RESULT=0
else
    echo -e "${RED}✗ Training service tests FAILED${NC}"
    TRAINING_RESULT=1
fi

echo ""
echo "========================================================================"
echo "  STEP 2: RECOMMENDATION SERVICE TESTS"
echo "========================================================================"
echo ""

if python3 tests/test_recommendation_service.py; then
    echo -e "${GREEN}✓ Recommendation service tests PASSED${NC}"
    RECOMMENDATION_RESULT=0
else
    echo -e "${RED}✗ Recommendation service tests FAILED${NC}"
    RECOMMENDATION_RESULT=1
fi

echo ""
echo "========================================================================"
echo "  FINAL RESULTS"
echo "========================================================================"

if [ $TRAINING_RESULT -eq 0 ] && [ $RECOMMENDATION_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo ""
    echo "Both services are working correctly!"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    echo ""
    if [ $TRAINING_RESULT -ne 0 ]; then
        echo "- Training service tests failed"
    fi
    if [ $RECOMMENDATION_RESULT -ne 0 ]; then
        echo "- Recommendation service tests failed"
    fi
    echo ""
    echo "Check the output above for details"
    exit 1
fi
