#!/bin/bash
# Script to create test tags for deployment pipeline testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🏷️  Test Tag Creation Script${NC}"
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ Not in a git repository${NC}"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo -e "Current branch: ${YELLOW}$CURRENT_BRANCH${NC}"

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ You have uncommitted changes. Please commit or stash them first.${NC}"
    exit 1
fi

# Generate test tag name
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
TEST_TAG="test/deployment-$TIMESTAMP"

echo ""
echo -e "${YELLOW}Creating test tag: $TEST_TAG${NC}"
echo ""

# Create and push test tag
git tag "$TEST_TAG"
echo -e "${GREEN}✅ Created local tag: $TEST_TAG${NC}"

echo ""
echo -e "${YELLOW}Push this tag to trigger the deployment pipeline:${NC}"
echo -e "${GREEN}git push origin $TEST_TAG${NC}"
echo ""
echo -e "${YELLOW}To delete the tag later:${NC}"
echo -e "${GREEN}git tag -d $TEST_TAG${NC}"
echo -e "${GREEN}git push origin --delete $TEST_TAG${NC}"
echo ""

# Ask if user wants to push immediately
read -p "Push the tag now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin "$TEST_TAG"
    echo -e "${GREEN}✅ Tag pushed! Check GitHub Actions for workflow execution.${NC}"
    echo -e "${YELLOW}Workflow URL: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^/]*\)\/\([^.]*\).*/\1\/\2/')/actions${NC}"
else
    echo -e "${YELLOW}Tag created locally but not pushed.${NC}"
fi
