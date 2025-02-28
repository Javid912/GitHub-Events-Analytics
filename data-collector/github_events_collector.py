#!/usr/bin/env python3
"""
GitHub Events Collector

This script fetches events from the GitHub Events API and publishes them to Kafka.
It handles rate limiting, pagination, and error recovery.
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import requests
from dotenv import load_dotenv
from kafka import KafkaProducer
from kafka.errors import KafkaError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from loguru import logger

# Load environment variables
load_dotenv()

# Configuration
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "github-events")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "60"))  # seconds
MAX_PAGES_PER_POLL = int(os.getenv("MAX_PAGES_PER_POLL", "10"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configure logger
logger.remove()
logger.add(
    "github_events_collector.log",
    rotation="10 MB",
    retention="1 week",
    level=LOG_LEVEL,
)
logger.add(lambda msg: print(msg, end=""), level=LOG_LEVEL)


class GitHubEventsCollector:
    """Collects GitHub events and publishes them to Kafka."""

    def __init__(self):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Events-Analytics",
        }
        
        if GITHUB_API_TOKEN:
            self.headers["Authorization"] = f"token {GITHUB_API_TOKEN}"
            logger.info("Using GitHub API token for authentication")
        else:
            logger.warning(
                "No GitHub API token provided. Rate limits will be more restrictive."
            )
        
        self.last_etag: Optional[str] = None
        self.last_event_id: Optional[str] = None
        
        # Initialize Kafka producer
        self.producer = self._create_kafka_producer()
        
        logger.info("GitHub Events Collector initialized")

    def _create_kafka_producer(self) -> KafkaProducer:
        """Create and return a Kafka producer instance."""
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=5,
                max_in_flight_requests_per_connection=1,
            )
            logger.info(f"Connected to Kafka at {KAFKA_BOOTSTRAP_SERVERS}")
            return producer
        except KafkaError as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            raise

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def _fetch_events_page(self, page: int = 1) -> tuple[List[Dict[str, Any]], Optional[str], Dict[str, str]]:
        """
        Fetch a page of events from the GitHub Events API.
        
        Args:
            page: Page number to fetch
            
        Returns:
            Tuple of (events list, etag, response headers)
        """
        url = f"https://api.github.com/events?page={page}"
        headers = self.headers.copy()
        
        if self.last_etag and page == 1:
            headers["If-None-Match"] = self.last_etag
        
        logger.debug(f"Fetching events page {page}")
        response = requests.get(url, headers=headers)
        
        # Handle rate limiting
        if response.status_code == 403 and "X-RateLimit-Remaining" in response.headers:
            remaining = int(response.headers["X-RateLimit-Remaining"])
            if remaining == 0:
                reset_time = int(response.headers["X-RateLimit-Reset"])
                sleep_time = max(reset_time - time.time(), 0) + 1
                logger.warning(f"Rate limit exceeded. Sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                return self._fetch_events_page(page)
        
        # Handle not modified (304) response
        if response.status_code == 304:
            logger.info("No new events since last poll")
            return [], self.last_etag, response.headers
        
        # Handle other errors
        response.raise_for_status()
        
        etag = response.headers.get("ETag")
        return response.json(), etag, response.headers

    def _publish_event_to_kafka(self, event: Dict[str, Any]) -> None:
        """
        Publish a GitHub event to Kafka.
        
        Args:
            event: GitHub event data
        """
        event_id = event.get("id", "unknown")
        event_type = event.get("type", "unknown")
        
        try:
            # Add timestamp for processing
            event["collected_at"] = datetime.now(timezone.utc).isoformat()
            
            # Use repository name as key for partitioning if available
            key = None
            if "repo" in event and "name" in event["repo"]:
                key = event["repo"]["name"]
            
            # Send to Kafka
            self.producer.send(
                KAFKA_TOPIC,
                key=key,
                value=event,
            )
            logger.debug(f"Published event {event_id} of type {event_type}")
        except Exception as e:
            logger.error(f"Failed to publish event {event_id}: {e}")

    def poll_events(self) -> None:
        """Poll for new GitHub events and publish them to Kafka."""
        try:
            new_events_count = 0
            latest_event_id = None
            
            # Fetch multiple pages if needed
            for page in range(1, MAX_PAGES_PER_POLL + 1):
                events, etag, headers = self._fetch_events_page(page)
                
                if not events:
                    break
                
                # Track the latest event ID from the first page
                if page == 1 and events:
                    latest_event_id = events[0].get("id")
                
                # Process events
                for event in events:
                    event_id = event.get("id")
                    
                    # Stop if we've seen this event before
                    if event_id == self.last_event_id:
                        logger.debug(f"Reached previously processed event {event_id}")
                        break
                    
                    self._publish_event_to_kafka(event)
                    new_events_count += 1
                
                # Check if we've reached previously seen events
                if any(e.get("id") == self.last_event_id for e in events):
                    break
                
                # Check if there are more pages
                if "Link" not in headers or 'rel="next"' not in headers["Link"]:
                    break
            
            # Update state for next poll
            if latest_event_id:
                self.last_event_id = latest_event_id
            if etag:
                self.last_etag = etag
            
            # Flush messages to Kafka
            self.producer.flush()
            
            logger.info(f"Poll completed: {new_events_count} new events published")
        except Exception as e:
            logger.error(f"Error during event polling: {e}")

    def run(self) -> None:
        """Run the collector in a continuous loop."""
        logger.info("Starting GitHub Events Collector")
        
        try:
            while True:
                self.poll_events()
                logger.info(f"Sleeping for {POLL_INTERVAL} seconds")
                time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Collector stopped by user")
        finally:
            if self.producer:
                self.producer.close()
                logger.info("Kafka producer closed")


if __name__ == "__main__":
    collector = GitHubEventsCollector()
    collector.run() 