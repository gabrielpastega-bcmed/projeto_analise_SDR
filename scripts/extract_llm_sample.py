"""
Extrai 500 chats aleatorios dos ultimos 60 dias para refinamento da LLM.
Uso unico - salva em data/raw/llm_training_sample.json
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion import load_chats_from_bigquery


def extract_sample(days: int = 60, limit: int = 500, output_path: str = "data/raw/llm_training_sample.json"):
    """Extrai amostra de chats e salva localmente."""
    print("\n" + "=" * 60)
    print("EXTRACAO DE AMOSTRA PARA REFINAMENTO LLM")
    print("=" * 60)
    print(f"  Periodo: ultimos {days} dias")
    print(f"  Quantidade: {limit} chats")
    print(f"  Destino: {output_path}")
    print("=" * 60)

    # Carregar chats completos (com mensagens para analise LLM)
    print("\n[1/3] Carregando chats do BigQuery...")
    chats = load_chats_from_bigquery(days=days, limit=limit, lightweight=False)
    print(f"      {len(chats)} chats carregados")

    # Converter para dict serializavel
    print("\n[2/3] Convertendo para JSON...")
    chats_data = []
    for chat in chats:
        try:
            chat_dict = chat.model_dump(mode="json")
            chats_data.append(chat_dict)
        except Exception as e:
            print(f"      [WARN] Erro ao converter chat {chat.id}: {e}")

    # Salvar arquivo
    print(f"\n[3/3] Salvando em {output_path}...")
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chats_data, f, ensure_ascii=False, indent=2, default=str)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)

    print("\n" + "=" * 60)
    print("EXTRACAO CONCLUIDA")
    print("=" * 60)
    print(f"  Chats salvos: {len(chats_data)}")
    print(f"  Tamanho: {file_size_mb:.2f} MB")
    print(f"  Arquivo: {output_file.absolute()}")
    print(f"  Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    return output_file


if __name__ == "__main__":
    extract_sample()
