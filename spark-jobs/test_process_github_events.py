#!/usr/bin/env python3
"""
Tests for GitHub Events Processor

This module contains unit tests for the GitHub Events Processor.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
from datetime import datetime, timezone

import pyspark
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, BooleanType

from process_github_events import (
    define_github_event_schema,
    write_to_postgres
)


class TestGitHubEventsProcessor(unittest.TestCase):
    """Test cases for the GitHub Events Processor."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are used for all tests."""
        # Create a local Spark session for testing
        cls.spark = SparkSession.builder \
            .appName("GitHubEventsProcessorTest") \
            .master("local[2]") \
            .getOrCreate()

    @classmethod
    def tearDownClass(cls):
        """Tear down test fixtures that were used for all tests."""
        # Stop the Spark session
        cls.spark.stop()

    def setUp(self):
        """Set up test fixtures for each test."""
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
            "payload": {"action": "started"},
            "public": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "collected_at": datetime.now(timezone.utc).isoformat(),
            "languages": ["Python", "JavaScript"],
            "repository_metrics": {
                "repo_id": 456,
                "repo_name": "testorg/testrepo",
                "stars": 1,
                "forks": 0,
                "watchers": 0,
                "open_issues": 0
            }
        }

    def test_define_github_event_schema(self):
        """Test the GitHub event schema definition."""
        schema = define_github_event_schema()
        
        # Verify the schema has the expected fields
        self.assertIsInstance(schema, StructType)
        field_names = [field.name for field in schema.fields]
        expected_fields = ["id", "type", "actor", "repo", "payload", "public", 
                          "created_at", "org", "collected_at", "languages", 
                          "repository_metrics"]
        for field in expected_fields:
            self.assertIn(field, field_names)

    def test_write_to_postgres(self):
        """Test writing a batch to PostgreSQL."""
        # Create a test DataFrame
        data = [
            ("12345", "WatchEvent", 123, "testuser", 456, "testorg/testrepo",
             datetime.now(timezone.utc), datetime.now(timezone.utc), 
             datetime.now(timezone.utc), True)
        ]
        schema = StructType([
            StructField("id", StringType(), True),
            StructField("type", StringType(), True),
            StructField("actor_id", IntegerType(), True),
            StructField("actor_login", StringType(), True),
            StructField("repo_id", IntegerType(), True),
            StructField("repo_name", StringType(), True),
            StructField("created_at", pyspark.sql.types.TimestampType(), True),
            StructField("collected_at", pyspark.sql.types.TimestampType(), True),
            StructField("processed_at", pyspark.sql.types.TimestampType(), True),
            StructField("public", BooleanType(), True)
        ])
        df = self.spark.createDataFrame(data, schema)
        
        # Mock the DataFrame.write method
        with patch.object(df, 'write') as mock_write:
            mock_format = MagicMock()
            mock_write.format.return_value = mock_format
            mock_option = MagicMock()
            mock_format.option.return_value = mock_option
            mock_mode = MagicMock()
            mock_option.mode.return_value = mock_mode
            
            # Call the function
            write_to_postgres(df, "events", 1)
            
            # Verify the correct methods were called
            mock_write.format.assert_called_once_with("jdbc")
            mock_format.option.assert_any_call("url", "jdbc:postgresql://postgres:5432/github_events")
            mock_format.option.assert_any_call("dbtable", "events")
            mock_option.mode.assert_called_once_with("append")
            mock_mode.save.assert_called_once()


if __name__ == '__main__':
    unittest.main() 