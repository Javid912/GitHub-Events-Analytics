# Quick Start Guide: GitHub Events Analytics

This guide provides the essential steps to get the GitHub Events Analytics project up and running quickly.

## Prerequisites

- Docker and Docker Compose installed
- Git installed
- A GitHub API token (get one from https://github.com/settings/tokens)

## Step 1: Set Up Environment

1. Create a `.env` file from the template:

```bash
cp .env.template .env
```

2. Edit the `.env` file and add your GitHub API token:

```
GITHUB_API_TOKEN=your_github_token_here
```

## Step 2: Start the System

Run the start script:

```bash
./start.sh
```

This will start all components:
- Zookeeper and Kafka
- PostgreSQL database
- GitHub Events collector
- Spark streaming job
- Grafana dashboards

## Step 3: Verify the System

1. Check that all services are running:

```bash
docker-compose -f docker/docker-compose.yml ps
```

2. Use the monitoring script to check the health of all services:

```bash
./monitor.sh
```

3. Access the Kafka UI to see events being collected:
   - Open http://localhost:8080 in your browser
   - Navigate to the "Topics" section
   - Check that the `github-events` topic exists and has messages

4. Access Grafana to see the analytics dashboards:
   - Open http://localhost:3000 in your browser
   - Login with username `admin` and password `admin`
   - Navigate to the "GitHub Events Overview" dashboard

## Step 4: Test Data Flow

1. Check that events are being collected:

```bash
docker logs github-events-collector
```

2. Check that events are being processed:

```bash
docker logs spark-streaming
```

3. Check that data is being stored in PostgreSQL:

```bash
docker exec -it postgres psql -U postgres -d github_events -c "SELECT COUNT(*) FROM events;"
```

## Step 5: Explore the Data

In Grafana, explore the different visualizations:
- Repository popularity trends
- Event type distribution
- User activity
- Programming language trends

## Step 6: Run Tests (Optional)

If you want to run the tests:

```bash
./run_tests.sh
```

## Step 7: Stop the System

When you're done, stop all services:

```bash
docker-compose -f docker/docker-compose.yml down
```

## Troubleshooting

If you encounter issues:

1. Use the monitoring script to check the health of all services:
```bash
./monitor.sh
```

2. Check the logs of specific components:
```bash
docker logs <container-name>
```

3. Verify that all services can communicate with each other
4. Check that your GitHub API token is valid
5. Ensure Docker has enough resources allocated

## Next Steps

- Read the `LEARNING_GUIDE.md` for a deeper understanding of the system
- Explore the code in each component to understand how they work
- Try modifying the dashboards in Grafana to create custom visualizations
- Consider extending the system with additional metrics or data sources 