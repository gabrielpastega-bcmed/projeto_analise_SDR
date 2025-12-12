from datetime import datetime

import pytest
import pytz

from src.models import Agent, Chat, Message, MessageSender
from src.ops_analysis import (
    analyze_agent_performance,
    analyze_heatmap,
    analyze_tags,
)


# Mock de dados para os testes de heatmap e tags
@pytest.fixture
def sample_chats_for_metrics():
    return [
        Chat(
            id="chat1",
            number="123",
            channel="whatsapp",
            contact={"id": "c1", "name": "Customer 1"},
            tags=[{"id": "t1", "name": "Sale"}, {"id": "t2", "name": "Hot"}],
            messages=[
                Message(
                    id="m1",
                    body="Msg 1",
                    time=datetime(2023, 10, 16, 14, 0, 0, tzinfo=pytz.UTC),  # Seg 11:00 BRT
                    type="public",
                    chatId="chat1",
                    sentBy=MessageSender(id="c1", type="contact"),
                )
            ],
            status="closed",
        ),
        Chat(
            id="chat2",
            number="456",
            channel="whatsapp",
            contact={"id": "c2", "name": "Customer 2"},
            tags=[{"id": "t1", "name": "Sale"}],
            messages=[
                Message(
                    id="m2",
                    body="Msg 2",
                    time=datetime(2023, 10, 16, 15, 0, 0, tzinfo=pytz.UTC),  # Seg 12:00 BRT
                    type="public",
                    chatId="chat2",
                    sentBy=MessageSender(id="c2", type="contact"),
                )
            ],
            status="closed",
        ),
    ]


# Mock de dados mais detalhado para o teste de performance de agente
@pytest.fixture
def chat_for_agent_performance():
    agent = Agent(id="a1", name="Agent Smith", email="agent@bcmed.com.br")
    return [
        Chat(
            id="chat-perf",
            number="789",
            channel="web",
            contact={"id": "c3", "name": "Performance Customer"},
            agent=agent,
            tags=[],
            messages=[
                # 1. Cliente envia msg às 10:00 (horário comercial)
                Message(
                    id="m1",
                    body="Oi",
                    time=datetime(2023, 10, 16, 13, 0, 0, tzinfo=pytz.UTC),  # Seg 10:00 BRT
                    type="text",
                    chatId="chat-perf",
                    sentBy=MessageSender(id="c3", type="contact"),
                ),
                # 2. Agente responde após 5 minutos (TME = 300s)
                Message(
                    id="m2",
                    body="Olá!",
                    time=datetime(2023, 10, 16, 13, 5, 0, tzinfo=pytz.UTC),  # Seg 10:05 BRT
                    type="text",
                    chatId="chat-perf",
                    sentBy=MessageSender(id="a1", type="agent", email=agent.email),
                ),
                # 3. Cliente envia msg às 18:05 (fora do horário comercial)
                Message(
                    id="m3",
                    body="Preciso de ajuda.",
                    time=datetime(2023, 10, 16, 21, 5, 0, tzinfo=pytz.UTC),  # Seg 18:05 BRT
                    type="text",
                    chatId="chat-perf",
                    sentBy=MessageSender(id="c3", type="contact"),
                ),
                # 4. Agente responde no dia seguinte às 08:00 (TME não deve ser contado)
                Message(
                    id="m4",
                    body="Com certeza.",
                    time=datetime(2023, 10, 17, 11, 0, 0, tzinfo=pytz.UTC),  # Ter 08:00 BRT
                    type="text",
                    chatId="chat-perf",
                    sentBy=MessageSender(id="a1", type="agent", email=agent.email),
                ),
            ],
            status="closed",
        )
    ]


def test_analyze_agent_performance(chat_for_agent_performance):
    """
    Testa o cálculo de TME e TMA após a refatoração com pandas.
    """
    results = analyze_agent_performance(chat_for_agent_performance)

    assert len(results) == 1
    agent_perf = results[0]

    assert agent_perf["agent"] == "Agent Smith"
    assert agent_perf["chats"] == 1

    # O TME é a média de todas as respostas dadas em horário comercial.
    # Resposta 1: 5 minutos = 300s.
    # Resposta 2: O agente responde no dia seguinte às 08:00 (horário comercial).
    # O tempo de espera foi de 13h 55m = 50100s.
    # TME médio = (300 + 50100) / 2 = 25200s.
    assert agent_perf["avg_tme_seconds"] == pytest.approx(25200.0)

    # TMA é o tempo total do chat (Ter 08:00 BRT - Seg 10:00 BRT).
    tma_expected = (
        datetime(2023, 10, 17, 11, 0, 0, tzinfo=pytz.UTC) - datetime(2023, 10, 16, 13, 0, 0, tzinfo=pytz.UTC)
    ).total_seconds()
    assert agent_perf["avg_tma_seconds"] == pytest.approx(tma_expected)


def test_analyze_heatmap(sample_chats_for_metrics):
    heatmap = analyze_heatmap(sample_chats_for_metrics)

    # Verifica a estrutura
    assert "0" in heatmap  # Segunda-feira
    assert len(heatmap) == 7

    # Seg 11:00 BRT (14:00 UTC) -> 1 msg
    assert heatmap["0"][11] == 1
    # Seg 12:00 BRT (15:00 UTC) -> 1 msg
    assert heatmap["0"][12] == 1
    # Outras horas vazias
    assert heatmap["0"][10] == 0


def test_analyze_tags(sample_chats_for_metrics):
    tags = analyze_tags(sample_chats_for_metrics)

    assert tags["Sale"] == 2
    assert tags["Hot"] == 1
    assert "Unknown" not in tags
