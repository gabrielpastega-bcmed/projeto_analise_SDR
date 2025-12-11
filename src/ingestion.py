"""
Módulo de ingestão de dados para carregar conversas de diversas fontes.
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, MutableMapping, Optional

from dotenv import load_dotenv
from google.cloud import bigquery

from src.models import Chat

# Carrega variáveis de ambiente de um arquivo .env
load_dotenv()

# --- Funções de Anonimização (LGPD) ---


def _anonymize_text(text: str) -> str:
    """
    Anonimiza informações sensíveis em um texto usando expressões regulares.

    Padrões de PII (Informações de Identificação Pessoal) cobertos:
    - Emails
    - Números de telefone (vários formatos brasileiros)
    - CPFs

    Args:
        text: O texto a ser anonimizado.

    Returns:
        O texto com as informações sensíveis substituídas por placeholders.
    """
    if not isinstance(text, str):
        return text

    # Padrão para emails
    text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL]", text)
    # Padrão para telefones (formatos: (xx) xxxxx-xxxx, xxxxx-xxxx, etc.)
    text = re.sub(r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}", "[TELEFONE]", text)
    # Padrão para CPF (xxx.xxx.xxx-xx)
    text = re.sub(r"\d{3}\.\d{3}\.\d{3}-\d{2}", "[CPF]", text)

    return text


def _anonymize_chat_data(chat_data: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """
    Aplica a anonimização em todos os campos relevantes de um dicionário de chat.

    Modifica o dicionário de entrada (in-place) para remover PII de:
    - Nomes e emails de contatos e agentes.
    - Corpo de todas as mensagens.

    Args:
        chat_data: Um dicionário mutável representando os dados brutos de um chat.

    Returns:
        O mesmo dicionário, com os campos sensíveis anonimizados.
    """
    # Anonimiza dados do contato
    if "contact" in chat_data and isinstance(chat_data["contact"], dict):
        if "name" in chat_data["contact"]:
            chat_data["contact"]["name"] = "[CONTATO]"
        if "email" in chat_data["contact"]:
            chat_data["contact"]["email"] = "[EMAIL]"

    # Anonimiza dados do agente, se houver
    if "agent" in chat_data and isinstance(chat_data["agent"], dict):
        if "name" in chat_data["agent"]:
            # Mantém o nome do agente para análise de performance, mas remove o email
            # Se a política for mais restrita, o nome também pode ser anonimizado.
            pass
        if "email" in chat_data["agent"]:
            chat_data["agent"]["email"] = "[EMAIL]"

    # Anonimiza o corpo das mensagens
    if "messages" in chat_data and isinstance(chat_data["messages"], list):
        for message in chat_data["messages"]:
            if isinstance(message, dict) and "body" in message:
                message["body"] = _anonymize_text(message["body"])

    return chat_data


def load_chats_from_json(file_path: str) -> List[Chat]:
    """
    Carrega e anonimiza conversas de um arquivo JSON, convertendo-as em objetos Chat.

    Args:
        file_path: Caminho para o arquivo JSON.

    Returns:
        Uma lista de objetos Chat com os dados sensíveis anonimizados.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    chats = []
    for item in data:
        try:
            # Etapa de anonimização antes da validação
            anonymized_item = _anonymize_chat_data(item)
            # Validação e parsing com Pydantic
            chat = Chat(**anonymized_item)
            chats.append(chat)
        except Exception as e:
            # Log de erro para chats malformados
            print(f"Erro ao processar o chat {item.get('id', 'desconhecido')}: {e}")
            continue

    return chats


def load_chats_from_bigquery(days: Optional[int] = None, limit: Optional[int] = None) -> List[Chat]:
    """
    Carrega e anonimiza conversas do BigQuery, convertendo-as em objetos Chat.

    Utiliza variáveis de ambiente para a configuração:
    - BIGQUERY_PROJECT_ID: ID do projeto no GCP.
    - BIGQUERY_DATASET: Nome do dataset no BigQuery.
    - BIGQUERY_TABLE: Nome da tabela no BigQuery.
    - GOOGLE_APPLICATION_CREDENTIALS: Caminho para o JSON da conta de serviço.
    - ANALYSIS_DAYS: Número padrão de dias para análise (padrão: 7).

    Args:
        days: Número de dias retroativos para a busca (sobrescreve a variável de ambiente ANALYSIS_DAYS).
        limit: Número máximo de chats a serem retornados (opcional).

    Returns:
        Uma lista de objetos Chat com os dados sensíveis anonimizados.
    """
    # Obtém a configuração a partir das variáveis de ambiente
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET")
    table = os.getenv("BIGQUERY_TABLE")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    default_days = int(os.getenv("ANALYSIS_DAYS", "7"))

    # Validação da configuração
    if not all([project_id, dataset, table]):
        raise ValueError(
            "Configuração do BigQuery incompleta. "
            "Defina BIGQUERY_PROJECT_ID, BIGQUERY_DATASET e BIGQUERY_TABLE "
            "no seu arquivo .env."
        )

    # Define o caminho das credenciais para a biblioteca do Google Cloud
    if credentials_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

    # Inicializa o cliente do BigQuery
    client = bigquery.Client(project=project_id)

    # Calcula o filtro de data
    analysis_days = days if days is not None else default_days
    start_date = datetime.now() - timedelta(days=analysis_days)
    start_date_str = start_date.strftime("%Y-%m-%d")

    # Constrói a query SQL
    # A query é parametrizada para evitar SQL Injection
    query = f"""
    SELECT *
    FROM `{project_id}.{dataset}.{table}`
    WHERE DATE(firstMessageDate) >= @start_date
    ORDER BY firstMessageDate DESC
    """  # nosec B608 - A construção da query é segura, pois os parâmetros vêm de env vars.

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "STRING", start_date_str),
        ]
    )

    # Adiciona o limite à query, se especificado
    if limit:
        query += f"\nLIMIT {limit}"

    print(f"Consultando o BigQuery: {project_id}.{dataset}.{table}")
    print(f"Filtro de data: >= {start_date_str} ({analysis_days} dias)")

    # Executa a query
    query_job = client.query(query, job_config=job_config)
    results = query_job.result()

    # Converte os resultados para uma lista de dicionários
    rows = [dict(row) for row in results]
    print(f"Foram obtidas {len(rows)} linhas do BigQuery")

    # Converte os dicionários em objetos Chat
    chats = []
    errors = 0
    for item in rows:
        try:
            # Etapa de anonimização antes da validação
            anonymized_item = _anonymize_chat_data(item)
            chat = Chat(**anonymized_item)
            chats.append(chat)
        except Exception as e:
            errors += 1
            if errors <= 5:  # Imprime apenas os 5 primeiros erros para não poluir o log
                print(f"Erro ao processar o chat {item.get('id', 'desconhecido')}: {e}")

    if errors > 5:
        print(f"... e mais {errors - 5} erros de processamento")

    print(f"Foram processados {len(chats)} chats com sucesso")
    return chats


def get_data_source() -> str:
    """
    Retorna o tipo de fonte de dados configurada.

    Returns:
        "bigquery" se as variáveis de ambiente do BigQuery estiverem configuradas,
        "json" caso contrário.
    """
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET")
    table = os.getenv("BIGQUERY_TABLE")

    if all([project_id, dataset, table]):
        return "bigquery"
    return "json"
