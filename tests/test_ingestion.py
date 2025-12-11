"""
Testes para o módulo de ingestão de dados.
"""
import json
from unittest.mock import mock_open, patch

import pytest

from src.ingestion import _anonymize_text, load_chats_from_json


@pytest.mark.parametrize(
    "original, expected",
    [
        ("Fale com joao@example.com", "Fale com [EMAIL]"),
        ("Meu telefone é (11) 99999-8888", "Meu telefone é [TELEFONE]"),
        ("CPF: 123.456.789-00", "CPF: [CPF]"),
        ("Texto sem PII.", "Texto sem PII."),
    ],
)
def test_anonymize_text(original, expected):
    """
    Testa a função de anonimização de texto para vários padrões de PII.
    """
    assert _anonymize_text(original) == expected


def test_load_chats_from_json_anonymization():
    """
    Testa se a função `load_chats_from_json` aplica a anonimização corretamente.
    """
    # Mock de um arquivo JSON com dados sensíveis
    mock_data = [
        {
            "id": "chat1",
            "number": "1",
            "channel": "web",
            "contact": {"id": "c1", "name": "Maria Silva", "email": "maria@email.com"},
            "messages": [
                {
                    "id": "m1",
                    "body": "Olá, meu CPF é 111.222.333-44.",
                    "time": "2023-01-01T12:00:00Z",
                    "type": "text",
                    "chatId": "chat1",
                }
            ],
            "status": "closed",
        }
    ]
    mock_file_content = json.dumps(mock_data)

    # Usa o `patch` para simular a leitura do arquivo
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        chats = load_chats_from_json("dummy/path/to/file.json")

    assert len(chats) == 1
    chat = chats[0]

    # Verifica se os dados foram anonimizados
    assert chat.contact.name == "[CONTATO]"
    assert chat.contact.email == "[EMAIL]"
    assert chat.messages[0].body == "Olá, meu CPF é [CPF]."
