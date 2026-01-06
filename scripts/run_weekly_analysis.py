"""
Script para executar analise semanal de chats.

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
    Calcula o intervalo da semana ÚTIL a analisar (segunda a sexta).

    A empresa opera apenas em dias úteis (seg-sex), portanto:
    - Semana = 5 dias (segunda a sexta)
    - Exclui sábado e domingo

    Args:
        week_start_str: Data de início no formato YYYY-MM-DD.
                       Se None, usa semana útil anterior.

    Returns:
        Tupla (week_start, week_end) representando segunda e sexta.
    """
    if week_start_str:
        # Manual: usa data fornecida como segunda-feira
        week_start = datetime.strptime(week_start_str, "%Y-%m-%d")
        # Semana útil: segunda + 4 dias = sexta
        week_end = week_start + timedelta(days=4)
    else:
        # Automático: calcula semana útil ANTERIOR
        today = datetime.now()

        # Encontra a ultima sexta-feira (fim da semana útil passada)
        days_since_monday = today.weekday()  # 0=Monday, 6=Sunday

        if days_since_monday >= 5:  # Sábado (5) ou Domingo (6)
            # Se hoje é fim de semana, volta para a sexta-feira passada
            days_to_last_friday = days_since_monday - 4
        else:  # Segunda a Sexta (0-4)
            # Se hoje é dia útil, volta para a sexta-feira da semana passada
            days_to_last_friday = days_since_monday + 3

        last_friday = today - timedelta(days=days_to_last_friday)
        last_friday = last_friday.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )

        # Semana útil: sexta - 4 dias = segunda
        week_start = last_friday - timedelta(days=4)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

        week_end = last_friday

    return week_start, week_end


