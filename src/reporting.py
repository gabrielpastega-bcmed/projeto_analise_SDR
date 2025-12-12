"""
Módulo para agregação e geração de relatórios consolidados.

Este módulo recebe os dados processados das análises operacional e qualitativa
e os consolida em um relatório final estruturado.
"""

from collections import Counter
from typing import Any, Dict, List


def generate_report(chats_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Agrega os resultados do pipeline de análise em um relatório consolidado.

    A entrada `chats_data` é uma lista de dicionários, onde cada dicionário
    representa uma conversa analisada e contém as seguintes chaves:
    - 'chat_id': ID da conversa.
    - 'agent_name': Nome do agente.
    - 'ops_metrics': Dicionário com métricas operacionais (tme, tma).
    - 'llm_results': Dicionário com os resultados da análise do LLM (cx, product, sales).

    Args:
        chats_data: Lista de dados de conversas analisadas.

    Returns:
        Um dicionário contendo o relatório com as seções:
        - 'agent_ranking': Desempenho dos agentes.
        - 'product_cloud': Produtos mais mencionados.
        - 'sales_funnel': Resumo do funil de vendas.
        - 'loss_reasons': Motivos de perda mais comuns.
    """

    # --- 1. Ranking de Agentes ---
    agent_stats: Dict[str, Dict[str, Any]] = {}
    for item in chats_data:
        agent = item["agent_name"]
        if not agent:
            continue

        # Inicializa o dicionário para um novo agente
        if agent not in agent_stats:
            agent_stats[agent] = {"count": 0, "total_tme": 0, "total_tma": 0, "humanization_sum": 0}

        # Acumula as estatísticas
        stats = agent_stats[agent]
        stats["count"] += 1
        stats["total_tme"] += item["ops_metrics"]["tme_seconds"]
        stats["total_tma"] += item["ops_metrics"]["tma_seconds"]
        stats["humanization_sum"] += item["llm_results"]["cx"]["humanization_score"]

    # Calcula as médias e formata a saída
    ranking = []
    for agent, stats in agent_stats.items():
        count = stats["count"]
        ranking.append(
            {
                "agent": agent,
                "chats": count,
                "avg_tme": stats["total_tme"] / count if count > 0 else 0,
                "avg_tma": stats["total_tma"] / count if count > 0 else 0,
                "avg_humanization": stats["humanization_sum"] / count if count > 0 else 0,
            }
        )
    # Ordena o ranking pelo menor TME (mais rápido)
    ranking.sort(key=lambda x: x["avg_tme"])

    # --- 2. "Top of Mind" de Produtos ---
    all_products = []
    for item in chats_data:
        products = item["llm_results"]["product"].get("products_mentioned", [])
        all_products.extend(products)

    # Conta e extrai os 10 produtos mais comuns
    top_products = Counter(all_products).most_common(10)

    # --- 3. Funil de Vendas e Motivos de Perda ---
    # Contagem dos resultados das conversas (convertido, perdido, etc.)
    outcomes = Counter(item["llm_results"]["sales"]["outcome"] for item in chats_data)

    # Contagem dos motivos de perda, apenas para os resultados "perdido"
    loss_reasons = Counter(
        item["llm_results"]["sales"]["rejection_reason"]
        for item in chats_data
        if item["llm_results"]["sales"]["outcome"] == "lost" and item["llm_results"]["sales"]["rejection_reason"]
    )

    # --- 4. Montagem do Relatório Final ---
    return {
        "agent_ranking": ranking,
        "product_cloud": top_products,
        "sales_funnel": dict(outcomes),
        "loss_reasons": dict(loss_reasons),
    }
