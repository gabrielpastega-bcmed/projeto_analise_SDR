"""
Cliente para integração com a API do Google Gemini.

Este módulo fornece uma classe GeminiClient para análise qualitativa
de conversas usando o modelo Gemini 2.5 Flash.

Migrado para google-genai SDK (substitui google-generativeai deprecado).
"""

import asyncio
import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.logging_config import get_logger

load_dotenv()

# Logger para este módulo
logger = get_logger(__name__)

# Timeout padrão para chamadas à API (segundos)
DEFAULT_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "60"))


class GeminiClient:
    """
    Cliente para a API do Google Gemini.

    Fornece métodos para análise qualitativa de conversas com retry logic
    e parsing de JSON estruturado.

    Usa o novo google-genai SDK (GA desde maio 2025).
    """

    def __init__(self, api_key: str | None = None, timeout: int = DEFAULT_TIMEOUT):
        """
        Inicializa o cliente Gemini.

        Args:
            api_key: Chave de API do Gemini. Se não fornecida, usa GEMINI_API_KEY do ambiente.
            timeout: Timeout em segundos para cada chamada à API.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.timeout = timeout

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não configurada. Configure no .env ou passe como parâmetro.")

        # Novo SDK: usa Client() ao invés de configure()
        self.client = genai.Client(api_key=self.api_key)

        # Modelo Gemini 2.5 Flash - estável, otimizado para texto
        self.model_name = "gemini-2.5-flash"

        # Configuração para respostas JSON estruturadas
        self.generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3,  # Mais determinístico para análises
        )
        logger.info(f"GeminiClient inicializado (timeout={timeout}s, model={self.model_name})")

    async def analyze(self, prompt: str, max_retries: int = 3) -> dict[str, Any]:
        """
        Envia um prompt ao Gemini e retorna a resposta como JSON.

        Args:
            prompt: O prompt formatado para análise.
            max_retries: Número máximo de tentativas em caso de erro.

        Returns:
            Dicionário com a resposta estruturada do modelo.
        """
        for attempt in range(max_retries):
            try:
                # Wrapper com timeout para evitar travamento indefinido
                async with asyncio.timeout(self.timeout):
                    # Nova API: usa client.models.generate_content()
                    response = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.client.models.generate_content(
                            model=self.model_name,
                            contents=prompt,
                            config=self.generation_config,
                        ),
                    )

                # Parse da resposta JSON
                if response.text is None:
                    return {"error": "Resposta vazia do modelo"}
                result = self._parse_response(response.text)
                return result

            except asyncio.TimeoutError:
                logger.error(
                    f"Timeout na chamada Gemini (tentativa {attempt + 1}/{max_retries}, timeout={self.timeout}s)"
                )
                if attempt == max_retries - 1:
                    return {"error": f"Timeout após {self.timeout}s"}

            except json.JSONDecodeError as e:
                logger.warning(f"Erro ao parsear JSON (tentativa {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return {"error": "Falha ao parsear resposta JSON", "raw": response.text}

            except Exception as e:
                logger.warning(f"Erro na chamada Gemini (tentativa {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    return {"error": str(e)}

        return {"error": "Máximo de tentativas excedido"}

    def _parse_response(self, text: str) -> dict[str, Any]:
        """
        Parse da resposta do Gemini para JSON.

        Args:
            text: Texto da resposta do modelo.

        Returns:
            Dicionário com os dados parseados.
        """
        # Remove possíveis marcadores de código
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        return json.loads(text.strip())

    async def analyze_chat_cx(self, transcript: str) -> dict[str, Any]:
        """Analisa experiência do cliente (CX)."""
        prompt = f"""Você é um analista de CX especializado em vendas B2B de equipamentos médicos.
Analise a transcrição de chat a seguir sob a ótica de Experiência do Cliente.

CRITÉRIOS DE AVALIAÇÃO:
- Personalização: O agente usou o nome do cliente? Adaptou a abordagem?
- Empatia: Demonstrou compreensão das necessidades?
- Resolução: O cliente teve suas dúvidas respondidas?
- Profissionalismo: Tom adequado para vendas consultivas?

Retorne um objeto JSON com os seguintes campos:
- sentiment: "positivo", "neutro" ou "negativo"
- humanization_score: inteiro de 1 (robótico) a 5 (muito humanizado)
- nps_prediction: inteiro de 0 a 10 (probabilidade de recomendação)
- resolution_status: "resolvido", "não_resolvido" ou "pendente"
- personalization_used: booleano (usou nome do cliente ou personalizou)
- satisfaction_comment: breve explicação do sentimento

