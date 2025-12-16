"""
Script para testar os prompts refinados com chats de amostra.

Uso:
    python scripts/test_llm_prompts.py

Requer: GEMINI_API_KEY no .env
"""

import asyncio
import json
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.batch_analyzer import format_transcript
from src.gemini_client import GeminiClient
from src.ingestion import load_chats_from_json


async def test_single_chat(client: GeminiClient, chat, chat_idx: int):
    """Testa analise de um chat."""
    print(f"\n{'=' * 60}")
    print(f"Chat #{chat_idx + 1}: {chat.id}")
    print(f"Agente: {chat.agent.name if chat.agent else 'N/A'}")
    print(f"Mensagens: {len(chat.messages)}")
    print(f"{'=' * 60}")

    transcript = format_transcript(chat)
    if not transcript.strip():
        print("  [SKIP] Chat sem mensagens")
        return None

    # Remove emojis para evitar erro de encoding no Windows
    import re

    clean_transcript = re.sub(r"[^\x00-\x7F]+", "", transcript[:500])
    print("\nTranscricao (primeiros 500 chars):")
    print(clean_transcript)
    print("...")

    print("\n[Analisando com Gemini...]")
    try:
        result = await client.analyze_chat_full(transcript)

        print("\n--- RESULTADO CX ---")
        cx = result.get("cx", {})
        print(f"  Sentimento: {cx.get('sentiment')}")
        print(f"  Humanizacao: {cx.get('humanization_score')}/5")
        print(f"  NPS: {cx.get('nps_prediction')}/10")
        print(f"  Personalizacao: {cx.get('personalization_used')}")

        print("\n--- RESULTADO SALES ---")
        sales = result.get("sales", {})
        print(f"  Estagio: {sales.get('funnel_stage')}")
        print(f"  Outcome: {sales.get('outcome')}")
        print(f"  Tipo Lead: {sales.get('lead_type')}")
        print(f"  Urgencia: {sales.get('urgency')}")

        print("\n--- RESULTADO PRODUCT ---")
        product = result.get("product", {})
        print(f"  Categoria: {product.get('category')}")
        print(f"  Produtos: {product.get('products_mentioned')}")
        print(f"  Interesse: {product.get('interest_level')}")

        print("\n--- RESULTADO QA ---")
        qa = result.get("qa", {})
        print(f"  Aderencia: {qa.get('script_adherence')}")
        print(f"  Perguntas feitas: {qa.get('questions_asked')}")
        print(f"  Perguntas faltando: {qa.get('questions_missing')}")
        print(f"  Score: {qa.get('overall_score')}/5")

        return result

    except Exception as e:
        print(f"  [ERRO] {e}")
        return None


async def main():
    # Carregar chats de amostra
    sample_file = Path("data/raw/llm_training_sample.json")
    if not sample_file.exists():
        print(f"Arquivo nao encontrado: {sample_file}")
        return

    print(f"Carregando chats de {sample_file}...")
    chats = load_chats_from_json(str(sample_file))
    print(f"Carregados {len(chats)} chats")

    # Filtrar chats com mensagens
    chats_with_messages = [c for c in chats if c.messages and len(c.messages) >= 3]
    print(f"Chats com >= 3 mensagens: {len(chats_with_messages)}")

    # Testar apenas os primeiros N chats
    n_test = 5  # Testar 5 chats
    test_chats = chats_with_messages[:n_test]

    print(f"\nTestando {len(test_chats)} chats...")

    try:
        client = GeminiClient()
    except ValueError as e:
        print(f"Erro ao inicializar Gemini: {e}")
        print("Configure GEMINI_API_KEY no .env")
        return

    results = []
    output_file = Path("data/analysis_results/test_prompts_output.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    for idx, chat in enumerate(test_chats):
        result = await test_single_chat(client, chat, idx)
        if result:
            results.append({"chat_id": chat.id, "analysis": result})

        # Salvar progresso após cada chat
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n[Progresso salvo: {len(results)} chats em {output_file}]")

        # Rate limiting entre chats
        if idx < len(test_chats) - 1:
            print("[Aguardando 1s...]")
            await asyncio.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"CONCLUIDO! {len(results)} chats analisados.")
    print(f"Resultados em: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
