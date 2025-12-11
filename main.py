import asyncio
import json
import logging
from typing import Any, Dict, List

from src.ingestion import get_data_source, load_chats_from_bigquery, load_chats_from_json
from src.llm_analysis import LLMAnalyzer
from src.models import Chat
from src.ops_analysis import analyze_agent_performance
from src.reporting import generate_report

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


async def process_chat(chat: Chat, llm_analyzer: LLMAnalyzer) -> Dict[str, Any]:
    """
    Processa um único chat, executando análises e tratando possíveis exceções.
    """
    try:
        logging.info(f"Processando chat: {chat.id}")
        # A análise operacional agora é feita em lote, então este dict é um placeholder
        ops_metrics = {"tme_seconds": 0, "tma_seconds": 0}  # Será preenchido posteriormente

        # Análise com LLM (assíncrona)
        llm_results = await llm_analyzer.analyze_chat(chat)

        return {
            "chat_id": chat.id,
            "agent_name": chat.agent.name if chat.agent else "Sem Agente",
            "ops_metrics": ops_metrics,
            "llm_results": llm_results,
            "error": None,
        }
    except Exception as e:
        logging.error(f"Falha ao processar o chat {chat.id}: {e}")
        return {"chat_id": chat.id, "error": str(e)}


def update_ops_metrics(
    processed_data: List[Dict[str, Any]], agent_performance: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Atualiza os dados processados com as métricas operacionais calculadas em lote.
    """
    # Mapeia o desempenho do agente para busca rápida
    agent_map = {item["agent"]: item for item in agent_performance}

    for item in processed_data:
        agent_name = item.get("agent_name")
        if agent_name in agent_map:
            agent_metrics = agent_map[agent_name]
            # Atualiza com as médias do agente, já que o cálculo agora é agregado
            item["ops_metrics"]["tme_seconds"] = agent_metrics.get("avg_tme_seconds", 0)
            item["ops_metrics"]["tma_seconds"] = agent_metrics.get("avg_tma_seconds", 0)

    return processed_data


async def main():
    """
    Pipeline principal para carregar, processar e gerar relatórios de chats.
    """
    try:
        # 1. Carregar Dados
        data_source = get_data_source()
        logging.info(f"Fonte de dados configurada: {data_source}")

        if data_source == "bigquery":
            chats = load_chats_from_bigquery()
        else:
            file_path = "data/raw/exemplo.json"
            logging.info(f"Carregando dados de {file_path}...")
            chats = load_chats_from_json(file_path)
        logging.info(f"Carregados {len(chats)} chats.")

        if not chats:
            logging.warning("Nenhum chat para analisar. Encerrando.")
            return

        # 2. Análise Operacional (em lote para performance)
        logging.info("Iniciando análise operacional em lote...")
        agent_performance = analyze_agent_performance(chats)
        logging.info("Análise operacional concluída.")

        # 3. Análise com LLM (em paralelo)
        llm_analyzer = LLMAnalyzer()
        logging.info("Iniciando análise com LLM em paralelo...")
        tasks = [process_chat(chat, llm_analyzer) for chat in chats]
        processed_results = await asyncio.gather(*tasks)

        # Filtra os resultados que tiveram erro
        processed_data = [res for res in processed_results if not res.get("error")]
        logging.info(f"Análise com LLM concluída para {len(processed_data)} chats.")

        # 4. Atualizar Métricas Operacionais
        processed_data = update_ops_metrics(processed_data, agent_performance)

        # 5. Gerar Relatório
        logging.info("Gerando relatório final...")
        report = generate_report(processed_data)

        # 6. Salvar Resultados
        report_path = "analysis_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logging.info(f"Relatório salvo em: {report_path}")

        print("\n=== RELATÓRIO FINAL ===")
        print(json.dumps(report, indent=2, ensure_ascii=False))

    except FileNotFoundError:
        logging.error("Arquivo de dados não encontrado. Verifique o caminho.")
    except Exception as e:
        logging.critical(f"Ocorreu um erro crítico no pipeline: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
