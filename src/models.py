import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class Organization(BaseModel):
    id: str = Field(alias="_id")
    name: str
    description: Optional[str] = None


class Contact(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    organization: Optional[Organization] = None
    customFields: Optional[Dict[str, Any]] = None


class Agent(BaseModel):
    id: str
    name: str
    email: Optional[str] = None


class MessageSender(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    type: Optional[str] = None


class Message(BaseModel):
    id: str
    body: str
    time: datetime
    readAt: Optional[datetime] = None
    sentBy: Optional[MessageSender] = None
    type: str
    chatId: str

    # Computed fields for analysis
    is_business_hour: bool = False


class ClosedInfo(BaseModel):
    closedAt: datetime
    closedBy: Optional[Agent] = None


class Chat(BaseModel):
    id: str
    number: str
    channel: str
    contact: Contact
    agent: Optional[Agent] = None
    messages: List[Message]
    status: str
    closed: Optional[ClosedInfo] = None
    waitingTime: Optional[int] = None
    tags: Optional[List[Dict[str, Any]]] = None

    # Computed metrics
    duration_seconds: Optional[float] = None
    message_count: int = 0

    @field_validator("number", mode="before")
    @classmethod
    def parse_number(cls, v: Any) -> str:
        """Convert number to string if it's an integer."""
        if isinstance(v, int):
            return str(v)
        return v

    @field_validator("contact", mode="before")
    @classmethod
    def parse_contact(cls, v: Any) -> Any:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("agent", mode="before")
    @classmethod
    def parse_agent(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    @field_validator("messages", mode="before")
    @classmethod
    def parse_messages(cls, v: Any) -> Any:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("closed", mode="before")
    @classmethod
    def parse_closed(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v: Any) -> Any:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v
