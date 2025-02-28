# GitHub Events Analytics

A real-time analytics platform for GitHub events data, providing insights into repository popularity, user activity, and programming language trends.

## Architecture

This project implements a complete streaming data pipeline with the following components:

1. **Data Collection**
   - Python scripts fetch data from GitHub Events API
   - Events are published to Apache Kafka topics

2. **Stream Processing**
   - Apache Spark Streaming processes GitHub events in real-time
   - Analyzes repository popularity, user activity, and language trends
   - Calculates metrics using sliding windows

3. **Data Storage**
   - PostgreSQL database with optimized schema
   - Tables for events, repositories, users, and aggregated metrics

4. **Visualization**
   - Grafana dashboards for real-time analytics visualization

## Project Structure

```
github-events-analytics/
├── data-collector/       # Python scripts for GitHub API data collection
├── kafka-setup/          # Kafka configuration and setup files
├── spark-jobs/           # Spark streaming applications
├── database/             # Database schema and migration scripts
├── grafana/              # Grafana dashboard definitions
├── docker/               # Docker compose files for the entire stack
└── README.md             # This file
```

## Key Metrics

The system analyzes the following metrics:

1. Repository popularity over time (stars, forks, watches)
2. Event type distribution (push, pull request, issue, etc.)
3. Active users and their contribution patterns
4. Programming language trends and adoption

## Prerequisites

- Docker and Docker Compose
- Git
- GitHub API token (for higher rate limits)

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/github-events-analytics.git
   cd github-events-analytics
   ```

2. Create a `.env` file in the root directory with the following variables:
   ```
   GITHUB_API_TOKEN=your_github_token
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=github_events
   ```

3. Start the entire stack using Docker Compose:
   ```
   docker-compose -f docker/docker-compose.yml up -d
   ```

4. Access the Grafana dashboard:
   ```
   http://localhost:3000
   ```
   Default credentials: admin/admin

## Component Details

### Data Collector

Python scripts that fetch data from the GitHub Events API and publish to Kafka topics. The collector handles rate limiting, pagination, and error recovery.

### Kafka Setup

Kafka configuration for topic creation, retention policies, and consumer groups.

### Spark Jobs

Spark Streaming applications that process the event stream, calculate metrics, and store results in PostgreSQL.

### Database

PostgreSQL database schema with tables for raw events, processed metrics, and aggregated data.

### Grafana

Pre-configured dashboards for visualizing GitHub event metrics and trends.

## Stopping the Services

To stop all services:
```
docker-compose -f docker/docker-compose.yml down
```

## Development

To run individual components during development:

- Data Collector:
  ```
  cd data-collector
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  python github_events_collector.py
  ```

- Spark Jobs:
  ```
  cd spark-jobs
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  python process_github_events.py
  ```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 