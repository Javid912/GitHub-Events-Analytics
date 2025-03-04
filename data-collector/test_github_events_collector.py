#!/usr/bin/env python3
"""
Tests for GitHub Events Collector

This module contains unit tests for the GitHub Events Collector.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
from datetime import datetime, timezone

from github_events_collector import GitHubEventsCollector
from event_parser import validate_event, extract_languages, extract_repository_metrics


class TestGitHubEventsCollector(unittest.TestCase):
    """Test cases for the GitHub Events Collector."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock environment variables
        self.env_patcher = patch.dict('os.environ', {
            'GITHUB_API_TOKEN': 'test_token',
            'KAFKA_BOOTSTRAP_SERVERS': 'localhost:9092',
            'KAFKA_TOPIC': 'test-topic'
        })
        self.env_patcher.start()
        
        # Mock Kafka producer
        self.kafka_patcher = patch('github_events_collector.KafkaProducer')
        self.mock_producer = self.kafka_patcher.start()
        
        # Sample event data
        self.sample_event = {
            "id": "12345",
            "type": "WatchEvent",
            "actor": {
                "id": 123,
                "login": "testuser",
                "display_login": "testuser",
                "url": "https://api.github.com/users/testuser",
                "avatar_url": "https://avatars.githubusercontent.com/u/123"
            },
            "repo": {
                "id": 456,
                "name": "testorg/testrepo",
                "url": "https://api.github.com/repos/testorg/testrepo"
            },
            "payload": {
                "action": "started"
            },
            "public": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Mock response for API calls
        self.mock_response = MagicMock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = [self.sample_event]
        self.mock_response.headers = {
            'ETag': 'test-etag',
            'X-RateLimit-Remaining': '4999',
            'X-RateLimit-Reset': str(int(datetime.now(timezone.utc).timestamp()) + 3600)
        }

    def tearDown(self):
        """Tear down test fixtures."""
        self.env_patcher.stop()
        self.kafka_patcher.stop()

    @patch('github_events_collector.requests.get')
    def test_fetch_events_page(self, mock_get):
        """Test fetching a page of events from the GitHub API."""
        mock_get.return_value = self.mock_response
        
        collector = GitHubEventsCollector()
        events, etag, headers = collector._fetch_events_page()
        
        # Verify the request was made correctly
        mock_get.assert_called_once()
        self.assertEqual(mock_get.call_args[0][0], 'https://api.github.com/events?page=1')
        
        # Verify the response was processed correctly
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['id'], '12345')
        self.assertEqual(etag, 'test-etag')

    @patch('github_events_collector.requests.get')
    def test_poll_events(self, mock_get):
        """Test polling for new GitHub events."""
        mock_get.return_value = self.mock_response
        
        collector = GitHubEventsCollector()
        collector.producer = MagicMock()
        collector.poll_events()
        
        # Verify events were published to Kafka
        collector.producer.send.assert_called_once()
        collector.producer.flush.assert_called_once()
        
        # Verify state was updated
        self.assertEqual(collector.last_etag, 'test-etag')
        self.assertEqual(collector.last_event_id, '12345')

    @patch('github_events_collector.requests.get')
    def test_rate_limiting(self, mock_get):
        """Test handling of rate limiting."""
        # Mock a rate-limited response
        rate_limited_response = MagicMock()
        rate_limited_response.status_code = 403
        rate_limited_response.headers = {
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': str(int(datetime.now(timezone.utc).timestamp()) + 10)
        }
        
        # Mock a successful response after rate limiting
        success_response = self.mock_response
        
        # Return rate-limited response first, then success response
        mock_get.side_effect = [rate_limited_response, success_response]
        
        with patch('github_events_collector.time.sleep') as mock_sleep:
            collector = GitHubEventsCollector()
            events, etag, headers = collector._fetch_events_page()
            
            # Verify sleep was called
            mock_sleep.assert_called_once()
            
            # Verify the second request was made
            self.assertEqual(mock_get.call_count, 2)
            
            # Verify we got the successful response
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]['id'], '12345')


class TestEventParser(unittest.TestCase):
    """Test cases for the Event Parser."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample event data
        self.sample_event = {
            "id": "12345",
            "type": "WatchEvent",
            "actor": {
                "id": 123,
                "login": "testuser",
                "display_login": "testuser",
                "url": "https://api.github.com/users/testuser",
                "avatar_url": "https://avatars.githubusercontent.com/u/123"
            },
            "repo": {
                "id": 456,
                "name": "testorg/testrepo",
                "url": "https://api.github.com/repos/testorg/testrepo"
            },
            "payload": {
                "action": "started"
            },
            "public": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Sample push event with language data
        self.push_event = {
            "id": "67890",
            "type": "PushEvent",
            "actor": {
                "id": 123,
                "login": "testuser",
                "url": "https://api.github.com/users/testuser",
                "avatar_url": "https://avatars.githubusercontent.com/u/123"
            },
            "repo": {
                "id": 456,
                "name": "testorg/testrepo",
                "url": "https://api.github.com/repos/testorg/testrepo"
            },
            "payload": {
                "commits": [
                    {
                        "sha": "abc123",
                        "message": "Test commit",
                        "languages": ["Python", "JavaScript"]
                    }
                ]
            },
            "public": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    def test_validate_event(self):
        """Test event validation."""
        validated = validate_event(self.sample_event)
        
        # Verify the event was validated correctly
        self.assertEqual(validated['id'], '12345')
        self.assertEqual(validated['type'], 'WatchEvent')
        self.assertIn('languages', validated)
        self.assertIn('repository_metrics', validated)

    def test_extract_languages(self):
        """Test extracting languages from an event."""
        languages = extract_languages(self.push_event)
        
        # Verify languages were extracted correctly
        self.assertEqual(len(languages), 2)
        self.assertIn('Python', languages)
        self.assertIn('JavaScript', languages)

    def test_extract_repository_metrics(self):
        """Test extracting repository metrics from an event."""
        metrics = extract_repository_metrics(self.sample_event)
        
        # Verify metrics were extracted correctly
        self.assertEqual(metrics['repo_id'], 456)
        self.assertEqual(metrics['repo_name'], 'testorg/testrepo')
        self.assertEqual(metrics['stars'], 1)  # WatchEvent with action 'started'


if __name__ == '__main__':
    unittest.main() 