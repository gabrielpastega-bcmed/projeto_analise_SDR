from collections import Counter
from typing import Any, Dict, List


def generate_report(chats_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates the results from the analysis pipeline.
    chats_data is a list of dicts containing:
    - chat_id
    - agent_name
    - ops_metrics (tme, tma)
    - llm_results (cx, product, sales)
    """

    # 1. Agent Ranking
    agent_stats = {}
    for item in chats_data:
        agent = item["agent_name"]
        if not agent:
            continue

        if agent not in agent_stats:
            agent_stats[agent] = {"count": 0, "total_tme": 0, "total_tma": 0, "humanization_sum": 0}

        stats = agent_stats[agent]
        stats["count"] += 1
        stats["total_tme"] += item["ops_metrics"]["tme_seconds"]
        stats["total_tma"] += item["ops_metrics"]["tma_seconds"]
        stats["humanization_sum"] += item["llm_results"]["cx"]["humanization_score"]

    ranking = []
    for agent, stats in agent_stats.items():
        ranking.append(
            {
                "agent": agent,
                "chats": stats["count"],
                "avg_tme": stats["total_tme"] / stats["count"],
                "avg_tma": stats["total_tma"] / stats["count"],
                "avg_humanization": stats["humanization_sum"] / stats["count"],
            }
        )
    ranking.sort(key=lambda x: x["avg_tme"])  # Sort by speed

    # 2. Product "Top of Mind"
    all_products = []
    for item in chats_data:
        products = item["llm_results"]["product"].get("products_mentioned", [])
        all_products.extend(products)

    top_products = Counter(all_products).most_common(10)

    # 3. Sales Funnel
    outcomes = Counter([item["llm_results"]["sales"]["outcome"] for item in chats_data])
    loss_reasons = Counter(
        [
            item["llm_results"]["sales"]["rejection_reason"]
            for item in chats_data
            if item["llm_results"]["sales"]["outcome"] == "lost"
        ]
    )

    return {
        "agent_ranking": ranking,
        "product_cloud": top_products,
        "sales_funnel": dict(outcomes),
        "loss_reasons": dict(loss_reasons),
    }
