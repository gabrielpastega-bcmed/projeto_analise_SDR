"""
Testes para os schemas de validação LLM.
"""

import pytest
from pydantic import ValidationError

from src.llm_schemas import (
    CXAnalysis,
    ProductAnalysis,
    QAAnalysis,
    SalesAnalysis,
)


class TestCXAnalysis:
    """Testes para CXAnalysis schema."""

    def test_valid_cx(self):
        """Testa CX válido."""
        data = {
            "sentiment": "positivo",
            "humanization_score": 4,
            "nps_prediction": 8,
            "resolution_status": "resolvido",
            "personalization_used": True,
            "satisfaction_comment": "Cliente satisfeito",
        }
        cx = CXAnalysis.model_validate(data)
        assert cx.sentiment == "positivo"
        assert cx.humanization_score == 4

    def test_invalid_sentiment(self):
        """Testa sentimento inválido."""
        data = {
            "sentiment": "muito_positivo",  # Inválido
            "humanization_score": 4,
            "nps_prediction": 8,
            "resolution_status": "resolvido",
            "personalization_used": True,
            "satisfaction_comment": "ok",
        }
        with pytest.raises(ValidationError):
            CXAnalysis.model_validate(data)

    def test_invalid_score_range(self):
        """Testa score fora do range."""
        data = {
            "sentiment": "positivo",
            "humanization_score": 10,  # Max é 5
            "nps_prediction": 8,
            "resolution_status": "resolvido",
            "personalization_used": True,
            "satisfaction_comment": "ok",
        }
        with pytest.raises(ValidationError):
            CXAnalysis.model_validate(data)


class TestProductAnalysis:
    """Testes para ProductAnalysis schema."""

    def test_valid_product(self):
        """Testa produto válido."""
        data = {
            "products_mentioned": ["equipamento_a", "ultrassom"],
            "category": "categoria_a",
            "interest_level": "alto",
            "budget_mentioned": True,
            "trends": ["remoção de tatuagem"],
        }
        product = ProductAnalysis.model_validate(data)
        assert product.category == "categoria_a"
        assert len(product.products_mentioned) == 2

    def test_indefinido_category(self):
        """Testa categoria indefinido."""
        data = {
            "products_mentioned": [],
            "category": "indefinido",
            "interest_level": "baixo",
            "budget_mentioned": False,
            "trends": [],
        }
        product = ProductAnalysis.model_validate(data)
        assert product.category == "indefinido"


class TestSalesAnalysis:
    """Testes para SalesAnalysis schema."""

    def test_valid_sales(self):
        """Testa venda válida."""
        data = {
            "funnel_stage": "qualificacao",
            "outcome": "em_andamento",
            "lead_type": "tipo_cliente",
            "rejection_reason": None,
            "next_step": "Agendar demo",
            "urgency": "alta",
        }
        sales = SalesAnalysis.model_validate(data)
        assert sales.funnel_stage == "qualificacao"

    def test_with_rejection(self):
        """Testa venda perdida com motivo."""
        data = {
            "funnel_stage": "negociacao",
            "outcome": "perdido",
            "lead_type": "autonomo",
            "rejection_reason": "Preço alto",
            "next_step": "Follow-up em 30 dias",
            "urgency": "baixa",
        }
        sales = SalesAnalysis.model_validate(data)
        assert sales.rejection_reason == "Preço alto"


class TestQAAnalysis:
    """Testes para QAAnalysis schema."""

    def test_valid_qa(self):
        """Testa QA válido."""
        data = {
            "script_adherence": True,
            "questions_asked": ["Área de atuação", "Tipo de negócio"],
            "questions_missing": ["Orçamento"],
            "response_time_quality": "adequado",
            "improvement_areas": ["Perguntar sobre prazo"],
            "overall_score": 4,
        }
        qa = QAAnalysis.model_validate(data)
        assert qa.overall_score == 4
        assert len(qa.questions_asked) == 2
