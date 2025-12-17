"""
Analisador em batch para processamento semanal de chats com Gemini.

Este módulo fornece funções para:
- Processar chats em lotes com rate limiting
- Calcular período da semana anterior
- Persistir resultados para uso no dashboard
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Union, cast

from config.settings import settings
from src.gemini_client import GeminiClient
from src.llm_cache import LLMCache
from src.logging_config import get_logger
from src.models import Chat

logger = get_logger(__name__)


def get_previous_week_range() -> tuple[datetime, datetime]:
    """
    Retorna o intervalo da semana anterior (segunda a domingo).

    Returns:
        Tupla com (início_semana, fim_semana) em datetime.
    """
    today = datetime.now()
    # Encontra a segunda-feira da semana atual
    days_since_monday = today.weekday()
    this_monday = today - timedelta(days=days_since_monday)
    this_monday = this_monday.replace(hour=0, minute=0, second=0, microsecond=0)

    # Semana anterior
    last_monday = this_monday - timedelta(days=7)
    last_sunday = this_monday - timedelta(seconds=1)

    return last_monday, last_sunday


def format_transcript(chat: Chat) -> str:
    """
    Formata as mensagens de um chat em uma string de transcrição legível.

    Args:
        chat: O objeto Chat a ser formatado.

    Returns:
        String com a transcrição formatada.
    """
    lines = []
    for msg in chat.messages:
        sender = "Agente" if (msg.sentBy and msg.sentBy.type == "agent") else "Cliente"
        body = msg.body.replace("<p>", "").replace("</p>", "").replace("<br>", "\n")
        timestamp = msg.time.strftime("%H:%M") if msg.time else ""
        lines.append(f"{sender} ({timestamp}): {body}")
    return "\n".join(lines)


class BatchAnalyzer:
    """
    Processador de lotes para análise qualitativa com Gemini.

    Atributos:
        client: Cliente GeminiClient para chamadas à API.
        results_dir: Diretório para salvar resultados.
        rate_limit: Requisições por minuto permitidas.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        results_dir: str = "data/analysis_results",
        rate_limit: int = 240,  # Tier 1: 300 RPM max, usando 80% como segurança
    ):
        """
        Inicializa o analisador de batch.

        Args:
            api_key: Chave de API do Gemini.
            results_dir: Diretório para salvar resultados.
            rate_limit: Limite de requisições por minuto (default: 10 para free tier).
        """
        self.client = GeminiClient(api_key)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit
        self._request_times: List[float] = []

        # Initialize LLM cache (safe: disabled by default if Redis unavailable)
        self.cache = LLMCache(
            redis_url=settings.cache.redis_url,
            ttl_seconds=settings.cache.ttl_seconds,
            enabled=settings.cache.enabled,
        )

        logger.info(f"BatchAnalyzer inicializado (rate_limit={rate_limit} RPM, cache={self.cache.enabled})")

    async def _wait_for_rate_limit(self) -> None:
        """Aguarda se necessário para respeitar o rate limit."""
        now = asyncio.get_event_loop().time()

        # Remove timestamps antigos (mais de 60s)
        self._request_times = [t for t in self._request_times if now - t < 60]

        if len(self._request_times) >= self.rate_limit:
            # Aguarda até o request mais antigo completar 60s
            wait_time = 60 - (now - self._request_times[0])
            if wait_time > 0:
                print(f"Rate limit atingido. Aguardando {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)

        self._request_times.append(now)

    async def analyze_chat(self, chat: Chat) -> Dict[str, Any]:
        """
        Analisa um único chat com rate limiting e métricas.

        Args:
            chat: O chat a ser analisado.

        Returns:
            Dicionário com resultados da análise, incluindo métricas.
        """
        import time

        start_time = time.time()

        # Try cache first (safe: returns None if disabled or fails)
        try:
            cached_result = self.cache.get(chat.id) if self.cache else None
            if cached_result:
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.info(f"Cache HIT for chat {chat.id} ({elapsed_ms}ms)")
                return {
                    "chat_id": chat.id,
                    "agent": chat.agent.name if chat.agent else "Sem Agente",
                    "analysis": cached_result,
                    "timestamp": datetime.now().isoformat(),
                    "processing_time_ms": elapsed_ms,
                    "from_cache": True,
                }
        except Exception as e:
            # Cache failure should not break analysis - just log and continue
            logger.warning(f"Cache GET failed for chat {chat.id}: {e}")

        await self._wait_for_rate_limit()

        transcript = format_transcript(chat)
        if not transcript.strip():
            return {
                "chat_id": chat.id,
                "error": "Chat sem mensagens",
                "timestamp": datetime.now().isoformat(),
                "processing_time_ms": 0,
            }

        try:
            results = await self.client.analyze_chat_full(transcript)
            elapsed_ms = int((time.time() - start_time) * 1000)

            # Try to cache result (safe: fails silently)
            try:
                if self.cache:
                    self.cache.set(chat.id, results)
            except Exception as e:
                logger.warning(f"Cache SET failed for chat {chat.id}: {e}")

            logger.info(
                f"Chat {chat.id} analisado em {elapsed_ms}ms (agent={chat.agent.name if chat.agent else 'N/A'})"
            )

            return {
                "chat_id": chat.id,
                "agent": chat.agent.name if chat.agent else "Sem Agente",
                "analysis": results,
                "timestamp": datetime.now().isoformat(),
                "processing_time_ms": elapsed_ms,
                "from_cache": False,
            }
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Erro ao analisar chat {chat.id}: {e} ({elapsed_ms}ms)")

            return {
                "chat_id": chat.id,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "processing_time_ms": elapsed_ms,
            }

    async def run_batch(
        self,
        chats: Union[List[Chat], Iterator[Chat]],  # Aceita list OU generator
        batch_size: int = 1,  # Processamento sequencial por padrão
        progress_callback: Optional[Callable[[int, int], None]] = None,
        checkpoint_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Processa uma lista ou generator de chats sequencialmente com rate limiting.

        Args:
            chats: Lista ou Iterator/Generator de chats a processar.
            batch_size: Ignorado (mantido para compatibilidade). Sempre processa 1 por vez.
            progress_callback: Função para reportar progresso (current, total).
            checkpoint_callback: Função para salvar progresso incremental.

        Returns:
            Lista de resultados de análise.
        """
        results = []

        # Detecta se chats é lista ou generator
        is_list = isinstance(chats, list)
        total = len(cast(List[Chat], chats)) if is_list else None

        # Converte para iterável se necessário
        chat_iter = iter(chats)

        i = 0
        for chat in chat_iter:
            i += 1

            # Rate limiting antes de cada chat
            await self._wait_for_rate_limit()

            # Analisar chat
            result = await self.analyze_chat(chat)
            results.append(result)

            # Checkpoint incremental
            if checkpoint_callback:
                checkpoint_callback(result)

            # Progresso
            if progress_callback:
                if total:
                    progress_callback(i, total)
                else:
                    progress_callback(i, i)  # Generator mode: current = total

            if total:
                logger.info(f"Chat {i}/{total} processado: {chat.id}")
            else:
                logger.info(f"Chat {i} processado: {chat.id} (streaming mode)")

        # Estatísticas finais
        success_count = sum(1 for r in results if "error" not in r)
        error_count = sum(1 for r in results if "error" in r)
        total_time_ms = sum(r.get("processing_time_ms", 0) for r in results)
        avg_time_ms = total_time_ms / len(results) if results else 0

        logger.info(
            f"Batch concluído: {success_count}/{i} sucesso, "
            f"{error_count} erros, "
            f"tempo médio: {avg_time_ms:.0f}ms, "
            f"tempo total: {total_time_ms / 1000:.1f}s"
        )

        return results

    def save_results(self, results: List[Dict[str, Any]], filename: Optional[str] = None) -> Path:
        """
        Salva os resultados em um arquivo JSON.

        Args:
            results: Lista de resultados da análise.
            filename: Nome do arquivo (opcional, usa timestamp se não fornecido).

        Returns:
            Path do arquivo salvo.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"analysis_{timestamp}.json"

        filepath = self.results_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"Resultados salvos em: {filepath}")
        return filepath

    def load_latest_results(self) -> Optional[List[Dict[str, Any]]]:
        """
        Carrega os resultados mais recentes.

        Returns:
            Lista de resultados ou None se não houver arquivos.
        """
        json_files = list(self.results_dir.glob("analysis_*.json"))
        if not json_files:
            return None

        # Ordena por data de modificação (mais recente primeiro)
        latest = max(json_files, key=lambda p: p.stat().st_mtime)

        with open(latest, "r", encoding="utf-8") as f:
            return json.load(f)

    def aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Agrega os resultados de análise para exibição no dashboard.

        Args:
            results: Lista de resultados individuais.

        Returns:
            Dicionário com métricas agregadas.
        """
        valid_results = [r for r in results if "analysis" in r and "error" not in r]

        if not valid_results:
            return {"error": "Nenhum resultado válido"}

        # Agregações de CX
        sentiments = [r["analysis"]["cx"].get("sentiment", "neutro") for r in valid_results if "cx" in r["analysis"]]
        sentiment_counts = {"positivo": 0, "neutro": 0, "negativo": 0}
        for s in sentiments:
            if s in sentiment_counts:
                sentiment_counts[s] += 1

        humanization_scores = [
            r["analysis"]["cx"].get("humanization_score", 3) for r in valid_results if "cx" in r["analysis"]
        ]
        avg_humanization = sum(humanization_scores) / len(humanization_scores) if humanization_scores else 0

        nps_scores = [r["analysis"]["cx"].get("nps_prediction", 5) for r in valid_results if "cx" in r["analysis"]]
        avg_nps = sum(nps_scores) / len(nps_scores) if nps_scores else 0

        # Agregações de Sales
        outcomes = [
            r["analysis"]["sales"].get("outcome", "em andamento") for r in valid_results if "sales" in r["analysis"]
        ]
        outcome_counts = {"convertido": 0, "perdido": 0, "em andamento": 0}
        for o in outcomes:
            if o in outcome_counts:
                outcome_counts[o] += 1

        # Agregações de Produto
        all_products = []
        for r in valid_results:
            if "product" in r["analysis"]:
                all_products.extend(r["analysis"]["product"].get("products_mentioned", []))

        product_counts: Dict[str, int] = {}
        for p in all_products:
            product_counts[p] = product_counts.get(p, 0) + 1

        # Top produtos
        top_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "total_analyzed": len(valid_results),
            "cx": {
                "sentiment_distribution": sentiment_counts,
                "avg_humanization_score": round(avg_humanization, 2),
                "avg_nps_prediction": round(avg_nps, 2),
            },
            "sales": {
                "outcome_distribution": outcome_counts,
                "conversion_rate": round(outcome_counts["convertido"] / len(outcomes) * 100 if outcomes else 0, 1),
            },
            "product": {
                "top_products": top_products,
                "total_mentions": len(all_products),
            },
        }

    # ================================================================
    # BIGQUERY INTEGRATION
    # ================================================================

    def _get_bigquery_table_id(self) -> str:
        """Retorna o ID completo da tabela de resultados."""
        import os

        project = os.getenv("BIGQUERY_PROJECT_ID")
        dataset = os.getenv("BIGQUERY_DATASET", "octadesk")
        table = "octadesk_analysis_results"
        return f"{project}.{dataset}.{table}"

    def save_to_bigquery(
        self,
        results: List[Dict[str, Any]],
        week_start: datetime,
        week_end: datetime,
        chunk_size: int = 500,
    ) -> int:
        """
        Salva os resultados de análise no BigQuery com chunked writes.

        Args:
            results: Lista de resultados da análise.
            week_start: Início da semana analisada.
            week_end: Fim da semana analisada.
            chunk_size: Tamanho do chunk para inserts (default: 500).

        Returns:
            Número de linhas inseridas.
        """
        from google.cloud import bigquery

        client = bigquery.Client()
        table_id = self._get_bigquery_table_id()

        # Prepara todas as linhas
        rows_to_insert = []
        for r in results:
            if "error" in r:
                continue  # Pula resultados com erro

            analysis = r.get("analysis", {})
            cx = analysis.get("cx", {})
            sales = analysis.get("sales", {})
            product = analysis.get("product", {})
            qa = analysis.get("qa", {})

            row = {
                "chat_id": r.get("chat_id"),
                "week_start": week_start.strftime("%Y-%m-%d"),
                "week_end": week_end.strftime("%Y-%m-%d"),
                "analyzed_at": datetime.now().isoformat(),
                "agent_name": r.get("agent"),
                # CX
                "cx_sentiment": cx.get("sentiment"),
                "cx_humanization_score": cx.get("humanization_score"),
                "cx_nps_prediction": cx.get("nps_prediction"),
                "cx_resolution_status": cx.get("resolution_status"),
                "cx_satisfaction_comment": cx.get("satisfaction_comment"),
                # Sales
                "sales_funnel_stage": sales.get("funnel_stage"),
                "sales_outcome": sales.get("outcome"),
                "sales_rejection_reason": sales.get("rejection_reason"),
                "sales_next_step": sales.get("next_step"),
                # Product
                "products_mentioned": product.get("products_mentioned", []),
                "interest_level": product.get("interest_level"),
                "trends": product.get("trends", []),
                # QA
                "qa_script_adherence": qa.get("script_adherence"),
                "key_questions_asked": qa.get("key_questions_asked", []),
                "improvement_areas": qa.get("improvement_areas", []),
            }
            rows_to_insert.append(row)

        if not rows_to_insert:
            print("Nenhum resultado valido para salvar.")
            return 0

        # Insere em chunks para evitar limite de 10MB do BigQuery
        total_inserted = 0
        total_chunks = (len(rows_to_insert) + chunk_size - 1) // chunk_size

        logger.info(
            f"Salvando {len(rows_to_insert)} resultados em {total_chunks} chunks " f"de até {chunk_size} linhas"
        )

        for i in range(0, len(rows_to_insert), chunk_size):
            chunk = rows_to_insert[i : i + chunk_size]
            chunk_num = (i // chunk_size) + 1

            logger.info(f"Inserindo chunk {chunk_num}/{total_chunks} ({len(chunk)} linhas)...")

            errors = client.insert_rows_json(table_id, chunk)
            if errors:
                logger.error(f"Erros ao inserir chunk {chunk_num}: {errors}")
            else:
                total_inserted += len(chunk)
                logger.info(f"Chunk {chunk_num} inserido com sucesso")

        print(f"[OK] {total_inserted}/{len(rows_to_insert)} resultados salvos no BigQuery")
        return total_inserted

    def load_from_bigquery(
        self,
        week_start: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Carrega resultados de análise do BigQuery.

        Args:
            week_start: Início da semana a carregar. Se None, carrega a mais recente.

        Returns:
            Lista de resultados da análise.
        """
        from google.cloud import bigquery

        client = bigquery.Client()
        table_id = self._get_bigquery_table_id()

        if week_start:
            query = f"""
            SELECT *
            FROM `{table_id}`
            WHERE week_start = @week_start
            ORDER BY analyzed_at DESC
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("week_start", "STRING", week_start.strftime("%Y-%m-%d")),
                ]
            )
            results = client.query(query, job_config=job_config).result()
        else:
            # Sem parâmetro - busca a semana mais recente
            query = f"""
            SELECT *
            FROM `{table_id}`
            WHERE week_start = (SELECT MAX(week_start) FROM `{table_id}`)
            ORDER BY analyzed_at DESC
            """
            results = client.query(query).result()

        return [dict(row) for row in results]

    def get_available_weeks(self) -> List[Dict[str, Any]]:
        """
        Retorna as semanas disponíveis para consulta.

        Returns:
            Lista de dicts com week_start, week_end e count.
        """
        from google.cloud import bigquery

        client = bigquery.Client()
        table_id = self._get_bigquery_table_id()

        query = f"""
        SELECT
            week_start,
            week_end,
            COUNT(*) as total_chats,
            COUNT(DISTINCT agent_name) as total_agents
        FROM `{table_id}`
        GROUP BY week_start, week_end
        ORDER BY week_start DESC
        LIMIT 52
        """

        try:
            results = client.query(query).result()
            return [dict(row) for row in results]
        except Exception:
            return []

    def get_analyzed_chat_ids(self, week_start: datetime) -> set:
        """
        Retorna os IDs dos chats já analisados em uma semana.

        Args:
            week_start: Início da semana.

        Returns:
            Set de chat_ids já analisados.
        """
        from google.cloud import bigquery

        client = bigquery.Client()
        table_id = self._get_bigquery_table_id()

        query = f"""
        SELECT DISTINCT chat_id
        FROM `{table_id}`
        WHERE week_start = @week_start
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("week_start", "STRING", week_start.strftime("%Y-%m-%d")),
            ]
        )

        results = client.query(query, job_config=job_config).result()
        return {row.chat_id for row in results}
