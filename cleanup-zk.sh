#!/bin/bash

# Create a temporary container to clean up Zookeeper data
docker run --rm -v github-events-analytics_zookeeper-data:/data alpine:latest sh -c "rm -rf /data/*"

echo "Zookeeper data cleaned up" 