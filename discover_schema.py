"""
Script to discover BigQuery table schema.
"""

import os

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

if __name__ == "__main__":
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET")
    table = os.getenv("BIGQUERY_TABLE")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if credentials_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

    client = bigquery.Client(project=project_id)

    # Get table schema
    table_ref = f"{project_id}.{dataset}.{table}"
    table_obj = client.get_table(table_ref)

    print("=" * 60)
    print(f"Schema for: {table_ref}")
    print("=" * 60)

    for field in table_obj.schema:
        print(f"{field.name}: {field.field_type}")
