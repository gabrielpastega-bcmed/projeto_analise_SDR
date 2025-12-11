from datetime import datetime

import pytest
import pytz

from src.models import Chat, Message, MessageSender
from src.ops_analysis import analyze_heatmap, analyze_tags


# Mock Data
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
                    time=datetime(2023, 10, 16, 14, 0, 0, tzinfo=pytz.UTC),  # Mon 11:00 BRT
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
                    time=datetime(2023, 10, 16, 15, 0, 0, tzinfo=pytz.UTC),  # Mon 12:00 BRT
                    type="public",
                    chatId="chat2",
                    sentBy=MessageSender(id="c2", type="contact"),
                )
            ],
            status="closed",
        ),
    ]


def test_analyze_heatmap(sample_chats_for_metrics):
    heatmap = analyze_heatmap(sample_chats_for_metrics)

    # Check structure
    assert "0" in heatmap  # Monday
    assert len(heatmap) == 7

    # Mon 11:00 BRT (14:00 UTC) -> 1 msg
    assert heatmap["0"][11] == 1
    # Mon 12:00 BRT (15:00 UTC) -> 1 msg
    assert heatmap["0"][12] == 1
    # Other hours empty
    assert heatmap["0"][10] == 0


def test_analyze_tags(sample_chats_for_metrics):
    tags = analyze_tags(sample_chats_for_metrics)

    assert tags["Sale"] == 2
    assert tags["Hot"] == 1
    assert "Unknown" not in tags
