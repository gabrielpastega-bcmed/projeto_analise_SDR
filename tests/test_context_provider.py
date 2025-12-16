"""Tests for context_provider module."""

import pytest

from src.context_provider import (
    CatalogAPIContextProvider,
    Category,
    CompanyContext,
    DefaultContextProvider,
    Product,
    get_context_provider,
)


class TestCategory:
    """Tests for Category dataclass."""

    def test_category_creation(self) -> None:
        cat = Category(id="test", name="Test Category", keywords=["a", "b"])
        assert cat.id == "test"
        assert cat.name == "Test Category"
        assert cat.keywords == ["a", "b"]

    def test_category_default_keywords(self) -> None:
        cat = Category(id="test", name="Test")
        assert cat.keywords == []


class TestProduct:
    """Tests for Product dataclass."""

    def test_product_creation(self) -> None:
        prod = Product(id="p1", name="Product 1", category_id="cat1", technologies=["tech1"])
        assert prod.id == "p1"
        assert prod.name == "Product 1"
        assert prod.category_id == "cat1"
        assert prod.technologies == ["tech1"]


class TestDefaultContextProvider:
    """Tests for DefaultContextProvider."""

    @pytest.mark.asyncio
    async def test_get_context(self) -> None:
        provider = DefaultContextProvider()
        context = await provider.get_context()

        assert isinstance(context, CompanyContext)
        assert context.company_name == "Empresa de Equipamentos"
        assert len(context.categories) > 0
        assert len(context.products) > 0
        assert len(context.sdr_questions) > 0

    @pytest.mark.asyncio
    async def test_get_categories(self) -> None:
        provider = DefaultContextProvider()
        categories = await provider.get_categories()

        assert len(categories) == 3
        assert all(isinstance(c, Category) for c in categories)

    @pytest.mark.asyncio
    async def test_get_products(self) -> None:
        provider = DefaultContextProvider()
        products = await provider.get_products()

        assert len(products) == 3
        assert all(isinstance(p, Product) for p in products)

    @pytest.mark.asyncio
    async def test_get_products_by_category(self) -> None:
        provider = DefaultContextProvider()
        products = await provider.get_products(category_id="categoria_a")

        assert len(products) == 2
        assert all(p.category_id == "categoria_a" for p in products)


class TestCatalogAPIContextProvider:
    """Tests for CatalogAPIContextProvider."""

    @pytest.mark.asyncio
    async def test_get_context_fallback(self) -> None:
        """Should fall back to default provider when API not configured."""
        provider = CatalogAPIContextProvider()
        context = await provider.get_context()

        assert isinstance(context, CompanyContext)
        assert context.company_name == "Empresa de Equipamentos"

    @pytest.mark.asyncio
    async def test_get_categories(self) -> None:
        provider = CatalogAPIContextProvider()
        categories = await provider.get_categories()

        assert len(categories) > 0

    @pytest.mark.asyncio
    async def test_get_products(self) -> None:
        provider = CatalogAPIContextProvider()
        products = await provider.get_products()

        assert len(products) > 0


class TestGetContextProvider:
    """Tests for get_context_provider factory."""

    def test_returns_default_when_no_catalog_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("CATALOG_API_URL", "")
        provider = get_context_provider()
        assert isinstance(provider, DefaultContextProvider)
