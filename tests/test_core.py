from datetime import datetime

import pytest
import pytz

from src.models import Chat, Message, MessageSender
from src.ops_analysis import calculate_response_times, is_business_hour


# Mock Data
@pytest.fixture
def sample_chat():
    return Chat(
        id="test-chat",
        number="123",
        channel="whatsapp",
        contact={"id": "c1", "name": "Customer"},
        agent={"id": "a1", "name": "Agent Smith", "email": "agent@empresa.com.br"},
        status="closed",
        messages=[
            Message(
                id="m1",
                body="Hi",
                time=datetime(2023, 10, 16, 14, 0, 0, tzinfo=pytz.UTC),
                type="public",
                chatId="test-chat",
                sentBy=MessageSender(id="c1", type="contact")
            ),
            Message(
                id="m2",
                body="Hello",
                time=datetime(2023, 10, 16, 14, 5, 0, tzinfo=pytz.UTC),
                type="public",
                chatId="test-chat",
                sentBy=MessageSender(id="a1", type="agent", email="agent@empresa.com.br")
            )
        ]
    )

def test_chat_model_parsing(sample_chat):
    assert sample_chat.id == "test-chat"
    assert len(sample_chat.messages) == 2
    assert sample_chat.messages[0].body == "Hi"

def test_business_hours():
    # Monday 14:00 UTC -> 11:00 São Paulo (Business Hour: Mon 08:00-18:00)
    dt_bh = datetime(2023, 10, 16, 14, 0, 0, tzinfo=pytz.UTC)
    assert is_business_hour(dt_bh) == True

    # Sunday 14:00 UTC -> 11:00 São Paulo (NOT Business Hour: Weekend)
    dt_weekend = datetime(2023, 10, 15, 14, 0, 0, tzinfo=pytz.UTC)
    assert is_business_hour(dt_weekend) == False

    # Monday 20:00 UTC -> 17:00 São Paulo (Business Hour: Mon ends at 18:00!)
    # This was previously expected to be False, but 17:00 is still within 08:00-18:00
    dt_5pm = datetime(2023, 10, 16, 20, 0, 0, tzinfo=pytz.UTC)
    assert is_business_hour(dt_5pm) == True  # FIXED: 17:00 < 18:00

    # Monday 22:00 UTC -> 19:00 São Paulo (NOT Business Hour: after 18:00)
    dt_night = datetime(2023, 10, 16, 22, 0, 0, tzinfo=pytz.UTC)
    assert is_business_hour(dt_night) == False

def test_response_time_calculation(sample_chat):
    metrics = calculate_response_times(sample_chat)

    # Wait time: 14:00 to 14:05 = 5 minutes = 300 seconds
    assert metrics['tme_seconds'] == 300.0
    assert metrics['response_count'] == 1
    assert metrics['tma_seconds'] == 300.0