Transcrição:
{transcript}"""
        return await self.analyze(prompt)

    async def analyze_chat_product(self, transcript: str) -> dict[str, Any]:
        """Analisa inteligência de produto."""
        prompt = f"""Você é um analista de produto de uma empresa de equipamentos.
Analise a transcrição para identificar interesses e tendências de produto.

CATEGORIAS (configure conforme seu negócio):
- categoria_a: produtos do tipo A
- categoria_b: produtos do tipo B
- categoria_c: produtos do tipo C
- indefinido: quando nenhum produto é mencionado ou não é possível identificar

IMPORTANTE: Se não houver produtos mencionados, use category="indefinido".

Retorne um objeto JSON com os seguintes campos:
- products_mentioned: lista de produtos/tecnologias mencionados (lista vazia se nenhum)
- category: categoria identificada ou "indefinido"
- interest_level: "alto", "medio" ou "baixo"
- budget_mentioned: booleano (cliente mencionou orçamento/preço)
- trends: lista de necessidades ou perguntas específicas do cliente

Transcrição:
{transcript}"""
        return await self.analyze(prompt)

    async def analyze_chat_sales(self, transcript: str) -> dict[str, Any]:
        """Analisa conversão de vendas."""
        prompt = f"""Você é um analista de vendas para uma equipe comercial.
Analise a transcrição para avaliar o progresso no funil de vendas.

ESTÁGIOS DO FUNIL:
- qualificacao: Validando perfil do cliente
- apresentacao: Demonstrando soluções e benefícios
- negociacao: Discutindo preço, condições, objeções
- fechamento: Agendando próximo passo ou fechando venda

Retorne um objeto JSON com os seguintes campos:
- funnel_stage: "qualificacao", "apresentacao", "negociacao" ou "fechamento"
- outcome: "convertido", "perdido" ou "em_andamento"
- lead_type: tipo de cliente identificado ou "indefinido"
- rejection_reason: se perdido, o motivo principal (senão null)
- next_step: próximo item de ação recomendado
- urgency: "alta", "media" ou "baixa" (urgência do lead)

Transcrição:
{transcript}"""
        return await self.analyze(prompt)

    async def analyze_chat_qa(self, transcript: str) -> dict[str, Any]:
        """Analisa Quality Assurance (QA)."""
        prompt = f"""Você é um analista de QA para uma equipe de vendas.
Avalie se o agente seguiu o script de qualificação corretamente.

PERGUNTAS-CHAVE DO SCRIPT (configure conforme seu negócio):
1. Área de interesse do cliente
2. Tipo de negócio/perfil
3. Localização
4. Situação atual
5. Orçamento disponível
6. Prazo para decisão

Retorne um objeto JSON com os seguintes campos:
- script_adherence: booleano (seguiu o script de qualificação?)
- questions_asked: lista das perguntas-chave que foram feitas
- questions_missing: lista das perguntas-chave que NÃO foram feitas
- response_time_quality: "rapido", "adequado" ou "lento"
- improvement_areas: lista de sugestões de melhoria para o agente
- overall_score: inteiro de 1 a 5 (nota geral do atendimento)

Transcrição:
{transcript}"""
        return await self.analyze(prompt)

    async def analyze_chat_full(self, transcript: str, validate: bool = True) -> dict[str, Any]:
        """
        Executa todas as análises em paralelo com validação opcional.

        Args:
            transcript: Transcrição do chat.
            validate: Se True, valida o output contra schemas Pydantic.

        Returns:
            Dicionário com todas as análises (cx, product, sales, qa).
        """
        from pydantic import ValidationError

        from src.llm_schemas import CXAnalysis, ProductAnalysis, QAAnalysis, SalesAnalysis

        results = await asyncio.gather(
            self.analyze_chat_cx(transcript),
            self.analyze_chat_product(transcript),
            self.analyze_chat_sales(transcript),
            self.analyze_chat_qa(transcript),
        )

        output = {
            "cx": results[0],
            "product": results[1],
            "sales": results[2],
            "qa": results[3],
        }

        if validate:
            schemas = {
                "cx": CXAnalysis,
                "product": ProductAnalysis,
                "sales": SalesAnalysis,
                "qa": QAAnalysis,
            }
            for key, schema_class in schemas.items():
                try:
                    if "error" not in output[key]:
                        schema_class(**output[key])
                except ValidationError as e:
                    logger.warning(f"Validação falhou para {key}: {e.errors()}")
                    output[key]["validation_errors"] = [{"field": err["loc"], "msg": err["msg"]} for err in e.errors()]

        return output
