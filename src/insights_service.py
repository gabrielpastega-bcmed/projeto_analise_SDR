"""
Serviço de Insights: Lógica de negócios extraída de 5_Insights.py.

Este módulo contém funções para:
- Carregar semanas disponíveis do BigQuery
- Agregar resultados de análises
- Formatar transcrições de chat
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.logging_config import get_logger

logger = get_logger(__name__)


def load_available_weeks() -> List[Dict[str, Any]]:
    """
    Carrega as semanas disponíveis do BigQuery.

    Returns:
        Lista de dicts com week_start, week_end, total_chats, total_agents.
    """
    try:
        from src.batch_analyzer import BatchAnalyzer

        analyzer = BatchAnalyzer()
        weeks = analyzer.get_available_weeks()
        logger.info(f"Carregadas {len(weeks)} semanas disponiveis")
        return weeks
    except Exception as e:
        logger.error(f"Erro ao carregar semanas: {e}")
        return []


def load_week_results(week_start: datetime) -> List[Dict[str, Any]]:
    """
    Carrega resultados de uma semana específica do BigQuery.

    Args:
        week_start: Data de início da semana.

    Returns:
        Lista de resultados da análise.
    """
    try:
        from src.batch_analyzer import BatchAnalyzer

        analyzer = BatchAnalyzer()
        results = analyzer.load_from_bigquery(week_start)
        logger.info(f"Carregados {len(results)} resultados para semana {week_start}")
        return results
    except Exception as e:
        logger.error(f"Erro ao carregar resultados: {e}")
        return []


def load_local_analysis(file_path: Path) -> Optional[List[Dict[str, Any]]]:
    """
    Carrega análise de arquivo JSON local.

    Args:
        file_path: Caminho para o arquivo JSON.

    Returns:
        Lista de resultados ou None se erro.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            results = json.load(f)
        logger.info(f"Carregados {len(results)} resultados de {file_path.name}")
        return results
    except Exception as e:
        logger.error(f"Erro ao carregar arquivo local: {e}")
        return None


