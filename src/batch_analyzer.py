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
from typing import Any, Callable, Dict, List, Optional

from src.gemini_client import GeminiClient
from src.models import Chat


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
        rate_limit: int = 60,
    ):
        """
        Inicializa o analisador de batch.

        Args:
            api_key: Chave de API do Gemini.
            results_dir: Diretório para salvar resultados.
            rate_limit: Limite de requisições por minuto.
        """
        self.client = GeminiClient(api_key)
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.rate_limit = rate_limit
        self._request_times: List[float] = []

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
        Analisa um único chat com rate limiting.

        Args:
            chat: O chat a ser analisado.

        Returns:
            Dicionário com resultados da análise.
        """
        await self._wait_for_rate_limit()

        transcript = format_transcript(chat)
        if not transcript.strip():
            return {
                "chat_id": chat.id,
                "error": "Chat sem mensagens",
                "timestamp": datetime.now().isoformat(),
            }

        try:
            results = await self.client.analyze_chat_full(transcript)
            return {
                "chat_id": chat.id,
                "agent": chat.agent.name if chat.agent else "Sem Agente",
                "analysis": results,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "chat_id": chat.id,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def run_batch(
        self,
        chats: List[Chat],
        batch_size: int = 10,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Processa uma lista de chats em lotes.

        Args:
            chats: Lista de chats a processar.
            batch_size: Tamanho de cada lote (para paralelismo limitado).
            progress_callback: Função para reportar progresso (current, total).

        Returns:
            Lista de resultados de análise.
        """
        results = []
        total = len(chats)

        for i in range(0, total, batch_size):
            batch = chats[i : i + batch_size]
            batch_results = await asyncio.gather(*[self.analyze_chat(chat) for chat in batch])
            results.extend(batch_results)

            if progress_callback:
                progress_callback(min(i + batch_size, total), total)

            print(f"Processados {min(i + batch_size, total)}/{total} chats")

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
    ) -> int:
        """
        Salva os resultados de análise no BigQuery.

        Args:
            results: Lista de resultados da análise.
            week_start: Início da semana analisada.
            week_end: Fim da semana analisada.

        Returns:
            Número de linhas inseridas.
        """
        from google.cloud import bigquery

        client = bigquery.Client()
        table_id = self._get_bigquery_table_id()

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

        errors = client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            print(f"Erros ao inserir: {errors}")
            return 0

        print(f"[OK] {len(rows_to_insert)} resultados salvos no BigQuery")
        return len(rows_to_insert)

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
            WHERE week_start = '{week_start.strftime("%Y-%m-%d")}'
            ORDER BY analyzed_at DESC
            """
        else:
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
        WHERE week_start = '{week_start.strftime("%Y-%m-%d")}'
        """

        results = client.query(query).result()
        return {row.chat_id for row in results}
