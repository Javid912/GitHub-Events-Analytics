#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}GitHub Events Analytics Cleanup${NC}"
echo -e "${YELLOW}============================${NC}"

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed.${NC}"
    exit 1
fi

# Ask for confirmation
echo -e "${RED}WARNING: This will stop all services and remove all data.${NC}"
read -p "Are you sure you want to continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Cleanup cancelled.${NC}"
    exit 0
fi

# Stop all services
echo -e "\n${YELLOW}Stopping all services...${NC}"
docker-compose -f docker/docker-compose.yml down
if [ $? -eq 0 ]; then
    echo -e "${GREEN}All services stopped successfully.${NC}"
else
    echo -e "${RED}Failed to stop services.${NC}"
    exit 1
fi

# Remove volumes
echo -e "\n${YELLOW}Removing Docker volumes...${NC}"
docker volume rm github-events-analytics_postgres-data github-events-analytics_grafana-data github-events-analytics_spark-checkpoints
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Volumes removed successfully.${NC}"
else
    echo -e "${YELLOW}Warning: Failed to remove some volumes. They may not exist or may be in use.${NC}"
fi

# Remove temporary files
echo -e "\n${YELLOW}Removing temporary files...${NC}"
rm -rf venv __pycache__ .pytest_cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete
find . -name ".coverage" -delete
find . -name "*.log" -delete
echo -e "${GREEN}Temporary files removed.${NC}"

# Clean up environment
echo -e "\n${YELLOW}Cleaning up environment...${NC}"
if [ -f ".env" ]; then
    echo -e "${YELLOW}Note: .env file was not removed. Remove it manually if needed.${NC}"
fi

echo -e "\n${GREEN}Cleanup completed successfully!${NC}"
echo -e "${YELLOW}To restart the system, run:${NC}"
echo -e "  ./start.sh" 