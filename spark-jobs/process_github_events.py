#!/usr/bin/env python3
"""
GitHub Events Processor

This script processes GitHub events from Kafka using Spark Structured Streaming
and stores the results in PostgreSQL.
"""

import os
import json
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, window, count, explode, split, 
    when, lit, expr, to_timestamp, current_timestamp
)
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    BooleanType, TimestampType, ArrayType, MapType
)
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC_INPUT = os.getenv("KAFKA_TOPIC_INPUT", "github-events")
KAFKA_TOPIC_OUTPUT = os.getenv("KAFKA_TOPIC_OUTPUT", "github-events-processed")
POSTGRES_URL = os.getenv("POSTGRES_URL", "jdbc:postgresql://postgres:5432/github_events")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
CHECKPOINT_LOCATION = os.getenv("CHECKPOINT_LOCATION", "/tmp/checkpoints")

# Configure logger
logger.remove()
logger.add(
    "github_events_processor.log",
    rotation="10 MB",
    retention="1 week",
    level="INFO",
)
logger.add(lambda msg: print(msg, end=""), level="INFO")


def create_spark_session():
    """Create and configure a Spark session."""
    return (
        SparkSession.builder
        .appName("GitHubEventsProcessor")
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1,org.postgresql:postgresql:42.6.0")
        .config("spark.sql.streaming.checkpointLocation", CHECKPOINT_LOCATION)
        .config("spark.sql.shuffle.partitions", "8")
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true")
        .config("spark.sql.adaptive.enabled", "true")
        .getOrCreate()
    )


def define_github_event_schema():
    """Define the schema for GitHub events."""
    return StructType([
        StructField("id", StringType(), True),
        StructField("type", StringType(), True),
        StructField("actor", StructType([
            StructField("id", IntegerType(), True),
            StructField("login", StringType(), True),
            StructField("display_login", StringType(), True),
            StructField("url", StringType(), True),
            StructField("avatar_url", StringType(), True),
        ]), True),
        StructField("repo", StructType([
            StructField("id", IntegerType(), True),
            StructField("name", StringType(), True),
            StructField("url", StringType(), True),
        ]), True),
        StructField("payload", MapType(StringType(), StringType()), True),
        StructField("public", BooleanType(), True),
        StructField("created_at", StringType(), True),
        StructField("org", StructType([
            StructField("id", IntegerType(), True),
            StructField("login", StringType(), True),
            StructField("url", StringType(), True),
            StructField("avatar_url", StringType(), True),
        ]), True),
        StructField("collected_at", StringType(), True),
        StructField("languages", ArrayType(StringType()), True),
        StructField("repository_metrics", StructType([
            StructField("repo_id", IntegerType(), True),
            StructField("repo_name", StringType(), True),
            StructField("stars", IntegerType(), True),
            StructField("forks", IntegerType(), True),
            StructField("watchers", IntegerType(), True),
            StructField("open_issues", IntegerType(), True),
        ]), True),
    ])


def process_events(spark):
    """Process GitHub events from Kafka."""
    logger.info("Starting GitHub Events Processor")
    
    # Define schema
    schema = define_github_event_schema()
    
    # Read from Kafka
    df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_TOPIC_INPUT)
        .option("startingOffsets", "latest")
        .option("failOnDataLoss", "false")
        .load()
    )
    
    # Parse JSON data
    parsed_df = (
        df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING)")
        .select(
            col("key").alias("event_key"),
            from_json(col("value"), schema).alias("event")
        )
        .select("event_key", "event.*")
    )
    
    # Convert string timestamps to actual timestamps
    events_df = (
        parsed_df
        .withColumn("created_at", to_timestamp(col("created_at")))
        .withColumn("collected_at", to_timestamp(col("collected_at")))
        .withColumn("processed_at", current_timestamp())
    )
    
    # Register as temp view for SQL queries
    events_df.createOrReplaceTempView("github_events")
    
    # Process and write raw events to PostgreSQL
    process_raw_events(events_df)
    
    # Process repository metrics
    process_repository_metrics(spark)
    
    # Process event type distribution
    process_event_type_distribution(spark)
    
    # Process user activity
    process_user_activity(spark)
    
    # Process language trends
    process_language_trends(spark)
    
    # Keep the streaming query running
    spark.streams.awaitAnyTermination()


def process_raw_events(events_df):
    """Process and store raw events."""
    logger.info("Setting up raw events processing")
    
    # Write raw events to PostgreSQL
    raw_events_query = (
        events_df
        .select(
            "id", "type", "actor.id", "actor.login", "repo.id", "repo.name",
            "created_at", "collected_at", "processed_at", "public"
        )
        .writeStream
        .foreachBatch(lambda batch_df, batch_id: write_to_postgres(
            batch_df, "events", batch_id
        ))
        .outputMode("append")
        .start()
    )
    
    return raw_events_query


