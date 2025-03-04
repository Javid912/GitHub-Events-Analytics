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
├── .github/              # GitHub Actions workflows for CI/CD
├── start.sh              # Script to start all services
├── monitor.sh            # Script to monitor service health
├── cleanup.sh            # Script to clean up the environment
├── CONTRIBUTING.md       # Guidelines for contributing to the project
├── LICENSE               # MIT License
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
   git clone https://github.com/javid912/github-events-analytics.git
   cd github-events-analytics
   ```

2. Create a `.env` file in the root directory with the following variables:
   ```
   GITHUB_API_TOKEN=your_github_token
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=github_events
   ```

3. Start the entire stack using the start script:
   ```
   ./start.sh
   ```

4. Monitor the health of all services:
   ```
   ./monitor.sh
   ```

5. Access the Grafana dashboard:
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

## Testing

The project includes comprehensive unit tests for all components:

1. Run all tests:
   ```
   ./run_tests.sh
   ```

2. Run specific component tests:
   ```
   cd data-collector
   python -m unittest test_github_events_collector.py
   
   cd ../spark-jobs
   python -m unittest test_process_github_events.py
   ```

3. Run tests with coverage:
   ```
   pytest --cov=data-collector --cov=spark-jobs
   ```

## Continuous Integration

This project uses GitHub Actions for CI/CD:

- Automated tests run on every push and pull request
- Code quality checks (linting, formatting)
- Docker images are built and pushed to Docker Hub on successful merges to main

## Monitoring

To monitor the health of all services:

```
./monitor.sh
```

This script checks:
- Service status (running, healthy, unhealthy)
- Kafka topics existence
- PostgreSQL tables
- Grafana availability
- Data flow through the system

## Stopping and Cleaning Up

1. To stop all services:
   ```
   docker-compose -f docker/docker-compose.yml down
   ```

2. To clean up the environment (stop services, remove volumes and temporary files):
   ```
   ./cleanup.sh
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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests. 