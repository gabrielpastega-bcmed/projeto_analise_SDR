"""
Schemas Pydantic para validação de output do LLM.

Define estruturas esperadas para cada tipo de análise
(CX, Product, Sales, QA) com validação automática.
"""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class CXAnalysis(BaseModel):
    """Schema para análise de Customer Experience."""

    sentiment: Literal["positivo", "neutro", "negativo"] = Field(
        description="Sentimento geral do cliente"
    )
    humanization_score: int = Field(ge=1, le=5, description="Score de humanização 1-5")
    nps_prediction: int = Field(ge=0, le=10, description="Previsão de NPS 0-10")
    resolution_status: Literal[
        "resolvido", "nao_resolvido", "não_resolvido", "pendente"
    ] = Field(description="Status de resolução")
    personalization_used: bool = Field(description="Se usou nome do cliente")
    satisfaction_comment: str = Field(description="Comentário sobre satisfação")


class ProductAnalysis(BaseModel):
    """Schema para análise de inteligência de produto."""

    products_mentioned: List[str] = Field(
        default_factory=list, description="Produtos mencionados"
    )
    category: str = Field(
        description="Categoria de produto (ex: categoria_a, categoria_b, hof, misto, indefinido)"
    )
    interest_level: Literal["alto", "medio", "baixo"] = Field(
        description="Nível de interesse"
    )
    budget_mentioned: bool = Field(description="Se mencionou orçamento")
    trends: List[str] = Field(
        default_factory=list, description="Tendências identificadas"
    )


class SalesAnalysis(BaseModel):
    """Schema para analise de qualificacao SDR."""

    funnel_stage: Literal[
        "qualificacao", "apresentacao", "negociacao", "encaminhamento", "fechamento"
    ] = Field(description="Estagio do funil SDR")
    outcome: Literal[
        "qualificado", "nao_qualificado", "convertido", "perdido", "em_andamento"
    ] = Field(description="Resultado da qualificacao")
    lead_type: str = Field(
        description="Tipo de lead/cliente (livre, definido conforme conversa)"
    )
    rejection_reason: Optional[str] = Field(None, description="Motivo de rejeição")
    next_step: str = Field(description="Próximo passo recomendado")
    urgency: Literal["alta", "media", "baixa"] = Field(description="Urgência do lead")


class QAAnalysis(BaseModel):
    """Schema para análise de Quality Assurance."""

    script_adherence: bool = Field(description="Se seguiu o script")
    questions_asked: List[str] = Field(
        default_factory=list, description="Perguntas feitas"
    )
    questions_missing: List[str] = Field(
        default_factory=list, description="Perguntas faltantes"
    )
    response_time_quality: Literal["rapido", "adequado", "lento"] = Field(
        description="Qualidade do tempo de resposta"
    )
    improvement_areas: List[str] = Field(
        default_factory=list, description="Áreas de melhoria"
    )
    overall_score: int = Field(ge=1, le=5, description="Score geral 1-5")


class FullAnalysis(BaseModel):
    """Schema completo para análise de chat."""

    cx: CXAnalysis
    product: ProductAnalysis
    sales: SalesAnalysis
    qa: QAAnalysis


class AnalysisError(BaseModel):
    """Schema para erros de análise."""

    error: str = Field(description="Mensagem de erro")
    raw: Optional[str] = Field(None, description="Resposta bruta do LLM")
