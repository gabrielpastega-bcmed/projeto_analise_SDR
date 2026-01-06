"""
Cliente para integração com a API do Google Gemini.

Este módulo fornece uma classe GeminiClient para análise qualitativa
de conversas usando o modelo Gemini 3 Flash Preview.

Migrado para google-genai SDK (substitui google-generativeai deprecado).
"""

import asyncio
import json
import os
from pathlib import Path
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
            api_key: Chave de API do Gemini. Se nao fornecida, usa GEMINI_API_KEY do ambiente.
            timeout: Timeout em segundos para cada chamada à API.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY nao configurada. Configure no .env ou passe como parâmetro."
            )

        # Novo SDK: usa Client() ao invés de configure()
        self.client = genai.Client(api_key=self.api_key)

        # Modelo Gemini 3 Flash Preview - novo modelo otimizado
        self.model_name = "gemini-3-flash-preview"

        # Configuração para respostas JSON estruturadas
        self.generation_config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.3,  # Mais determinístico para análises
        )
        logger.info(
            f"GeminiClient inicializado (timeout={timeout}s, model={self.model_name})"
        )

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
                    response = await asyncio.get_running_loop().run_in_executor(
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
                    return {
                        "error": "Falha ao parsear resposta JSON",
                        "raw": response.text,
                    }

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

    def _load_prompt(self, name: str) -> str:
        """
        Load prompt template from config/prompts/{name}.txt.

        Args:
            name: Name of the prompt file (without .txt extension)

        Returns:
            Prompt template string with {transcript} placeholder

        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        prompt_path = (
            Path(__file__).parent.parent / "config" / "prompts" / f"{name}.txt"
        )
        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}. "
                f"Copy from {name}.example.txt and customize."
            )
        return prompt_path.read_text(encoding="utf-8")

    async def analyze_chat_cx(self, transcript: str) -> dict[str, Any]:
        """Analisa experiência do cliente (CX)."""
        prompt_template = self._load_prompt("cx_analysis")
        prompt = prompt_template.format(transcript=transcript)
        return await self.analyze(prompt)

    async def analyze_chat_product(self, transcript: str) -> dict[str, Any]:
        """Analisa inteligência de produto."""
        prompt_template = self._load_prompt("product_analysis")
        prompt = prompt_template.format(transcript=transcript)
        return await self.analyze(prompt)

    async def analyze_chat_sales(self, transcript: str) -> dict[str, Any]:
        """Analisa qualificacao de leads pelo SDR."""
        prompt_template = self._load_prompt("sales_analysis")
        prompt = prompt_template.format(transcript=transcript)
        return await self.analyze(prompt)

    async def analyze_chat_qa(self, transcript: str) -> dict[str, Any]:
        """Analisa Quality Assurance do atendimento SDR."""
        prompt_template = self._load_prompt("qa_analysis")
        prompt = prompt_template.format(transcript=transcript)
        return await self.analyze(prompt)

    async def analyze_chat_full(
        self, transcript: str, validate: bool = True
    ) -> dict[str, Any]:
        """
        Executa todas as análises em paralelo com validacao opcional.

        Args:
            transcript: Transcrição do chat.
            validate: Se True, valida o output contra schemas Pydantic.

        Returns:
            Dicionário com todas as análises (cx, product, sales, qa).
        """
        from pydantic import ValidationError

        from src.llm_schemas import (
            CXAnalysis,
            ProductAnalysis,
            QAAnalysis,
            SalesAnalysis,
        )

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
                    logger.warning(f"Validacao falhou para {key}: {e.errors()}")
                    output[key]["validation_errors"] = [
                        {"field": err["loc"], "msg": err["msg"]} for err in e.errors()
                    ]

        return output
