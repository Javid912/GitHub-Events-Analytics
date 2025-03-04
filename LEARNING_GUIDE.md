# GitHub Events Analytics: A Learning Guide

This guide will help you understand the GitHub Events Analytics project, the technologies used, and how data flows through the system. It's designed for beginners to data streaming architectures.

## Table of Contents

1. [Introduction to Data Streaming](#1-introduction-to-data-streaming)
2. [Project Architecture Overview](#2-project-architecture-overview)
3. [Key Technologies Explained](#3-key-technologies-explained)
4. [Data Flow Walkthrough](#4-data-flow-walkthrough)
5. [Component Deep Dives](#5-component-deep-dives)
6. [Running and Testing the Project](#6-running-and-testing-the-project)
7. [Monitoring and Troubleshooting](#7-monitoring-and-troubleshooting)
8. [Development Workflow](#8-development-workflow)
9. [Next Steps and Extensions](#9-next-steps-and-extensions)
10. [Learning Resources](#10-learning-resources)

## 1. Introduction to Data Streaming

### What is Data Streaming?

Data streaming is a technology paradigm where data is processed continuously as it's generated, rather than in batches. This enables real-time analytics and insights.

### Key Concepts in Data Streaming

- **Event**: A discrete piece of data representing something that happened (e.g., a GitHub commit, star, or issue)
- **Stream**: A continuous flow of events
- **Producer**: A component that generates events (our GitHub API collector)
- **Consumer**: A component that processes events (our Spark streaming job)
- **Message Broker**: A middleware that stores and routes events between producers and consumers (Kafka)
- **Stream Processing**: Analyzing and transforming data as it flows through the system

### Batch vs. Stream Processing

| Batch Processing | Stream Processing |
|------------------|-------------------|
| Processes data in chunks | Processes data continuously |
| Higher latency (minutes to hours) | Lower latency (seconds to milliseconds) |
| Typically simpler to implement | More complex to implement |
| Good for historical analysis | Good for real-time insights |

## 2. Project Architecture Overview

Our GitHub Events Analytics project follows a modern streaming architecture with four main layers:

1. **Data Collection Layer**: Python scripts fetch data from GitHub's Events API
2. **Message Broker Layer**: Apache Kafka stores and distributes events
3. **Processing Layer**: Apache Spark Streaming processes and analyzes events
4. **Storage & Visualization Layer**: PostgreSQL stores processed data, and Grafana visualizes it

![Architecture Diagram](https://miro.medium.com/max/1400/1*sfYn7zFfbdxLrxH0PkBIjg.png)
*(This is a generic streaming architecture diagram - our project follows a similar pattern)*

## 3. Key Technologies Explained

### GitHub Events API

- **What it is**: REST API provided by GitHub that exposes events happening across GitHub
- **What it provides**: Data about commits, pull requests, issues, stars, forks, etc.
- **Rate limits**: 60 requests/hour for unauthenticated requests, 5,000 requests/hour with authentication

### Apache Kafka

- **What it is**: A distributed event streaming platform
- **Key concepts**:
  - **Topics**: Categories for events (we use `github-events`)
  - **Partitions**: Divisions of a topic for parallel processing
  - **Producers**: Applications that send data to Kafka
  - **Consumers**: Applications that read data from Kafka
  - **Consumer Groups**: Groups of consumers that divide work

### Apache Spark Streaming

- **What it is**: A framework for processing data streams
- **Key concepts**:
  - **DStreams**: Discretized streams, the basic abstraction in Spark Streaming
  - **Micro-batches**: Small batches of data processed together
  - **Window operations**: Operations over sliding windows of time
  - **Stateful processing**: Maintaining state across batches

### PostgreSQL

- **What it is**: A powerful, open-source relational database
- **How we use it**: To store processed events and aggregated metrics

### Grafana

- **What it is**: A visualization and monitoring platform
- **How we use it**: To create dashboards that visualize GitHub event metrics

## 4. Data Flow Walkthrough

Let's follow an event through our system:

1. **Event Creation**: A user stars a repository on GitHub
2. **Data Collection**: 
   - Our Python collector polls the GitHub Events API
   - It detects the new star event
   - It formats the event and sends it to Kafka

3. **Message Brokering**:
   - Kafka receives the event and stores it in the `github-events` topic
   - The event waits in Kafka until consumed

4. **Stream Processing**:
   - Spark Streaming job consumes the event from Kafka
   - It extracts relevant information (repository, user, event type)
   - It performs aggregations (e.g., stars per repository over time)
   - It writes results to PostgreSQL

5. **Storage and Visualization**:
   - PostgreSQL stores the processed data
   - Grafana queries PostgreSQL and updates dashboards in real-time

## 5. Component Deep Dives

### Data Collector (`data-collector/`)

The data collector is a Python application that:
- Polls the GitHub Events API at regular intervals
- Handles rate limiting and pagination
- Validates and enriches event data
- Publishes events to Kafka

Key files:
- `github_events_collector.py`: Main collector script
- `event_parser.py`: Utilities for parsing and validating events
- `test_github_events_collector.py`: Unit tests for the collector

### Kafka Setup (`kafka-setup/`)

This component configures Kafka with:
- Topics for raw and processed events
- Appropriate partitioning for parallel processing
- Retention policies for data

### Spark Jobs (`spark-jobs/`)

The Spark streaming application:
- Consumes events from Kafka
- Processes them using Structured Streaming
- Calculates metrics using window functions
- Writes results to PostgreSQL

Key files:
- `process_github_events.py`: Main Spark streaming job
- `test_process_github_events.py`: Unit tests for the Spark job

### Database (`database/`)

The PostgreSQL database schema:
- Stores raw events
- Stores aggregated metrics
- Provides views for common queries

Key file:
- `schema.sql`: Database schema definition

### Grafana (`grafana/`)

Grafana dashboards that visualize:
- Repository popularity
- Event type distribution
- User activity
- Programming language trends

### Testing and CI/CD

The project includes:
- Unit tests for key components
- A test runner script (`run_tests.sh`)
- CI/CD workflow (`.github/workflows/ci.yml`)

### Monitoring and Management

The project includes:
- A monitoring script (`monitor.sh`) to check system health
- A cleanup script (`cleanup.sh`) to reset the environment

## 6. Running and Testing the Project

### Prerequisites

Before starting, ensure you have:

- Docker and Docker Compose installed
- Git installed
- A GitHub API token (for higher rate limits)

### Step 1: Clone the Repository

If you haven't already:

```bash
git clone https://github.com/yourusername/github-events-analytics.git
cd github-events-analytics
```

### Step 2: Configure Environment Variables

Create a `.env` file from the template:

```bash
cp .env.template .env
```

Edit the `.env` file and add your GitHub API token:

```
GITHUB_API_TOKEN=your_github_token_here
```

### Step 3: Start the Services

Run the start script:

```bash
./start.sh
```

This will:
1. Start Zookeeper and Kafka
2. Start PostgreSQL
3. Start the GitHub Events collector
4. Start the Spark streaming job
5. Start Grafana

### Step 4: Verify Services are Running

Check that all services are running using the monitoring script:

```bash
./monitor.sh
```

This will check:
- Service health for all containers
- Kafka topic existence and message flow
- PostgreSQL connection and table existence
- Grafana availability
- Data flow through the system

### Step 5: Access the Dashboards

1. **Kafka UI**: http://localhost:8080
   - Verify that the `github-events` topic exists
   - Check that messages are being produced

2. **Grafana**: http://localhost:3000
   - Login with admin/admin
   - Navigate to the GitHub Events Overview dashboard
   - You should start seeing data within a few minutes

### Step 6: Test Data Flow

To verify the entire pipeline is working:

1. Check Kafka UI to see events being produced
2. Connect to PostgreSQL to see data being stored:

```bash
docker exec -it postgres psql -U postgres -d github_events
```

Then run:

```sql
SELECT COUNT(*) FROM events;
```

You should see a count greater than 0 after a few minutes.

### Step 7: Explore the Data

In Grafana, explore the different panels:
- Repository Activity Over Time
- Event Type Distribution
- Top Programming Languages
- Top Repositories
- Most Active Users
- Overall Activity Trends

### Step 8: Running Tests

To run the automated tests:

```bash
./run_tests.sh
```

This will run unit tests for:
- The GitHub Events collector
- The Spark processing job

### Step 9: Stop and Clean Up

When you're done, stop all services and clean up:

```bash
./cleanup.sh
```

This will:
- Stop all Docker containers
- Remove Docker volumes
- Delete temporary files and logs

## 7. Monitoring and Troubleshooting

### Using the Monitoring Script

The `monitor.sh` script provides a comprehensive health check:

```bash
./monitor.sh
```

It checks:
- Container status for all services
- Kafka topics and message flow
- PostgreSQL connection and tables
- Grafana availability
- End-to-end data flow

### Monitoring Tools

- **Kafka UI**: Monitor Kafka topics, producers, and consumers
  - Access at: http://localhost:8080

- **Grafana**: Monitor metrics and system health
  - Access at: http://localhost:3000

### Common Issues and Solutions

- **Data collector not receiving events**:
  - Check GitHub API rate limits
  - Verify your API token is valid
  - Check network connectivity

- **Spark job failing**:
  - Check Spark logs for errors
  - Verify Kafka connectivity
  - Check PostgreSQL connectivity

- **No data in Grafana**:
  - Verify PostgreSQL contains data
  - Check Grafana data source configuration
  - Verify dashboard queries

### Viewing Logs

To view logs for a specific service:

```bash
docker logs [service-name]
```

For example:

```bash
docker logs github-events-collector
docker logs spark-streaming
```

## 8. Development Workflow

### Contributing to the Project

The project follows a standard GitHub workflow:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests locally
5. Submit a pull request

For detailed guidelines, see the [CONTRIBUTING.md](CONTRIBUTING.md) file.

### Continuous Integration

The project uses GitHub Actions for CI/CD:

- Automated tests run on every pull request
- Code quality checks ensure consistency
- Integration tests verify system functionality

The workflow is defined in `.github/workflows/ci.yml`.

### Testing Strategy

The project employs multiple testing levels:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test the entire system flow

### Code Standards

The project follows:

- PEP 8 style guide for Python code
- Comprehensive docstrings and comments
- Clear commit messages

## 9. Next Steps and Extensions

Once you're comfortable with the basic system, consider these extensions:

- Add more event types and metrics
- Implement machine learning for trend prediction
- Add alerting for unusual activity
- Scale the system to handle higher volumes
- Add authentication and multi-user support

## 10. Learning Resources

### Apache Kafka

- [Apache Kafka Official Documentation](https://kafka.apache.org/documentation/)
- [Kafka: The Definitive Guide](https://www.confluent.io/resources/kafka-the-definitive-guide/)
- [Confluent Kafka Tutorials](https://kafka-tutorials.confluent.io/)

### Apache Spark

- [Apache Spark Official Documentation](https://spark.apache.org/docs/latest/)
- [Spark Streaming Programming Guide](https://spark.apache.org/docs/latest/streaming-programming-guide.html)
- [Learning Spark, 2nd Edition](https://pages.databricks.com/rs/094-YMS-629/images/LearningSpark2.0.pdf)

### PostgreSQL

- [PostgreSQL Official Documentation](https://www.postgresql.org/docs/)
- [PostgreSQL Tutorial](https://www.postgresqltutorial.com/)

### Grafana

- [Grafana Official Documentation](https://grafana.com/docs/grafana/latest/)
- [Grafana University](https://grafana.com/tutorials/)

### Data Streaming Concepts

- [Streaming 101](https://www.oreilly.com/radar/the-world-beyond-batch-streaming-101/)
- [Streaming Systems](https://www.oreilly.com/library/view/streaming-systems/9781491983867/)

---

This learning guide provides a comprehensive understanding of the GitHub Events Analytics project. As you become more familiar with the system, you can explore more advanced features and contribute to its development. The project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 