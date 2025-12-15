"""
Módulo de modelos de dados Pydantic.

Define a estrutura, validação e tipagem dos dados de entrada, garantindo
consistência e robustez ao processar informações de chats.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class Organization(BaseModel):
    """Representa a organização associada a um contato."""

    id: Optional[str] = Field(None, alias="_id", description="ID único da organização.")
    name: Optional[str] = Field(None, description="Nome da organização.")
    description: Optional[str] = Field(None, description="Descrição da organização.")


class Contact(BaseModel):
    """Representa um contato (cliente) que participa de uma conversa."""

    id: str = Field(description="ID único do contato.")
    name: str = Field(description="Nome do contato.")
    email: Optional[str] = Field(None, description="Email do contato.")
    organization: Optional[Organization] = Field(None, description="Organização associada.")
    customFields: Optional[Dict[str, Any]] = Field(None, description="Campos customizados.")


class Agent(BaseModel):
    """Representa um agente (atendente) do sistema."""

    id: str = Field(description="ID único do agente.")
    name: str = Field(description="Nome do agente.")
    email: Optional[str] = Field(None, description="Email do agente.")


class MessageSender(BaseModel):
    """Representa o remetente de uma mensagem (pode ser agente ou contato)."""

    id: str = Field(description="ID do remetente.")
    name: Optional[str] = Field(None, description="Nome do remetente.")
    email: Optional[str] = Field(None, description="Email do remetente.")
    type: Optional[str] = Field(None, description="Tipo de remetente (ex: 'agent').")


class Message(BaseModel):
    """Representa uma única mensagem dentro de uma conversa."""

    id: str = Field(description="ID único da mensagem.")
    body: str = Field(description="Conteúdo textual da mensagem.")
    time: datetime = Field(description="Data e hora em que a mensagem foi enviada.")
    readAt: Optional[datetime] = Field(None, description="Data e hora da leitura.")
    sentBy: Optional[MessageSender] = Field(None, description="Remetente da mensagem.")
    type: str = Field(description="Tipo da mensagem (ex: 'text').")
    chatId: str = Field(description="ID da conversa à qual a mensagem pertence.")

    # Campo computado para análise posterior
    is_business_hour: bool = Field(False, description="Indica se a mensagem foi enviada em horário comercial.")


class ClosedInfo(BaseModel):
    """Informações sobre o fechamento de uma conversa."""

    closedAt: datetime = Field(description="Data e hora do fechamento.")
    closedBy: Optional[Agent] = Field(None, description="Agente que fechou a conversa.")


class Chat(BaseModel):
    """
    Modelo principal que representa uma conversa completa (chat).
    Inclui validadores para normalizar dados que podem vir como strings JSON.
    """

    id: str = Field(description="ID único da conversa.")
    number: str = Field(description="Número sequencial da conversa.")
    channel: str = Field(description="Canal de origem (ex: 'whatsapp', 'web').")
    contact: Contact = Field(description="Contato participante.")
    agent: Optional[Agent] = Field(None, description="Agente responsável.")
    messages: List[Message] = Field(description="Lista de mensagens da conversa.")
    status: str = Field(description="Status atual (ex: 'open', 'closed').")
    closed: Optional[ClosedInfo] = Field(None, description="Detalhes de fechamento.")
    waitingTime: Optional[int] = Field(None, description="Tempo até primeira resposta humana (segundos).")
    tags: Optional[List[Dict[str, Any]]] = Field(None, description="Tags associadas à conversa.")

    # Novos campos do BigQuery
    pastAgents: Optional[List[Agent]] = Field(None, description="Agentes anteriores que atenderam.")
    firstMessageDate: Optional[datetime] = Field(None, description="Data da primeira mensagem.")
    lastMessageDate: Optional[datetime] = Field(None, description="Data da última mensagem.")
    messagesCount: Optional[int] = Field(None, description="Contagem de mensagens.")
    withBot: Optional[str] = Field(None, description="Se passou pelo bot (true/false).")
    unreadMessages: Optional[str] = Field(None, description="Mensagens não lidas (true/false).")
    octavia_analysis: Optional[str] = Field(None, description="Análise da Octavia IA.")

    # Métricas computadas que podem ser preenchidas durante a análise
    duration_seconds: Optional[float] = Field(None, description="Duração total da conversa em segundos.")
    message_count: int = Field(0, description="Número total de mensagens na conversa.")

    @field_validator("number", mode="before")
    @classmethod
    def parse_number(cls, v: Any) -> str:
        """Garante que o campo 'number' seja sempre uma string."""
        if isinstance(v, int):
            return str(v)
        return v

    # Validadores para campos que podem ser strings JSON no dado de origem
    @field_validator("agent", "closed", "tags", mode="before")
    @classmethod
    def _parse_optional_json_field(cls, v: Any) -> Optional[Any]:
        """
        Converte campos JSON opcionais que são strings, retornando None em caso de erro.
        Isso evita que um erro de parsing em um campo opcional quebre a validação do chat.
        """
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None  # Se o campo opcional for inválido, trate como nulo
        return v

    @field_validator("contact", "messages", mode="before")
    @classmethod
    def _parse_required_json_field(cls, v: Any) -> Any:
        """
        Converte campos JSON obrigatórios que são strings.
        Se o parsing falhar, a validação do Pydantic irá falhar, o que é o esperado.
        """
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}  # Retorna um dict vazio para forçar o erro de validação do Pydantic
        return v
