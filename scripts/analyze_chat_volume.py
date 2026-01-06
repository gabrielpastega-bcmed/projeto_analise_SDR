"""
Script para analisar volume de chats por semana e período.

Ajuda a determinar a melhor estratégia de deduplicação.
"""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()


def analyze_chat_volume():
    """Analisa volume de chats para determinar melhor estratégia."""

    client = bigquery.Client()

    project_id = os.getenv("BIGQUERY_PROJECT_ID")
    dataset_id = os.getenv("BIGQUERY_DATASET")
    table_name = "chats"

    table_id = f"{project_id}.{dataset_id}.{table_name}"

    print("\n" + "=" * 60)
    print("ANALISE DE VOLUME DE CHATS")
    print("=" * 60 + "\n")

    # Query 1: Total de chats
    query_total = f"""
    SELECT COUNT(*) as total
    FROM `{table_id}`
    """

    result = client.query(query_total).result()
    total_chats = list(result)[0].total
    print(f"📊 Total de chats (all time): {total_chats:,}")

    # Query 2: Chats por semana (ultimas 8 semanas)
    query_weekly = f"""
    WITH weekly_stats AS (
        SELECT 
            DATE_TRUNC(CAST(firstMessageDate AS DATE), WEEK(MONDAY)) as week_start,
            COUNT(*) as chat_count
        FROM `{table_id}`
        WHERE firstMessageDate >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 8 WEEK)
        GROUP BY week_start
        ORDER BY week_start DESC
    )
    SELECT 
        week_start,
        chat_count,
        AVG(chat_count) OVER() as avg_per_week
    FROM weekly_stats
    """

    print("\n📅 Chats por Semana (ultimas 8 semanas):")
    print("-" * 60)

    results = client.query(query_weekly).result()
    weekly_data = []

    for row in results:
        weekly_data.append(
            {"week": row.week_start, "count": row.chat_count, "avg": row.avg_per_week}
        )
        print(f"  {row.week_start}: {row.chat_count:,} chats")

    if weekly_data:
        avg = weekly_data[0]["avg"]
        print(f"\n  Média semanal: {avg:,.0f} chats/semana")

        # Query 3: Chats por dia (ultima semana)
        query_daily = f"""
        SELECT 
            CAST(firstMessageDate AS DATE) as day,
            COUNT(*) as chat_count
        FROM `{table_id}`
        WHERE firstMessageDate >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        GROUP BY day
        ORDER BY day DESC
        """

        print("\n📆 Chats por Dia (ultima semana):")
        print("-" * 60)

        daily_results = client.query(query_daily).result()
        daily_counts = []

        for row in daily_results:
            daily_counts.append(row.chat_count)
            print(f"  {row.day}: {row.chat_count:,} chats")

        if daily_counts:
            avg_daily = sum(daily_counts) / len(daily_counts)
            print(f"\n  Média diária: {avg_daily:,.0f} chats/dia")

        # Analise de estratégia
        print("\n" + "=" * 60)
        print("💡 ANALISE DE ESTRATÉGIA")
        print("=" * 60 + "\n")

        if avg < 100:
            strategy = "BATCH-BASED (Atual)"
            reason = "Volume baixo, batch otimizado é ideal"
        elif avg < 1000:
            strategy = "BATCH-BASED (Recomendado)"
            reason = "Volume médio, batch otimizado funciona bem"
        elif avg < 5000:
            strategy = "HÍBRIDO"
            reason = "Volume alto, considere batch para novos + index para histórico"
        else:
            strategy = "INDEX-BASED"
            reason = "Volume muito alto, considere index separado de IDs analisados"

        print(f"Volume médio semanal: {avg:,.0f} chats")
        print(f"Estrategia recomendada: {strategy}")
        print(f"Razao: {reason}")

        print("\n📊 Comparação de Abordagens:")
        print("-" * 60)

        # Batch-based
        batch_size = 500
        num_batches = int(avg / batch_size) + 1
        print(f"\n1. BATCH-BASED (atual otimizado):")
        print(f"   - Batches por semana: {num_batches}")
        print(f"   - IDs por query: {batch_size} (maximo)")
        print(f"   - Queries total: {num_batches}")
        print(f"   - Custo estimado: BAIXO")
        print(f"   - Complexidade: BAIXA")

        # Week-based
        print(f"\n2. WEEK-BASED (busca todos da semana):")
        print(f"   - IDs por query: {avg:,.0f}")
        print(f"   - Queries total: 1")
        print(f"   - Custo estimado: {'MÉDIO' if avg < 5000 else 'ALTO'}")
        print(f"   - Complexidade: BAIXA")

        # Bloom filter / Index
        print(f"\n3. BLOOM FILTER / EXTERNAL INDEX:")
        print(f"   - IDs em memória: {avg:,.0f}")
        print(f"   - Memory footprint: ~{avg * 50 / 1024:.1f} KB")
        print(f"   - Queries total: 0 (apos carregar)")
        print(f"   - Custo estimado: {'BAIXO' if avg < 10000 else 'MÉDIO'}")
        print(f"   - Complexidade: ALTA")

        print("\n" + "=" * 60)
        print("RECOMENDACOES:")
        print("=" * 60)

        if avg < 1000:
            print(
                """
✅ BATCH-BASED é a melhor opção:
   - Volume está dentro do ideal (< 1000/semana)
   - Query otimizada com WHERE IN (...) é muito rápida
   - Baixa complexidade de implementação
   - Escalável até ~5000 chats/semana

💡 Próximos passos:
   1. Implementar batch-based otimizado
   2. Monitorar performance
   3. Reavaliar se volume crescer >5000/semana
            """
            )
        elif avg < 5000:
            print(
                """
⚠️ BATCH-BASED funciona, mas considere otimizações:
   - Volume está alto (1000-5000/semana)
   - Batch-based ainda é eficiente
   - Considere cache de IDs analisados em memória
   - Monitore query performance

💡 Próximos passos:
   1. Implementar batch-based
   2. Adicionar cache opcional (Redis)
   3. Reavaliar se volume crescer >5000/semana
            """
            )
        else:
            print(
                """
🔥 Volume ALTO - Considere abordagem híbrida:
   - Volume está muito alto (>5000/semana)
   - Batch-based pode ficar lento
   - Recomendo uma das seguintes:
     a) Tabela auxiliar com IDs analisados (index otimizado)
     b) Bloom filter em memória
     c) Cache distribuído (Redis)

💡 Próximos passos:
   1. Implementar batch-based como MVP
   2. Monitorar performance real
   3. Migrar para solução escalável se necessário
            """
            )


if __name__ == "__main__":
    analyze_chat_volume()
