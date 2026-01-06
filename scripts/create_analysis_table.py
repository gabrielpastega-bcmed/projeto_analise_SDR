"""
Script para criar a tabela de resultados de analise no BigQuery.

Executar uma única vez:
    python scripts/create_analysis_table.py
"""

import os

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()


def create_analysis_results_table():
    """Cria a tabela octadesk_analysis_results no BigQuery."""
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET", "octadesk")
    table_name = "octadesk_analysis_results"

    if not project_id:
        raise ValueError("BIGQUERY_PROJECT_ID não configurado")

    client = bigquery.Client(project=project_id)
    table_id = f"{project_id}.{dataset}.{table_name}"

    schema = [
        bigquery.SchemaField("chat_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("week_start", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("week_end", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("analyzed_at", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("agent_name", "STRING"),
        # CX Analysis
        bigquery.SchemaField("cx_sentiment", "STRING"),
        bigquery.SchemaField("cx_humanization_score", "FLOAT64"),
        bigquery.SchemaField("cx_nps_prediction", "FLOAT64"),
        bigquery.SchemaField("cx_resolution_status", "STRING"),
        bigquery.SchemaField("cx_satisfaction_comment", "STRING"),
        # Sales Analysis
        bigquery.SchemaField("sales_funnel_stage", "STRING"),
        bigquery.SchemaField("sales_outcome", "STRING"),
        bigquery.SchemaField("sales_rejection_reason", "STRING"),
        bigquery.SchemaField("sales_next_step", "STRING"),
        # Product Analysis
        bigquery.SchemaField("products_mentioned", "STRING", mode="REPEATED"),
        bigquery.SchemaField("interest_level", "STRING"),
        bigquery.SchemaField("trends", "STRING", mode="REPEATED"),
        # QA Analysis
        bigquery.SchemaField("qa_script_adherence", "BOOL"),
        bigquery.SchemaField("key_questions_asked", "STRING", mode="REPEATED"),
        bigquery.SchemaField("improvement_areas", "STRING", mode="REPEATED"),
    ]

    table = bigquery.Table(table_id, schema=schema)

    # Particionamento por semana para otimizar consultas
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="week_start",
    )

    # Clustering por agente para consultas frequentes
    table.clustering_fields = ["agent_name"]

    try:
        table = client.create_table(table)
        print(f"[OK] Tabela criada: {table_id}")
        print(f"     Schema: {len(schema)} campos")
        print("     Particionamento: week_start")
        print("     Clustering: agent_name")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"[INFO] Tabela ja existe: {table_id}")
        else:
            raise e

    return table_id


if __name__ == "__main__":
    create_analysis_results_table()
