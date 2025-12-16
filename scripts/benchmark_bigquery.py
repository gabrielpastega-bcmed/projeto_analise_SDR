"""
Benchmark: Tempo de resposta do BigQuery para diferentes volumes de chats.
"""

import sys
import time
from pathlib import Path

# Adicionar diretorio raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion import load_chats_from_bigquery


def benchmark(limit: int, lightweight: bool = True, days: int = 30):
    """Mede tempo de carregamento do BigQuery."""
    print(f"\n{'=' * 60}")
    print(f"Benchmark: {limit} chats | Lightweight: {lightweight} | Dias: {days}")
    print("=" * 60)

    start = time.time()
    try:
        chats = load_chats_from_bigquery(days=days, limit=limit, lightweight=lightweight)
        elapsed = time.time() - start
        print(f"\n[OK] {len(chats)} chats carregados em {elapsed:.2f} segundos")
        print(f"     Taxa: {len(chats) / elapsed:.1f} chats/segundo")
        return elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"\n[ERROR] Falha apos {elapsed:.2f} segundos: {e}")
        return None


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("BENCHMARK BIGQUERY - PROJETO ANALISE SDR")
    print("=" * 60)

    results = {}

    # Teste 1: 500 chats lightweight (sem mensagens)
    results["500_light"] = benchmark(500, lightweight=True)

    # Teste 2: 500 chats completos (com mensagens)
    results["500_full"] = benchmark(500, lightweight=False)

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    for key, value in results.items():
        status = f"{value:.2f}s" if value else "FALHOU"
        print(f"  {key}: {status}")
