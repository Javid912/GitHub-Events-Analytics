-- GitHub Events Analytics Database Schema

-- Create database
CREATE DATABASE github_events;

-- Connect to the database
\c github_events;

-- Enable TimescaleDB extension (if available)
-- CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create events table
CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(255) PRIMARY KEY,
    type VARCHAR(100) NOT NULL,
    actor_id INTEGER NOT NULL,
    actor_login VARCHAR(255) NOT NULL,
    repo_id INTEGER NOT NULL,
    repo_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    collected_at TIMESTAMP NOT NULL,
    processed_at TIMESTAMP NOT NULL,
    public BOOLEAN NOT NULL,
    CONSTRAINT unique_event UNIQUE (id)
);

-- Create index on events table
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events (created_at);
CREATE INDEX IF NOT EXISTS idx_events_type ON events (type);
CREATE INDEX IF NOT EXISTS idx_events_actor_id ON events (actor_id);
CREATE INDEX IF NOT EXISTS idx_events_repo_id ON events (repo_id);

-- Create repository metrics table
CREATE TABLE IF NOT EXISTS repository_metrics (
    id SERIAL PRIMARY KEY,
    repo_id INTEGER NOT NULL,
    repo_name VARCHAR(255) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    event_count INTEGER NOT NULL,
    stars INTEGER NOT NULL DEFAULT 0,
    forks INTEGER NOT NULL DEFAULT 0,
    pull_requests INTEGER NOT NULL DEFAULT 0,
    issues INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT unique_repo_window UNIQUE (repo_id, window_start, window_end)
);

-- Create index on repository metrics table
CREATE INDEX IF NOT EXISTS idx_repo_metrics_window ON repository_metrics (window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_repo_metrics_repo_id ON repository_metrics (repo_id);

-- Create event type distribution table
CREATE TABLE IF NOT EXISTS event_type_distribution (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    event_count INTEGER NOT NULL,
    CONSTRAINT unique_event_type_window UNIQUE (event_type, window_start, window_end)
);

-- Create index on event type distribution table
CREATE INDEX IF NOT EXISTS idx_event_type_dist_window ON event_type_distribution (window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_event_type_dist_type ON event_type_distribution (event_type);

-- Create user activity table
CREATE TABLE IF NOT EXISTS user_activity (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    username VARCHAR(255) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    event_count INTEGER NOT NULL,
    repos_contributed INTEGER NOT NULL,
    event_types TEXT,
    CONSTRAINT unique_user_window UNIQUE (user_id, window_start, window_end)
);

-- Create index on user activity table
CREATE INDEX IF NOT EXISTS idx_user_activity_window ON user_activity (window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_user_activity_user_id ON user_activity (user_id);

-- Create language trends table
CREATE TABLE IF NOT EXISTS language_trends (
    id SERIAL PRIMARY KEY,
    language VARCHAR(100) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    event_count INTEGER NOT NULL,
    CONSTRAINT unique_language_window UNIQUE (language, window_start, window_end)
);

-- Create index on language trends table
CREATE INDEX IF NOT EXISTS idx_language_trends_window ON language_trends (window_start, window_end);
CREATE INDEX IF NOT EXISTS idx_language_trends_language ON language_trends (language);

-- Create aggregated metrics view
CREATE OR REPLACE VIEW aggregated_metrics AS
SELECT
    date_trunc('hour', window_start) AS hour,
    SUM(event_count) AS total_events,
    COUNT(DISTINCT repo_id) AS unique_repos,
    SUM(stars) AS total_stars,
    SUM(forks) AS total_forks,
    SUM(pull_requests) AS total_prs,
    SUM(issues) AS total_issues
FROM repository_metrics
GROUP BY date_trunc('hour', window_start)
ORDER BY hour DESC;

-- Create top repositories view
CREATE OR REPLACE VIEW top_repositories AS
SELECT
    repo_id,
    repo_name,
    SUM(event_count) AS total_events,
    SUM(stars) AS total_stars,
    SUM(forks) AS total_forks,
    SUM(pull_requests) AS total_prs,
    SUM(issues) AS total_issues
FROM repository_metrics
WHERE window_start >= NOW() - INTERVAL '24 hours'
GROUP BY repo_id, repo_name
ORDER BY total_events DESC
LIMIT 100;

-- Create top users view
CREATE OR REPLACE VIEW top_users AS
SELECT
    user_id,
    username,
    SUM(event_count) AS total_events,
    SUM(repos_contributed) AS total_repos_contributed
FROM user_activity
WHERE window_start >= NOW() - INTERVAL '24 hours'
GROUP BY user_id, username
ORDER BY total_events DESC
LIMIT 100;

-- Create top languages view
CREATE OR REPLACE VIEW top_languages AS
SELECT
    language,
    SUM(event_count) AS total_events
FROM language_trends
WHERE window_start >= NOW() - INTERVAL '24 hours'
GROUP BY language
ORDER BY total_events DESC
LIMIT 20;

-- Create event type summary view
CREATE OR REPLACE VIEW event_type_summary AS
SELECT
    event_type,
    SUM(event_count) AS total_events,
    ROUND(100.0 * SUM(event_count) / SUM(SUM(event_count)) OVER (), 2) AS percentage
FROM event_type_distribution
WHERE window_start >= NOW() - INTERVAL '24 hours'
GROUP BY event_type
ORDER BY total_events DESC; 