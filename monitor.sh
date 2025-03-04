#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed.${NC}"
    exit 1
fi

# Check if services are running
echo -e "${YELLOW}Checking services status...${NC}"
docker-compose -f docker/docker-compose.yml ps

# Function to check if a service is healthy
check_service() {
    local service=$1
    local status=$(docker inspect --format='{{.State.Health.Status}}' $service 2>/dev/null)
    
    if [ "$status" == "healthy" ]; then
        echo -e "${GREEN}✓ $service is healthy${NC}"
        return 0
    elif [ "$status" == "starting" ]; then
        echo -e "${YELLOW}⟳ $service is starting${NC}"
        return 1
    elif [ "$status" == "unhealthy" ]; then
        echo -e "${RED}✗ $service is unhealthy${NC}"
        return 2
    else
        local running=$(docker inspect --format='{{.State.Running}}' $service 2>/dev/null)
        if [ "$running" == "true" ]; then
            echo -e "${YELLOW}? $service is running (no health check)${NC}"
            return 0
        else
            echo -e "${RED}✗ $service is not running${NC}"
            return 2
        fi
    fi
}

# Check individual services
echo -e "\n${YELLOW}Checking individual services:${NC}"
services=("zookeeper" "kafka" "kafka-ui" "postgres" "grafana" "github-events-collector" "spark-streaming")

all_healthy=true
for service in "${services[@]}"; do
    check_service $service
    if [ $? -ne 0 ]; then
        all_healthy=false
    fi
done

# Check Kafka topics
echo -e "\n${YELLOW}Checking Kafka topics:${NC}"
topics=$(docker exec kafka kafka-topics --bootstrap-server kafka:9092 --list 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Kafka topics:${NC}"
    echo "$topics"
    
    # Check if our topics exist
    if echo "$topics" | grep -q "github-events"; then
        echo -e "${GREEN}✓ github-events topic exists${NC}"
    else
        echo -e "${RED}✗ github-events topic does not exist${NC}"
        all_healthy=false
    fi
    
    if echo "$topics" | grep -q "github-events-processed"; then
        echo -e "${GREEN}✓ github-events-processed topic exists${NC}"
    else
        echo -e "${RED}✗ github-events-processed topic does not exist${NC}"
        all_healthy=false
    fi
else
    echo -e "${RED}✗ Could not connect to Kafka${NC}"
    all_healthy=false
fi

# Check PostgreSQL tables
echo -e "\n${YELLOW}Checking PostgreSQL tables:${NC}"
tables=$(docker exec postgres psql -U postgres -d github_events -c '\dt' 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}PostgreSQL tables:${NC}"
    echo "$tables"
else
    echo -e "${RED}✗ Could not connect to PostgreSQL${NC}"
    all_healthy=false
fi

# Check Grafana
echo -e "\n${YELLOW}Checking Grafana:${NC}"
grafana_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health)
if [ "$grafana_status" == "200" ]; then
    echo -e "${GREEN}✓ Grafana is responding${NC}"
else
    echo -e "${RED}✗ Grafana is not responding (HTTP $grafana_status)${NC}"
    all_healthy=false
fi

# Check data flow
echo -e "\n${YELLOW}Checking data flow:${NC}"
event_count=$(docker exec postgres psql -U postgres -d github_events -c 'SELECT COUNT(*) FROM events;' -t 2>/dev/null)
if [ $? -eq 0 ]; then
    event_count=$(echo $event_count | tr -d ' ')
    if [ "$event_count" -gt 0 ]; then
        echo -e "${GREEN}✓ Data is flowing: $event_count events in database${NC}"
    else
        echo -e "${YELLOW}⚠ No events in database yet${NC}"
    fi
else
    echo -e "${RED}✗ Could not check event count${NC}"
    all_healthy=false
fi

# Summary
echo -e "\n${YELLOW}Summary:${NC}"
if $all_healthy; then
    echo -e "${GREEN}All services appear to be healthy!${NC}"
else
    echo -e "${RED}Some services have issues. Check the logs for more details:${NC}"
    echo -e "${YELLOW}docker-compose -f docker/docker-compose.yml logs${NC}"
fi 