async def run_analysis(week_start: datetime, week_end: datetime, max_chats: int = 200):
    """
    Executa a analise para uma semana específica.

    Args:
        week_start: Início da semana.
        week_end: Fim da semana.
        max_chats: Máximo de chats a analisar.
    """
    import json
    from pathlib import Path

    from src.batch_analyzer import BatchAnalyzer
    from src.ingestion import load_chats_from_bigquery

    print(f"\n{'=' * 60}")
    print(
        f"ANALISE SEMANAL - {week_start.strftime('%d/%m/%Y')} a {week_end.strftime('%d/%m/%Y')}"
    )
    print(f"{'=' * 60}\n")

    # Verificar API Key
    if not os.getenv("GEMINI_API_KEY"):
        print("[ERRO] GEMINI_API_KEY nao configurada!")
        return

    analyzer = BatchAnalyzer()

    # Arquivo de checkpoint
    checkpoint_file = Path(
        f"data/analysis_results/checkpoint_{week_start.strftime('%Y-%m-%d')}.json"
    )
    checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

    # Carregar checkpoint existente
    existing_results = []
    existing_ids = set()
    if checkpoint_file.exists():
        with open(checkpoint_file, encoding="utf-8") as f:
            existing_results = json.load(f)
            existing_ids = {r.get("chat_id") for r in existing_results}
        print(f"[CHECKPOINT] {len(existing_results)} chats ja processados")

    # ETAPA 1: Carregar chats do BigQuery PRIMEIRO
    print("[1/4] Carregando chats do BigQuery...")
    days_back = (datetime.now() - week_start).days + 7
    chats = load_chats_from_bigquery(
        days=days_back, limit=max_chats * 2, lightweight=False
    )

    # ETAPA 2: Filtrar chats por data (semana útil)
    print("[2/4] Filtrando chats da semana...")
    chats_in_week = []
    for chat in chats:
        if not chat.messages:
            continue

        # CRÍTICO: Usa lastMessageDate (término do chat) ao invés de firstMessageDate
        # Isso garante que:
        # 1. O chat FINALIZOU na semana (não apenas começou)
        # 2. Analisamos conversas COMPLETAS (imutáveis)
        # 3. Evitamos reprocessar chats em andamento
        if chat.lastMessageDate:
            chat_date = chat.lastMessageDate
            if isinstance(chat_date, str):
                try:
                    chat_date = datetime.fromisoformat(chat_date.replace("Z", "+00:00"))
                except Exception:
                    continue
            if hasattr(chat_date, "date"):
                chat_date = chat_date.replace(tzinfo=None)

            # Valida: chat FINALIZOU na semana útil?
            if week_start.date() <= chat_date.date() <= week_end.date():
                chats_in_week.append(chat)

    print(f"      {len(chats_in_week)} chats encontrados na semana")

    # ETAPA 3: Verificar duplicados APENAS dos chats do batch atual (OTIMIZADO)
    print("[3/4] Verificando chats ja analisados (batch otimizado)...")
    batch_ids = [chat.id for chat in chats_in_week]

    if batch_ids:
        analyzed_ids_pg = analyzer.get_analyzed_chat_ids_postgres(batch_ids=batch_ids)

        # Se Postgres não estiver configurado, tenta BigQuery como fallback
        if not analyzed_ids_pg:
            try:
                analyzed_ids = analyzer.get_analyzed_chat_ids(week_start)
                print(f"      {len(analyzed_ids)} chats ja analisados no BigQuery")
            except Exception:
                analyzed_ids = set()
                print("      Nenhum chat analisado anteriormente")
        else:
            analyzed_ids = analyzed_ids_pg
            print(
                f"      {len(analyzed_ids)}/{len(batch_ids)} chats ja analisados no Postgres"
            )
    else:
        analyzed_ids = set()
        print("      Nenhum chat encontrado na semana")

    # Combinar IDs já processados (Postgres/BigQuery + checkpoint local)
    skip_ids = analyzed_ids | existing_ids

    # ETAPA 4: Filtrar duplicados
    chats_to_analyze = []
    for chat in chats_in_week:
        if chat.id in skip_ids:
            continue  # IGNORA duplicado
        chats_to_analyze.append(chat)

    print(f"      {len(chats_to_analyze)} chats NOVOS pendentes de analise")

    if not chats_to_analyze:
        print("\n[OK] Nenhum chat novo para analisar!")
        # Se tem checkpoint, salvar no BigQuery
        if existing_results:
            print("[4/4] Salvando checkpoint no PostgreSQL...")
            saved = analyzer.save_to_postgres(existing_results)
            print(f"      {saved} resultados salvos")
        return

    # Limitar quantidade
    chats_to_analyze = chats_to_analyze[:max_chats]
    print(f"      Limite aplicado: analisando {len(chats_to_analyze)} chats")

    # Callback para salvar checkpoint
    def save_checkpoint(result):
        existing_results.append(result)
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(existing_results, f, ensure_ascii=False, indent=2)

    # Executar analise
    print("[4/4] Executando analise com Gemini (paralelo)...")

    def progress_callback(current, total):
        pct = current / total * 100
        print(f"      Progresso: {current}/{total} ({pct:.1f}%)")

    # Processar em chunks para volumes muito grandes
    CHUNK_SIZE = 500  # Processa 500 chats por vez

    for chunk_idx in range(0, len(chats_to_analyze), CHUNK_SIZE):
        chunk = chats_to_analyze[chunk_idx : chunk_idx + CHUNK_SIZE]
        chunk_num = (chunk_idx // CHUNK_SIZE) + 1
        total_chunks = (len(chats_to_analyze) + CHUNK_SIZE - 1) // CHUNK_SIZE

        print(f"\n  Chunk {chunk_num}/{total_chunks}: {len(chunk)} chats")

        chunk_results = await analyzer.run_batch_parallel(
            chunk,
            concurrency=15,  # Otimizado para 240 RPM
            progress_callback=progress_callback,
            checkpoint_callback=save_checkpoint,
        )

        # Salvar chunk no BigQuery imediatamente
        if chunk_results:
            print(f"  Salvando chunk {chunk_num} no PostgreSQL...")
            analyzer.save_to_postgres(chunk_results)

    # Combinar todos os resultados
    all_results = existing_results

    # Contar resultados validos
    valid_results = [r for r in all_results if "error" not in r]
    error_results = [r for r in all_results if "error" in r]

    print(f"\n  TOTAL: {len(valid_results)} analises concluidas")
    if error_results:
        print(f"  {len(error_results)} erros")

    # BigQuery já foi salvo em chunks durante analise, só salvamos backup local
    print("\n[CONCLUIDO] Salvando backup local...")
    analyzer.save_results(
        all_results, f"analysis_{week_start.strftime('%Y-%m-%d')}.json"
    )

    # Limpar checkpoint (concluido com sucesso)
    if checkpoint_file.exists():
        checkpoint_file.unlink()

    print(f"\n{'=' * 60}")
    print("CONCLUIDO!")
    print(f"  - {len(valid_results)} resultados salvos no PostgreSQL (em chunks)")
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
        default=10000,  # Aumentado de 200 para 10000
        help="Maximo de chats a analisar (default: 10000, use 0 para ilimitado)",
    )

    args = parser.parse_args()

    week_start, week_end = get_week_range(args.week)

    asyncio.run(run_analysis(week_start, week_end, args.max_chats))


if __name__ == "__main__":
    main()
