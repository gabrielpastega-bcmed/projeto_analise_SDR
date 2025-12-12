"""
Cliente para integração com a API do Google Gemini.

Este módulo fornece uma classe GeminiClient para análise qualitativa
de conversas usando o modelo Gemini 2.5 Flash.
"""

import asyncio
import json
import os
from typing import Any, Dict, Optional

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class GeminiClient:
    """
    Cliente para a API do Google Gemini.

    Fornece métodos para análise qualitativa de conversas com retry logic
    e parsing de JSON estruturado.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o cliente Gemini.

        Args:
            api_key: Chave de API do Gemini. Se não fornecida, usa GEMINI_API_KEY do ambiente.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY não configurada. Configure no .env ou passe como parâmetro.")

        genai.configure(api_key=self.api_key)
        # Modelo Gemini 2.5 Flash - estável, otimizado para texto
        self.model = genai.GenerativeModel("gemini-2.5-flash")

        # Configuração para respostas JSON estruturadas
        self.generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.3,  # Mais determinístico para análises
        )

    async def analyze(self, prompt: str, max_retries: int = 3) -> Dict[str, Any]:
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
                # Gemini SDK é síncrono, então rodamos em thread separada
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.model.generate_content(
                        prompt,
                        generation_config=self.generation_config,
                    ),
                )

                # Parse da resposta JSON
                result = self._parse_response(response.text)
                return result

            except json.JSONDecodeError as e:
                print(f"Erro ao parsear JSON (tentativa {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return {"error": "Falha ao parsear resposta JSON", "raw": response.text}

            except Exception as e:
                print(f"Erro na chamada Gemini (tentativa {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                else:
                    return {"error": str(e)}

        return {"error": "Máximo de tentativas excedido"}

    def _parse_response(self, text: str) -> Dict[str, Any]:
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

    async def analyze_chat_cx(self, transcript: str) -> Dict[str, Any]:
        """Analisa experiência do cliente (CX)."""
        prompt = f"""Analise a transcrição de chat a seguir sob a ótica de Experiência do Cliente (CX).
Retorne um objeto JSON com os seguintes campos:
- sentiment: "positivo", "neutro" ou "negativo"
- humanization_score: um inteiro de 1 (robótico) a 5 (muito humano/personalizado)
- nps_prediction: um inteiro de 0 a 10 (probabilidade de recomendação)
- resolution_status: "resolvido", "não resolvido" ou "pendente"
- satisfaction_comment: Uma breve explicação sobre o sentimento.

Transcrição:
{transcript}"""
        return await self.analyze(prompt)

    async def analyze_chat_product(self, transcript: str) -> Dict[str, Any]:
        """Analisa inteligência de produto."""
        prompt = f"""Analise a transcrição de chat a seguir para Inteligência de Produto.
Retorne um objeto JSON com os seguintes campos:
- products_mentioned: Lista de strings (nomes de produtos, tecnologias)
- interest_level: "alto", "médio" ou "baixo"
- trends: Lista de strings (necessidades emergentes, perguntas específicas)

Transcrição:
{transcript}"""
        return await self.analyze(prompt)

    async def analyze_chat_sales(self, transcript: str) -> Dict[str, Any]:
        """Analisa conversão de vendas."""
        prompt = f"""Analise a transcrição de chat a seguir para Conversão de Vendas.
Retorne um objeto JSON com os seguintes campos:
- funnel_stage: "consciência", "consideração" ou "decisão"
- outcome: "convertido", "perdido" ou "em andamento"
- rejection_reason: Se perdido, o motivo principal. Se não, nulo.
- next_step: Qual é o próximo item de ação?

Transcrição:
{transcript}"""
        return await self.analyze(prompt)

    async def analyze_chat_qa(self, transcript: str) -> Dict[str, Any]:
        """Analisa Quality Assurance (QA)."""
        prompt = f"""Analise a transcrição de chat a seguir para Quality Assurance (QA).
Retorne um objeto JSON com os seguintes campos:
- script_adherence: booleano (o agente fez as perguntas-chave de qualificação?)
- key_questions_asked: Lista de strings (ex: "Clínica ou PF?", "Localização?")
- improvement_areas: Lista de strings (o que o agente poderia fazer melhor?)

Transcrição:
{transcript}"""
        return await self.analyze(prompt)

    async def analyze_chat_full(self, transcript: str) -> Dict[str, Any]:
        """
        Executa todas as análises em paralelo.

        Args:
            transcript: Transcrição do chat.

        Returns:
            Dicionário com todas as análises (cx, product, sales, qa).
        """
        results = await asyncio.gather(
            self.analyze_chat_cx(transcript),
            self.analyze_chat_product(transcript),
            self.analyze_chat_sales(transcript),
            self.analyze_chat_qa(transcript),
        )

        return {
            "cx": results[0],
            "product": results[1],
            "sales": results[2],
            "qa": results[3],
        }