def process_repository_metrics(spark):
    """Process repository popularity metrics."""
    logger.info("Setting up repository metrics processing")
    
    # Repository popularity over time (sliding window)
    repo_metrics_query = (
        spark.sql("""
            SELECT
                repo.id AS repo_id,
                repo.name AS repo_name,
                window(created_at, '1 hour', '15 minutes') AS time_window,
                count(*) AS event_count,
                count(CASE WHEN type = 'WatchEvent' THEN 1 END) AS stars,
                count(CASE WHEN type = 'ForkEvent' THEN 1 END) AS forks,
                count(CASE WHEN type = 'PullRequestEvent' THEN 1 END) AS pull_requests,
                count(CASE WHEN type = 'IssuesEvent' THEN 1 END) AS issues
            FROM github_events
            GROUP BY repo.id, repo.name, window(created_at, '1 hour', '15 minutes')
        """)
        .writeStream
        .foreachBatch(lambda batch_df, batch_id: write_to_postgres(
            batch_df, "repository_metrics", batch_id
        ))
        .outputMode("append")
        .start()
    )
    
    return repo_metrics_query


def process_event_type_distribution(spark):
    """Process event type distribution."""
    logger.info("Setting up event type distribution processing")
    
    # Event type distribution over time
    event_type_query = (
        spark.sql("""
            SELECT
                type AS event_type,
                window(created_at, '1 hour', '15 minutes') AS time_window,
                count(*) AS event_count
            FROM github_events
            GROUP BY type, window(created_at, '1 hour', '15 minutes')
        """)
        .writeStream
        .foreachBatch(lambda batch_df, batch_id: write_to_postgres(
            batch_df, "event_type_distribution", batch_id
        ))
        .outputMode("append")
        .start()
    )
    
    return event_type_query


def process_user_activity(spark):
    """Process user activity metrics."""
    logger.info("Setting up user activity processing")
    
    # User activity over time
    user_activity_query = (
        spark.sql("""
            SELECT
                actor.id AS user_id,
                actor.login AS username,
                window(created_at, '1 hour', '15 minutes') AS time_window,
                count(*) AS event_count,
                count(DISTINCT repo.id) AS repos_contributed,
                collect_list(type) AS event_types
            FROM github_events
            GROUP BY actor.id, actor.login, window(created_at, '1 hour', '15 minutes')
        """)
        .writeStream
        .foreachBatch(lambda batch_df, batch_id: write_to_postgres(
            batch_df, "user_activity", batch_id
        ))
        .outputMode("append")
        .start()
    )
    
    return user_activity_query


def process_language_trends(spark):
    """Process programming language trends."""
    logger.info("Setting up language trends processing")
    
    # Language trends over time
    language_trends_query = (
        spark.sql("""
            SELECT
                language,
                window(created_at, '1 hour', '15 minutes') AS time_window,
                count(*) AS event_count
            FROM github_events
            LATERAL VIEW explode(languages) AS language
            GROUP BY language, window(created_at, '1 hour', '15 minutes')
        """)
        .writeStream
        .foreachBatch(lambda batch_df, batch_id: write_to_postgres(
            batch_df, "language_trends", batch_id
        ))
        .outputMode("append")
        .start()
    )
    
    return language_trends_query


def write_to_postgres(batch_df, table_name, batch_id):
    """Write a batch DataFrame to PostgreSQL."""
    if batch_df.isEmpty():
        logger.info(f"Batch {batch_id} is empty, skipping write to {table_name}")
        return
    
    logger.info(f"Writing batch {batch_id} to table {table_name}")
    
    # Convert window column to string if it exists
    if "time_window" in batch_df.columns:
        batch_df = batch_df.withColumn(
            "window_start", 
            col("time_window.start")
        ).withColumn(
            "window_end", 
            col("time_window.end")
        ).drop("time_window")
    
    # Convert array columns to strings if they exist
    for field in batch_df.schema.fields:
        if isinstance(field.dataType, ArrayType):
            batch_df = batch_df.withColumn(
                field.name, 
                expr(f"array_join({field.name}, ',')")
            )
    
    # Write to PostgreSQL
    try:
        (
            batch_df.write
            .format("jdbc")
            .option("url", POSTGRES_URL)
            .option("dbtable", table_name)
            .option("user", POSTGRES_USER)
            .option("password", POSTGRES_PASSWORD)
            .option("driver", "org.postgresql.Driver")
            .mode("append")
            .save()
        )
        logger.info(f"Successfully wrote batch {batch_id} to table {table_name}")
    except Exception as e:
        logger.error(f"Error writing to PostgreSQL: {e}")


if __name__ == "__main__":
    # Create Spark session
    spark = create_spark_session()
    
    try:
        # Process events
        process_events(spark)
    except KeyboardInterrupt:
        logger.info("Processor stopped by user")
    except Exception as e:
        logger.error(f"Error in event processing: {e}")
    finally:
        spark.stop()
        logger.info("Spark session stopped") 