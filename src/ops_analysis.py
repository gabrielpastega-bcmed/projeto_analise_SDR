"""
Módulo para análise de métricas operacionais a partir de dados de chat.

Este módulo foi refatorado para usar a biblioteca `pandas` para otimização de
desempenho, permitindo a análise eficiente de grandes volumes de dados.
Ele calcula:
- Tempo Médio de Espera (TME)
- Tempo Médio de Atendimento (TMA)
- Desempenho de agentes
- Volume de mensagens (heatmap)
- Frequência de tags
"""

from datetime import time
from typing import Dict, List, Tuple, TypedDict

import pandas as pd
import pytz

from src.models import Chat


class AgentPerformance(TypedDict):
    """
    Define a estrutura de dados para o dicionário de desempenho do agente.
    """

    agent: str
    chats: int
    avg_tme_seconds: float
    avg_tma_seconds: float


# Define o fuso horário para conversões
TZ = pytz.timezone("America/Sao_Paulo")


def _prepare_dataframes(chats: List[Chat]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Converte uma lista de objetos Chat em DataFrames otimizados para análise.

    Args:
        chats: A lista de objetos Chat.

    Returns:
        Uma tupla contendo dois DataFrames: (chats_df, messages_df).
    """
    # Transforma os chats em um DataFrame
    chats_data = [
        {
            "chat_id": chat.id,
            "agent_name": chat.agent.name if chat.agent else "Sem Agente",
            "tags": [tag["name"] for tag in chat.tags] if chat.tags else [],
        }
        for chat in chats
    ]
    chats_df = pd.DataFrame(chats_data)

    # Transforma as mensagens em um DataFrame
    messages_data = [
        {
            "chat_id": msg.chatId,
            "timestamp": msg.time,
            "is_agent": (msg.sentBy and msg.sentBy.type == "agent")
            or (msg.sentBy and msg.sentBy.email and "company.exemplo.com" in msg.sentBy.email),
        }
        for chat in chats
        for msg in chat.messages
    ]
    messages_df = pd.DataFrame(messages_data)
    # Converte a coluna de timestamp para datetime com fuso horário UTC
    messages_df["timestamp"] = pd.to_datetime(messages_df["timestamp"], utc=True)

    return chats_df, messages_df


def _calculate_metrics_in_batches(messages_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula TME e TMA de forma vetorizada usando pandas.
    """
    if messages_df.empty:
        return pd.DataFrame(columns=["chat_id", "tme_seconds", "tma_seconds", "response_count"])

    # Ordena as mensagens por chat e tempo
    messages_df = messages_df.sort_values(by=["chat_id", "timestamp"])

    # Identifica o remetente da mensagem anterior, preenchendo NA com False
    # Isso corrige o bug onde a primeira mensagem era ignorada na comparação.
    messages_df["prev_is_agent"] = messages_df.groupby("chat_id")["is_agent"].shift(1).fillna(False)
    messages_df["prev_timestamp"] = messages_df.groupby("chat_id")["timestamp"].shift(1)

    # Filtra apenas as respostas do agente a mensagens do cliente
    agent_responses = messages_df[messages_df["is_agent"] & ~messages_df["prev_is_agent"]].copy()

    # --- Cálculo do TME (Tempo Médio de Espera) ---
    # Converte o timestamp para o fuso horário local
    agent_responses["local_time"] = agent_responses["timestamp"].dt.tz_convert(TZ)
    dt = agent_responses["local_time"].dt

    # Verifica se a resposta está dentro do horário comercial
    is_weekday = dt.weekday < 5
    is_friday = dt.weekday == 4
    is_work_hour_mon_thu = (dt.time >= time(8, 0)) & (dt.time <= time(18, 0)) & ~is_friday
    is_work_hour_fri = (dt.time >= time(8, 0)) & (dt.time <= time(17, 0)) & is_friday

    agent_responses["is_business_hour"] = is_weekday & (is_work_hour_mon_thu | is_work_hour_fri)
    responses_in_business_hours = agent_responses[agent_responses["is_business_hour"]].copy()

    # Calcula a diferença de tempo em segundos
    responses_in_business_hours["wait_time"] = (
        responses_in_business_hours["timestamp"] - responses_in_business_hours["prev_timestamp"]
    ).dt.total_seconds()

    # Agrega o tempo de espera e a contagem de respostas por chat
    tme_stats = (
        responses_in_business_hours.groupby("chat_id")
        .agg(total_wait_time=("wait_time", "sum"), response_count=("wait_time", "size"))
        .reset_index()
    )
    tme_stats["tme_seconds"] = tme_stats["total_wait_time"] / tme_stats["response_count"]

    # --- Cálculo do TMA (Tempo Médio de Atendimento) ---
    chat_durations = messages_df.groupby("chat_id")["timestamp"].agg(["min", "max"])
    chat_durations["tma_seconds"] = (chat_durations["max"] - chat_durations["min"]).dt.total_seconds()
    tma_stats = chat_durations[["tma_seconds"]].reset_index()

    # Combina as métricas de TME e TMA
    final_metrics = pd.merge(tma_stats, tme_stats, on="chat_id", how="left").fillna(0)

    return final_metrics[["chat_id", "tme_seconds", "tma_seconds", "response_count"]]


def analyze_agent_performance(chats: List[Chat]) -> List[AgentPerformance]:
    """
    Agrega as métricas de desempenho por agente de forma otimizada.

    Args:
        chats: Uma lista de objetos Chat.

    Returns:
        Uma lista de dicionários AgentPerformance, ordenada pelo TME mais rápido.
    """
    chats_df, messages_df = _prepare_dataframes(chats)
    if chats_df.empty or messages_df.empty:
        return []

    # Calcula as métricas por chat
    metrics_df = _calculate_metrics_in_batches(messages_df)

    # Junta as métricas com as informações do agente
    agent_data = pd.merge(chats_df, metrics_df, on="chat_id", how="left").fillna(0)

    # Agrega as estatísticas por agente
    agent_summary = (
        agent_data.groupby("agent_name")
        .agg(
            chats=("chat_id", "count"),
            total_tme_weighted=("tme_seconds", lambda x: (x * agent_data.loc[x.index, "response_count"]).sum()),
            total_tma=("tma_seconds", "sum"),
            total_responses=("response_count", "sum"),
        )
        .reset_index()
    )

    # Calcula as médias
    agent_summary["avg_tme_seconds"] = (agent_summary["total_tme_weighted"] / agent_summary["total_responses"]).fillna(
        0
    )
    agent_summary["avg_tma_seconds"] = (agent_summary["total_tma"] / agent_summary["chats"]).fillna(0)

    # Formata a saída
    agent_summary = agent_summary.rename(columns={"agent_name": "agent"})
    results = agent_summary[["agent", "chats", "avg_tme_seconds", "avg_tma_seconds"]].to_dict(orient="records")

    # Ordena por TME
    return sorted(results, key=lambda x: x["avg_tme_seconds"])


def analyze_heatmap(chats: List[Chat]) -> Dict[str, Dict[int, int]]:
    """
    Gera um mapa de calor do volume de mensagens por dia da semana e hora.
    """
    _, messages_df = _prepare_dataframes(chats)
    if messages_df.empty:
        return {}

    messages_df["local_time"] = messages_df["timestamp"].dt.tz_convert(TZ)
    messages_df["weekday"] = messages_df["local_time"].dt.weekday.astype(str)
    messages_df["hour"] = messages_df["local_time"].dt.hour

    heatmap_data = messages_df.groupby(["weekday", "hour"]).size().unstack(fill_value=0)

    # Garante que todos os dias e horas estejam presentes
    heatmap_full = pd.DataFrame(0, index=map(str, range(7)), columns=range(24))
    heatmap_full.update(heatmap_data)

    return heatmap_full.to_dict(orient="index")


def analyze_tags(chats: List[Chat]) -> Dict[str, int]:
    """
    Conta a frequência de cada tag nos chats.
    """
    chats_df, _ = _prepare_dataframes(chats)
    if chats_df.empty:
        return {}

    # "Explode" a lista de tags em linhas individuais e conta a frequência
    tag_counts = chats_df.explode("tags")["tags"].value_counts().to_dict()

    return tag_counts
