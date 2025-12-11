from datetime import datetime

import pytest
import pytz

from src.llm_analysis import LLMAnalyzer
from src.models import Chat, Message, MessageSender


@pytest.fixture
def sample_chat_for_llm():
    return Chat(
        id="chat_llm",
        number="123",
        channel="whatsapp",
        contact={"id": "c1", "name": "Customer"},
        messages=[
            Message(
                id="m1",
                body="Qual o preço do Ultrassom?",
                time=datetime(2023, 10, 16, 14, 0, 0, tzinfo=pytz.UTC),
                type="public",
                chatId="chat_llm",
                sentBy=MessageSender(id="c1", type="contact"),
            )
        ],
        status="open",
    )


@pytest.mark.asyncio
async def test_analyze_chat_structure(sample_chat_for_llm):
    analyzer = LLMAnalyzer()
    result = await analyzer.analyze_chat(sample_chat_for_llm)

    # Check top-level keys
    assert "cx" in result
    assert "product" in result
    assert "sales" in result
    assert "qa" in result

    # Check CX fields
    assert "nps_prediction" in result["cx"]
    assert "humanization_score" in result["cx"]

    # Check Sales fields
    assert "funnel_stage" in result["sales"]

    # Check QA fields
    assert "script_adherence" in result["qa"]
    assert isinstance(result["qa"]["key_questions_asked"], list)
