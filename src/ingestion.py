import json
from typing import List

from src.models import Chat


def load_chats_from_json(file_path: str) -> List[Chat]:
    """
    Loads chats from a JSON file and parses them into Chat objects.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chats = []
    for item in data:
        try:
            chat = Chat(**item)
            chats.append(chat)
        except Exception as e:
            print(f"Error parsing chat {item.get('id', 'unknown')}: {e}")
            # In production, we might want to log this to a file or skip silently
            continue

    return chats
