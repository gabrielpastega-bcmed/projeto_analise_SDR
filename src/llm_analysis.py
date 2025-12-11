"""
Módulo para análise qualitativa de conversas usando um Modelo de Linguagem Grande (LLM).

Este módulo define os prompts para diferentes tipos de análise e fornece uma
classe `LLMAnalyzer` que orquestra as chamadas a um serviço de LLM.

Atualmente, o módulo retorna dados MOCK para simular a resposta do LLM.
"""
import asyncio
from typing import Any, Dict

from src.models import Chat

# --- Seção de Prompts ---
# Cada prompt é uma instrução para o LLM, pedindo uma análise específica
# e a resposta em um formato JSON estruturado.

PROMPT_CX = """
Analise a transcrição de chat a seguir sob a ótica de Experiência do Cliente (CX).
Retorne um objeto JSON com os seguintes campos:
- sentiment: "positivo", "neutro" ou "negativo"
- humanization_score: um inteiro de 1 (robótico) a 5 (muito humano/personalizado)
- nps_prediction: um inteiro de 0 a 10 (probabilidade de recomendação)
- resolution_status: "resolvido", "não resolvido" ou "pendente"
- satisfaction_comment: Uma breve explicação sobre o sentimento.

Transcrição:
{transcript}
"""

PROMPT_PRODUCT = """
Analise a transcrição de chat a seguir para Inteligência de Produto.
Retorne um objeto JSON com os seguintes campos:
- products_mentioned: Lista de strings (nomes de produtos, tecnologias)
- interest_level: "alto", "médio" ou "baixo"
- trends: Lista de strings (necessidades emergentes, perguntas específicas)

Transcrição:
{transcript}
"""

PROMPT_SALES = """
Analise a transcrição de chat a seguir para Conversão de Vendas.
Retorne um objeto JSON com os seguintes campos:
- funnel_stage: "consciência", "consideração" ou "decisão"
- outcome: "convertido", "perdido" ou "em andamento"
- rejection_reason: Se perdido, o motivo principal (ex: "preço", "estoque",
  "concorrente", "sem resposta"). Se não, nulo.
- next_step: Qual é o próximo item de ação?

Transcrição:
{transcript}
"""

PROMPT_QA = """
Analise a transcrição de chat a seguir para Quality Assurance (QA).
Retorne um objeto JSON com os seguintes campos:
- script_adherence: booleano (o agente fez as perguntas-chave de qualificação?)
- key_questions_asked: Lista de strings (ex: "Clínica ou PF?", "Localização?")
- improvement_areas: Lista de strings (o que o agente poderia fazer melhor?)

Transcrição:
{transcript}
"""


class LLMAnalyzer:
    """
    Coordena a análise de chats com um LLM, utilizando processamento assíncrono
    para otimizar o tempo de resposta.
    """

    def __init__(self, api_key: str = "mock_key"):
        """
        Inicializa o analisador.

        Args:
            api_key: A chave de API para o serviço de LLM. Atualmente, usa "mock_key".
        """
        self.api_key = api_key

    def _format_transcript(self, chat: Chat) -> str:
        """
        Formata as mensagens de um chat em uma string de transcrição legível.
        """
        lines = []
        for msg in chat.messages:
            sender = "Agente" if (msg.sentBy and msg.sentBy.type == "agent") else "Cliente"
            body = msg.body.replace("<p>", "").replace("</p>", "").replace("<br>", "\n")
            lines.append(f"{sender} ({msg.time}): {body}")
        return "\n".join(lines)

    async def analyze_chat(self, chat: Chat) -> Dict[str, Any]:
        """
        Orquestra a análise executando as chamadas ao LLM em paralelo.
        Isto otimiza o tempo de I/O, aguardando todas as respostas simultaneamente.

        Args:
            chat: O objeto Chat a ser analisado.

        Returns:
            Um dicionário com as análises de CX, Produto, Vendas e QA.
        """
        transcript = self._format_transcript(chat)

        # Cria uma tarefa para cada tipo de análise
        tasks = {
            "cx": self._call_llm(PROMPT_CX.format(transcript=transcript), "cx"),
            "product": self._call_llm(PROMPT_PRODUCT.format(transcript=transcript), "product"),
            "sales": self._call_llm(PROMPT_SALES.format(transcript=transcript), "sales"),
            "qa": self._call_llm(PROMPT_QA.format(transcript=transcript), "qa"),
        }

        # Executa todas as tarefas em paralelo
        results = await asyncio.gather(*tasks.values())

        # Combina os resultados em um único dicionário
        return {key: result for key, result in zip(tasks.keys(), results)}

    async def _call_llm(self, prompt: str, analysis_type: str) -> Dict[str, Any]:
        """
        Simula uma chamada HTTP assíncrona a um provedor de LLM.

        Args:
            prompt: O prompt formatado a ser enviado para o LLM.
            analysis_type: O tipo de análise (usado para retornar o mock correto).

        Returns:
            Um dicionário com a resposta JSON simulada do LLM.
        """
        # Simula o tempo de espera de uma chamada de rede
        await asyncio.sleep(0.1)

        # Mock da resposta, baseado no tipo de análise
        mock_responses: Dict[str, Dict[str, Any]] = {
            "cx": {
                "sentiment": "neutro",
                "humanization_score": 4,
                "nps_prediction": 8,
                "resolution_status": "resolvido",
                "satisfaction_comment": "Cliente recebeu a informação solicitada.",
            },
            "product": {
                "products_mentioned": ["Ultrassom Microfocado", "HIFU"],
                "interest_level": "alto",
                "trends": ["Resultados de marca própria"],
            },
            "sales": {
                "funnel_stage": "consideração",
                "outcome": "em andamento",
                "rejection_reason": None,
                "next_step": "Contato de um especialista",
            },
            "qa": {
                "script_adherence": True,
                "key_questions_asked": ["Região", "Tipo de equipamento"],
                "improvement_areas": ["Poderia ter perguntado sobre o orçamento"],
            },
        }
        return mock_responses.get(analysis_type, {})
