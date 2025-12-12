"""
Módulo de ingestão de dados para carregar conversas de diversas fontes.
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, List, MutableMapping, Optional

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


def load_chats_from_bigquery(
    days: Optional[int] = None,
    limit: Optional[int] = None,
    lightweight: bool = True,
) -> List[Chat]:
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
        lightweight: Se True, exclui o campo 'messages' para carregamento mais rápido.

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
    # Modo lightweight exclui o campo 'messages' que é o mais pesado
    if lightweight:
        # Campos essenciais para dashboard (sem messages)
        fields = """
            id, number, channel, contact, agent, pastAgents,
            firstMessageDate, lastMessageDate, messagesCount,
            status, closed, waitingTime, tags,
            withBot, unreadMessages, octavia_analysis
        """
        # Criar lista vazia de mensagens para o modelo
        query = f"""
        SELECT
            {fields}
        FROM `{project_id}.{dataset}.{table}`
        WHERE DATE(firstMessageDate) >= @start_date
        ORDER BY firstMessageDate DESC
        """
    else:
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

    # Adiciona o limite à query, se especificado (default: 5000 para performance)
    effective_limit = limit if limit else 5000
    query += f"\nLIMIT {effective_limit}"

    print(f"Consultando o BigQuery: {project_id}.{dataset}.{table}")
    print(f"Filtro de data: >= {start_date_str} ({analysis_days} dias)")
    print(f"Modo: {'Lightweight (sem mensagens)' if lightweight else 'Completo'}")
    print(f"Limite: {effective_limit} chats")

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
            # Em modo lightweight, adicionar lista vazia de mensagens
            if lightweight and "messages" not in item:
                item["messages"] = []

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


def load_aggregated_metrics_from_bigquery(days: Optional[int] = None) -> dict:
    """
    Carrega métricas agregadas diretamente do BigQuery (mais rápido).

    Retorna estatísticas pré-calculadas sem precisar carregar todos os chats.
    """
    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset = os.getenv("BIGQUERY_DATASET")
    table = os.getenv("BIGQUERY_TABLE")
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    default_days = int(os.getenv("ANALYSIS_DAYS", "7"))

    if not all([project_id, dataset, table]):
        return {}

    if credentials_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

    client = bigquery.Client(project=project_id)

    analysis_days = days if days is not None else default_days
    start_date = datetime.now() - timedelta(days=analysis_days)
    start_date_str = start_date.strftime("%Y-%m-%d")

    query = f"""
    SELECT
        COUNT(*) as total_chats,
        AVG(waitingTime) as avg_waiting_time,
        AVG(messagesCount) as avg_messages,
        COUNTIF(withBot = 'true') as with_bot_count,
        COUNT(DISTINCT JSON_EXTRACT_SCALAR(agent, '$.name')) as unique_agents
    FROM `{project_id}.{dataset}.{table}`
    WHERE DATE(firstMessageDate) >= @start_date
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_date", "STRING", start_date_str),
        ]
    )

    try:
        result = list(client.query(query, job_config=job_config).result())[0]
        return {
            "total_chats": result.total_chats or 0,
            "avg_waiting_time": result.avg_waiting_time or 0,
            "avg_messages": result.avg_messages or 0,
            "with_bot_count": result.with_bot_count or 0,
            "unique_agents": result.unique_agents or 0,
        }
    except Exception as e:
        print(f"Erro ao carregar métricas agregadas: {e}")
        return {}


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
