"""
Configurações centralizadas do projeto.

Carrega variáveis de ambiente e fornece settings tipados.
Para customizar, crie um arquivo .env na raiz do projeto.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

# Carrega variáveis de ambiente do .env
load_dotenv()


@dataclass
class GeminiSettings:
    """Configurações da API Gemini."""

    api_key: Optional[str] = field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
    timeout: int = field(default_factory=lambda: int(os.getenv("GEMINI_TIMEOUT", "60")))
    rate_limit_rpm: int = field(default_factory=lambda: int(os.getenv("GEMINI_RATE_LIMIT", "240")))


@dataclass
class BigQuerySettings:
    """Configurações do BigQuery."""

    project_id: Optional[str] = field(default_factory=lambda: os.getenv("BIGQUERY_PROJECT_ID"))
    dataset_id: Optional[str] = field(default_factory=lambda: os.getenv("BIGQUERY_DATASET_ID"))
    table_id: Optional[str] = field(default_factory=lambda: os.getenv("BIGQUERY_TABLE_ID"))


@dataclass
class CatalogSettings:
    """Configurações do catálogo de produtos (projeto externo)."""

    api_url: Optional[str] = field(default_factory=lambda: os.getenv("CATALOG_API_URL"))
    api_key: Optional[str] = field(default_factory=lambda: os.getenv("CATALOG_API_KEY"))
    cache_ttl_seconds: int = field(default_factory=lambda: int(os.getenv("CATALOG_CACHE_TTL", "3600")))


@dataclass
class Settings:
    """Configurações globais do projeto."""

    gemini: GeminiSettings = field(default_factory=GeminiSettings)
    bigquery: BigQuerySettings = field(default_factory=BigQuerySettings)
    catalog: CatalogSettings = field(default_factory=CatalogSettings)

    # Configurações gerais
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))


# Singleton para uso em todo o projeto
settings = Settings()
