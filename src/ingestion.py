"""
Data ingestion module for loading chat data from various sources.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Optional

from dotenv import load_dotenv
from google.cloud import bigquery

from src.models import Chat

# Load environment variables
load_dotenv()


def load_chats_from_json(file_path: str) -> List[Chat]:
    """
    Loads chats from a JSON file and parses them into Chat objects.

    Args:
        file_path: Path to the JSON file

    Returns:
        List of Chat objects
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chats = []
    for item in data:
        try:
            chat = Chat(**item)
            chats.append(chat)
        except Exception as e:
            print(f"Error parsing chat {item.get('id', 'unknown')}: {e}")
            continue

    return chats


def load_chats_from_bigquery(days: Optional[int] = None, limit: Optional[int] = None) -> List[Chat]:
    """
    Loads chats from BigQuery and parses them into Chat objects.

    Uses environment variables for configuration:
    - BIGQUERY_PROJECT_ID: GCP project ID
    - BIGQUERY_DATASET: BigQuery dataset name
    - BIGQUERY_TABLE: BigQuery table name
    - GOOGLE_APPLICATION_CREDENTIALS: Path to service account JSON
    - ANALYSIS_DAYS: Default number of days to analyze (default: 7)

    Args:
        days: Number of days to look back (overrides ANALYSIS_DAYS env var)
        limit: Maximum number of chats to return (optional)

    Returns:
        List of Chat objects
    """
    # Get configuration from environment
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET")
    table = os.getenv("BIGQUERY_TABLE")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    default_days = int(os.getenv("ANALYSIS_DAYS", "7"))

    if not all([project_id, dataset, table]):
        raise ValueError(
            "Missing BigQuery configuration. "
            "Please set BIGQUERY_PROJECT_ID, BIGQUERY_DATASET, and BIGQUERY_TABLE "
            "in your .env file."
        )

    # Set credentials path for google-cloud-bigquery
    if credentials_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

    # Initialize BigQuery client
    client = bigquery.Client(project=project_id)

    # Calculate date filter
    analysis_days = days if days is not None else default_days
    start_date = datetime.now() - timedelta(days=analysis_days)
    start_date_str = start_date.strftime("%Y-%m-%d")

    # Build query
    query = f"""
    SELECT *
    FROM `{project_id}.{dataset}.{table}`
    WHERE DATE(firstMessageDate) >= @start_date
    ORDER BY firstMessageDate DESC
    """  # nosec

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "STRING", start_date_str),
        ]
    )

    if limit:
        query += f"\nLIMIT {limit}"

    print(f"Querying BigQuery: {project_id}.{dataset}.{table}")
    print(f"Date filter: >= {start_date_str} ({analysis_days} days)")

    # Execute query
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()

    # Convert to list of dicts
    rows = [dict(row) for row in results]
    print(f"Retrieved {len(rows)} rows from BigQuery")

    # Parse into Chat objects
    chats = []
    errors = 0
    for item in rows:
        try:
            chat = Chat(**item)
            chats.append(chat)
        except Exception as e:
            errors += 1
            if errors <= 5:  # Only print first 5 errors
                print(f"Error parsing chat {item.get('id', 'unknown')}: {e}")

    if errors > 5:
        print(f"... and {errors - 5} more parsing errors")

    print(f"Successfully parsed {len(chats)} chats")
    return chats


def get_data_source() -> str:
    """
    Returns the configured data source type.

    Returns:
        "bigquery" if BigQuery is configured, "json" otherwise
    """
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET")
    table = os.getenv("BIGQUERY_TABLE")

    if all([project_id, dataset, table]):
        return "bigquery"
    return "json"