def aggregate_bigquery_results(results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Agrega resultados do BigQuery para exibição no dashboard.

    Args:
        results: Lista de resultados do BigQuery.

    Returns:
        Dicionário com métricas agregadas.
    """
    if not results:
        return None

    total = len(results)

    # Sentimentos
    sentiments = {"positivo": 0, "neutro": 0, "negativo": 0}
    for r in results:
        s = r.get("cx_sentiment", "neutro")
        if s in sentiments:
            sentiments[s] += 1

    # NPS e Humanização - filter None values explicitly
    nps_scores: List[Any] = [r.get("cx_nps_prediction") for r in results if r.get("cx_nps_prediction") is not None]
    humanization: List[Any] = [
        r.get("cx_humanization_score") for r in results if r.get("cx_humanization_score") is not None
    ]

    # Outcomes
    outcomes = {"convertido": 0, "perdido": 0, "em andamento": 0}
    for r in results:
        o = r.get("sales_outcome", "em andamento")
        if o in outcomes:
            outcomes[o] += 1

    # Produtos
    all_products: List[str] = []
    for r in results:
        prods = r.get("products_mentioned") or []
        all_products.extend(prods)

    product_counts: Dict[str, int] = {}
    for p in all_products:
        product_counts[p] = product_counts.get(p, 0) + 1
    top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_analyzed": total,
        "cx": {
            "sentiment_distribution": sentiments,
            "avg_nps_prediction": sum(nps_scores) / len(nps_scores) if nps_scores else 0,
            "avg_humanization_score": sum(humanization) / len(humanization) if humanization else 0,
        },
        "sales": {
            "outcome_distribution": outcomes,
            "conversion_rate": outcomes["convertido"] / total * 100 if total else 0,
        },
        "product": {
            "top_products": top_products,
        },
    }


def aggregate_local_results(results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Agrega resultados de análises locais (formato aninhado ou direto).

    Args:
        results: Lista de resultados locais.

    Returns:
        Dicionário com métricas agregadas.
    """
    if not results:
        return None

    total = len(results)

    # Sentimentos
    sentiments = {"positivo": 0, "neutro": 0, "negativo": 0}
    nps_scores = []
    humanization_scores = []
    outcomes = {"convertido": 0, "perdido": 0, "em andamento": 0}

    for r in results:
        # Suporta formato aninhado { analysis: { cx, sales } } ou direto { cx, sales }
        analysis = r.get("analysis", r)
        cx = analysis.get("cx", r.get("cx", {}))
        sales = analysis.get("sales", r.get("sales", {}))

        # CX
        s = cx.get("sentiment") or r.get("cx_sentiment", "neutro")
        if s and s.lower() in sentiments:
            sentiments[s.lower()] += 1

        nps = cx.get("nps_prediction") or r.get("cx_nps_prediction")
        if nps:
            nps_scores.append(float(nps))

        hum = cx.get("humanization_score") or r.get("cx_humanization_score")
        if hum:
            humanization_scores.append(float(hum))

        # Sales
        o = sales.get("outcome") or r.get("sales_outcome", "em andamento")
        if o and o.lower() in outcomes:
            outcomes[o.lower()] += 1

    return {
        "total_analyzed": total,
        "cx": {
            "sentiment_distribution": sentiments,
            "avg_nps_prediction": sum(nps_scores) / len(nps_scores) if nps_scores else 0,
            "avg_humanization_score": (
                sum(humanization_scores) / len(humanization_scores) if humanization_scores else 0
            ),
        },
        "sales": {
            "outcome_distribution": outcomes,
            "conversion_rate": outcomes["convertido"] / total * 100 if total else 0,
        },
    }


def format_chat_transcript(chat, include_timestamps: bool = True) -> str:
    """
    Formata as mensagens de um chat em uma transcrição legível.

    Args:
        chat: Objeto Chat com mensagens.
        include_timestamps: Se True, inclui horários e deltas de tempo.

    Returns:
        String com a transcrição formatada.
    """
    import re

    messages_text = []
    last_time = None

    for msg in chat.messages or []:
        # Determinar tipo de remetente
        sender_type = msg.sentBy.type if msg.sentBy else None
        sender_name = msg.sentBy.name if msg.sentBy and msg.sentBy.name else ""

        if sender_type == "bot":
            sender = "Bot"
        elif sender_type == "agent":
            sender = sender_name if sender_name else "Agente"
        else:
            sender = sender_name if sender_name else "Cliente"

        # Formatar horário
        time_str = msg.time.strftime("%H:%M") if msg.time and include_timestamps else ""

        # Calcular tempo desde a última mensagem
        time_diff = ""
        if include_timestamps and last_time and msg.time:
            diff_seconds = (msg.time - last_time).total_seconds()
            if diff_seconds >= 60:
                diff_minutes = int(diff_seconds // 60)
                time_diff = f" (+{diff_minutes}min)"
        last_time = msg.time

        # Limpar HTML do body
        clean_body = re.sub(r"<[^>]+>", "", msg.body) if msg.body else ""

        if include_timestamps:
            messages_text.append(f"[{time_str}] [{sender}]{time_diff}: {clean_body}")
        else:
            messages_text.append(f"{sender}: {clean_body}")

    return "\n\n".join(messages_text)


def list_local_analysis_files(results_dir: str = "data/analysis_results", limit: int = 10) -> List[Path]:
    """
    Lista arquivos de análise disponíveis localmente.

    Args:
        results_dir: Diretório com arquivos de análise.
        limit: Número máximo de arquivos a retornar.

    Returns:
        Lista de Paths ordenada por data (mais recente primeiro).
    """
    path = Path(results_dir)
    if not path.exists():
        return []

    json_files = sorted(path.glob("analysis_*.json"), reverse=True)
    return json_files[:limit]
