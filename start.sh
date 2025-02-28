#!/bin/bash

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found."
    echo "Please create a .env file based on .env.template"
    echo "cp .env.template .env"
    exit 1
fi

# Start the entire stack
echo "Starting GitHub Events Analytics stack..."
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "Checking services status..."
docker-compose -f docker/docker-compose.yml ps

echo ""
echo "GitHub Events Analytics is now running!"
echo ""
echo "Access the following services:"
echo "- Kafka UI: http://localhost:8080"
echo "- Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "To stop the services, run: docker-compose -f docker/docker-compose.yml down" 