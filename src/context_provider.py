"""
Provedor de contexto empresarial para prompts LLM.

Este módulo fornece uma interface abstrata para obter informações
de produtos, categorias e tecnologias que serão injetadas nos prompts.

Por padrão, retorna contexto genérico. Quando integrado ao projeto
catalogo_bcmed, retornará dados reais da empresa.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

from config.settings import settings


@dataclass
class Category:
    """Representa uma categoria de produto."""

    id: str
    name: str
    keywords: List[str] = field(default_factory=list)


@dataclass
class Product:
    """Representa um produto do catálogo."""

    id: str
    name: str
    category_id: str
    technologies: List[str] = field(default_factory=list)


@dataclass
class CompanyContext:
    """Contexto empresarial completo para prompts."""

    company_name: str
    segment: str
    categories: List[Category]
    products: List[Product]
    sdr_questions: List[str]


class ContextProvider(ABC):
    """Interface abstrata para provedores de contexto."""

    @abstractmethod
    async def get_context(self) -> CompanyContext:
        """Retorna o contexto empresarial completo."""
        pass

    @abstractmethod
    async def get_categories(self) -> List[Category]:
        """Retorna lista de categorias."""
        pass

    @abstractmethod
    async def get_products(self, category_id: Optional[str] = None) -> List[Product]:
        """Retorna lista de produtos, opcionalmente filtrada por categoria."""
        pass


class DefaultContextProvider(ContextProvider):
    """
    Provedor de contexto padrão com dados genéricos.

    Use esta implementação para desenvolvimento ou quando o
    catálogo externo não estiver disponível.
    """

    async def get_context(self) -> CompanyContext:
        return CompanyContext(
            company_name="Empresa de Equipamentos",
            segment="Equipamentos comerciais",
            categories=await self.get_categories(),
            products=await self.get_products(),
            sdr_questions=[
                "Área de interesse",
                "Tipo de negócio",
                "Localização",
                "Situação atual",
                "Orçamento disponível",
                "Prazo para decisão",
            ],
        )

    async def get_categories(self) -> List[Category]:
        return [
            Category(id="categoria_a", name="Categoria A", keywords=["produto_1", "produto_2"]),
            Category(id="categoria_b", name="Categoria B", keywords=["produto_3", "produto_4"]),
            Category(id="categoria_c", name="Categoria C", keywords=["produto_5", "produto_6"]),
        ]

    async def get_products(self, category_id: Optional[str] = None) -> List[Product]:
        products = [
            Product(id="prod_1", name="Produto A", category_id="categoria_a", technologies=["tech_1"]),
            Product(id="prod_2", name="Produto B", category_id="categoria_a", technologies=["tech_2"]),
            Product(id="prod_3", name="Produto C", category_id="categoria_b", technologies=["tech_3"]),
        ]
        if category_id:
            return [p for p in products if p.category_id == category_id]
        return products


class CatalogAPIContextProvider(ContextProvider):
    """
    Provedor de contexto que busca dados do projeto catalogo_bcmed.

    Esta implementação será usada em produção, quando o catálogo
    externo estiver configurado via CATALOG_API_URL.
    """

    def __init__(self, api_url: Optional[str] = None, api_key: Optional[str] = None):
        self.api_url = api_url or settings.catalog.api_url
        self.api_key = api_key or settings.catalog.api_key
        self._cache: Optional[CompanyContext] = None

    async def get_context(self) -> CompanyContext:
        # TODO: Implementar chamada real à API quando catalogo_bcmed estiver pronto
        # Por enquanto, delega para o provider padrão
        default = DefaultContextProvider()
        return await default.get_context()

    async def get_categories(self) -> List[Category]:
        context = await self.get_context()
        return context.categories

    async def get_products(self, category_id: Optional[str] = None) -> List[Product]:
        context = await self.get_context()
        if category_id:
            return [p for p in context.products if p.category_id == category_id]
        return context.products


def get_context_provider() -> ContextProvider:
    """
    Factory que retorna o provider apropriado baseado na configuração.

    Se CATALOG_API_URL estiver configurada, retorna CatalogAPIContextProvider.
    Caso contrário, retorna DefaultContextProvider.
    """
    if settings.catalog.api_url:
        return CatalogAPIContextProvider()
    return DefaultContextProvider()
