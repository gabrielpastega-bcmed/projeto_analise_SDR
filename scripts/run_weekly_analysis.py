"""
Script para executar análise semanal de chats.

Pode ser executado via cron ou Cloud Scheduler:
    python scripts/run_weekly_analysis.py
    python scripts/run_weekly_analysis.py --week 2025-12-09
    python scripts/run_weekly_analysis.py --max-chats 200
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


def get_week_range(week_start_str: Optional[str] = None) -> tuple[datetime, datetime]:
    """
    Calcula o intervalo da semana a analisar.

    Args:
        week_start_str: Data de início no formato YYYY-MM-DD. Se None, usa semana anterior.

    Returns:
        Tupla (week_start, week_end).
    """
    if week_start_str:
        week_start = datetime.strptime(week_start_str, "%Y-%m-%d")
        week_end = week_start + timedelta(days=6)
    else:
        # Semana anterior
        today = datetime.now()
        days_since_monday = today.weekday()
        this_monday = today - timedelta(days=days_since_monday)
        this_monday = this_monday.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = this_monday - timedelta(days=7)
        week_end = this_monday - timedelta(days=1)

    return week_start, week_end


async def run_analysis(week_start: datetime, week_end: datetime, max_chats: int = 200):
    """
    Executa a análise para uma semana específica.

    Args:
        week_start: Início da semana.
        week_end: Fim da semana.
        max_chats: Máximo de chats a analisar.
    """
    from src.batch_analyzer import BatchAnalyzer
    from src.ingestion import load_chats_from_bigquery

    print(f"\n{'=' * 60}")
    print(f"ANALISE SEMANAL - {week_start.strftime('%d/%m/%Y')} a {week_end.strftime('%d/%m/%Y')}")
    print(f"{'=' * 60}\n")

    # Verificar API Key
    if not os.getenv("GEMINI_API_KEY"):
        print("[ERRO] GEMINI_API_KEY nao configurada!")
        return

    analyzer = BatchAnalyzer()

    # Verificar chats já analisados
    print("[1/4] Verificando chats ja analisados...")
    analyzed_ids = analyzer.get_analyzed_chat_ids(week_start)
    print(f"      {len(analyzed_ids)} chats ja analisados nesta semana")

    # Carregar chats do BigQuery
    print("[2/4] Carregando chats do BigQuery...")
    days_back = (datetime.now() - week_start).days + 7
    chats = load_chats_from_bigquery(days=days_back, limit=max_chats * 2, lightweight=False)

    # Filtrar chats da semana que ainda não foram analisados
    chats_to_analyze = []
    for chat in chats:
        if chat.id in analyzed_ids:
            continue
        if not chat.messages:
            continue
        # Verificar se está na semana correta
        if chat.firstMessageDate:
            chat_date = chat.firstMessageDate
            if isinstance(chat_date, str):
                try:
                    chat_date = datetime.fromisoformat(chat_date.replace("Z", "+00:00"))
                except Exception:
                    continue
            if hasattr(chat_date, "date"):
                chat_date = chat_date.replace(tzinfo=None)
            if week_start.date() <= chat_date.date() <= week_end.date():
                chats_to_analyze.append(chat)

    print(f"      {len(chats_to_analyze)} chats pendentes de analise")

    if not chats_to_analyze:
        print("\n[OK] Nenhum chat novo para analisar!")
        return

    # Limitar quantidade
    chats_to_analyze = chats_to_analyze[:max_chats]
    print(f"      Analisando {len(chats_to_analyze)} chats...")

    # Executar análise
    print("[3/4] Executando analise com Gemini...")

    def progress_callback(current, total):
        pct = current / total * 100
        print(f"      Progresso: {current}/{total} ({pct:.1f}%)", end="\r")

    results = await analyzer.run_batch(
        chats_to_analyze,
        batch_size=5,
        progress_callback=progress_callback,
    )
    print()

    # Contar resultados válidos
    valid_results = [r for r in results if "error" not in r]
    error_results = [r for r in results if "error" in r]

    print(f"      {len(valid_results)} analises concluidas")
    if error_results:
        print(f"      {len(error_results)} erros")

    # Salvar no BigQuery
    print("[4/4] Salvando resultados no BigQuery...")
    saved = analyzer.save_to_bigquery(results, week_start, week_end)

    # Também salvar localmente como backup
    analyzer.save_results(results, f"analysis_{week_start.strftime('%Y-%m-%d')}.json")

    print(f"\n{'=' * 60}")
    print("CONCLUIDO!")
    print(f"  - {saved} resultados salvos no BigQuery")
    print("  - Backup local em data/analysis_results/")
    print(f"{'=' * 60}\n")


def main():
    parser = argparse.ArgumentParser(description="Executar analise semanal de chats")
    parser.add_argument(
        "--week",
        type=str,
        default=None,
        help="Data de inicio da semana (YYYY-MM-DD). Se omitido, usa semana anterior.",
    )
    parser.add_argument(
        "--max-chats",
        type=int,
        default=200,
        help="Maximo de chats a analisar (default: 200)",
    )

    args = parser.parse_args()

    week_start, week_end = get_week_range(args.week)

    asyncio.run(run_analysis(week_start, week_end, args.max_chats))


if __name__ == "__main__":
    main()
