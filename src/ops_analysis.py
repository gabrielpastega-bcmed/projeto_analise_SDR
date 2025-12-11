from datetime import datetime, time
from typing import Any, Dict, List, TypedDict

import pytz

from src.models import Chat


class AgentPerformance(TypedDict):
    agent: str
    chats: int
    avg_tme_seconds: float
    avg_tma_seconds: float


# Define timezone (assuming Sao Paulo based on user context)
TZ = pytz.timezone("America/Sao_Paulo")


def is_business_hour(dt: datetime) -> bool:
    """
    Checks if a datetime is within business hours:
    Mon-Thu: 08:00 - 18:00
    Fri: 08:00 - 17:00
    """
    # Ensure dt is timezone aware, convert to Sao Paulo if needed
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)

    dt_local = dt.astimezone(TZ)

    weekday = dt_local.weekday()  # 0=Mon, 6=Sun
    current_time = dt_local.time()

    if 0 <= weekday <= 3:  # Mon-Thu
        return time(8, 0) <= current_time <= time(18, 0)
    elif weekday == 4:  # Fri
        return time(8, 0) <= current_time <= time(17, 0)

    return False


def calculate_response_times(chat: Chat) -> Dict[str, Any]:
    """
    Calculates TME (Average Wait Time) and TMA (Handle Time) for a chat.
    Only considers business hours for TME.
    """
    messages = sorted(chat.messages, key=lambda m: m.time)
    if not messages:
        return {"tme_seconds": 0, "tma_seconds": 0, "response_count": 0}

    total_wait_time = 0.0
    response_count = 0
    last_customer_msg_time = None

    # TMA: Duration from first to last message
    start_time = messages[0].time
    end_time = messages[-1].time
    tma_seconds = (end_time - start_time).total_seconds()

    for msg in messages:
        # Identify sender type (heuristic based on email or type)
        is_agent = False
        if msg.sentBy and msg.sentBy.type == "agent":
            is_agent = True
        elif msg.sentBy and msg.sentBy.email and "bcmed.com.br" in msg.sentBy.email:
            is_agent = True

        if not is_agent:
            # Customer message
            last_customer_msg_time = msg.time
        elif last_customer_msg_time:
            # Agent response to a customer message
            if is_business_hour(msg.time):
                wait_seconds = (msg.time - last_customer_msg_time).total_seconds()
                total_wait_time += wait_seconds
                response_count += 1
                last_customer_msg_time = None  # Reset

    avg_wait_time = total_wait_time / response_count if response_count > 0 else 0

    return {"tme_seconds": avg_wait_time, "tma_seconds": tma_seconds, "response_count": response_count}


def analyze_agent_performance(chats: List[Chat]) -> List[AgentPerformance]:
    """
    Aggregates performance metrics by agent.
    """
    agent_stats: Dict[str, Dict[str, float]] = {}

    for chat in chats:
        if not chat.agent:
            continue

        agent_name = chat.agent.name
        metrics = calculate_response_times(chat)

        if agent_name not in agent_stats:
            agent_stats[agent_name] = {"chats": 0.0, "total_tme": 0.0, "total_tma": 0.0, "response_count": 0.0}

        agent_stats[agent_name]["chats"] += 1.0
        agent_stats[agent_name]["total_tme"] += metrics["tme_seconds"] * metrics["response_count"]
        agent_stats[agent_name]["total_tma"] += metrics["tma_seconds"]
        agent_stats[agent_name]["response_count"] += metrics["response_count"]

    # Calculate averages
    results: List[AgentPerformance] = []
    for name, stats in agent_stats.items():
        avg_tme = stats["total_tme"] / stats["response_count"] if stats["response_count"] > 0 else 0.0
        avg_tma = stats["total_tma"] / stats["chats"] if stats["chats"] > 0 else 0.0

        results.append(
            AgentPerformance(
                agent=name,
                chats=int(stats["chats"]),
                avg_tme_seconds=avg_tme,
                avg_tma_seconds=avg_tma,
            )
        )

    return sorted(results, key=lambda x: x["avg_tme_seconds"])  # Sort by fastest response
