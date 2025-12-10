from typing import Any, Dict

from src.models import Chat

# Prompts defined as constants
PROMPT_CX = """
Analyze the following chat transcript for Customer Experience (CX).
Return a JSON object with the following fields:
- sentiment: "positive", "neutral", or "negative"
- humanization_score: integer from 1 (robotic) to 5 (very human/personalized)
- resolution_status: "resolved", "unresolved", or "pending"
- satisfaction_comment: Brief explanation of the sentiment.

Transcript:
{transcript}
"""

PROMPT_PRODUCT = """
Analyze the following chat transcript for Product Intelligence.
Return a JSON object with the following fields:
- products_mentioned: List of strings (product names, technologies)
- interest_level: "high", "medium", or "low"
- trends: List of strings (emerging needs, specific questions)

Transcript:
{transcript}
"""

PROMPT_SALES = """
Analyze the following chat transcript for Sales Conversion.
Return a JSON object with the following fields:
- outcome: "converted", "lost", or "in_progress"
- rejection_reason: If lost, provide the main reason (e.g., "price", "stock",
  "competitor", "no_response"). If not lost, null.
- next_step: What is the next action item?

Transcript:
{transcript}
"""

class LLMAnalyzer:
    def __init__(self, api_key: str = "mock_key"):
        self.api_key = api_key

    def _format_transcript(self, chat: Chat) -> str:
        lines = []
        for msg in chat.messages:
            sender = "Agent" if (msg.sentBy and msg.sentBy.type == 'agent') else "Customer"
            # Simple HTML tag removal if needed, but LLMs handle it fine usually
            body = msg.body.replace("<p>", "").replace("</p>", "").replace("<br>", "\n")
            lines.append(f"{sender} ({msg.time}): {body}")
        return "\n".join(lines)

    async def analyze_chat(self, chat: Chat) -> Dict[str, Any]:
        """
        Orchestrates the analysis by calling the LLM with different prompts.
        For now, this returns MOCK data to demonstrate the structure.
        """
        transcript = self._format_transcript(chat)

        # In a real implementation, we would make parallel calls to the LLM here.
        # response_cx = await self._call_llm(PROMPT_CX.format(transcript=transcript))
        # response_product = await self._call_llm(PROMPT_PRODUCT.format(transcript=transcript))
        # response_sales = await self._call_llm(PROMPT_SALES.format(transcript=transcript))

        # Mocking the response based on the "exemplo.json" content we know
        # The example chat is about "Produto A", customer asks price/conditions,
        # agent sends contact info, customer stops responding? Or conversation ends.

        return {
            "cx": {
                "sentiment": "neutral",
                "humanization_score": 4,
                "resolution_status": "resolved", # Agent gave info
                "satisfaction_comment": "Customer received the requested information."
            },
            "product": {
                "products_mentioned": ["Produto A", "Produto B"],
                "interest_level": "high",
                "trends": ["Private label results"]
            },
            "sales": {
                "outcome": "in_progress",
                "rejection_reason": None,
                "next_step": "Specialist contact"
            }
        }

    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """
        Placeholder for actual HTTP call to LLM provider (OpenAI/Gemini).
        """
        # import httpx
        # async with httpx.AsyncClient() as client:
        #     resp = await client.post(...)
        #     return resp.json()
        return {}
