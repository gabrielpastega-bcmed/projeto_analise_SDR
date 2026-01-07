import os
import sys

# Add src to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv

load_dotenv()

from src.dashboard_utils import get_lead_status
from src.ingestion import load_analysis_results_from_postgres
from src.models import Chat

# Mock chat object structure based on BigQuery
# Using an ID we know exists in Postgres from previous steps: 38e407b3-a047-42a8-baa2-b1fb696e6a67 (Qualificado)
mock_chat_data = {
    "id": "38e407b3-a047-42a8-baa2-b1fb696e6a67",
    "number": "123",
    "channel": "whatsapp",
    "contact": {"id": "c1", "name": "Test Contact"},
    "agent": {"id": "a1", "name": "Test Agent"},
    "messages": [],
    "status": "closed",
    "tags": [{"name": "Procedimento"}],
}


def verify_logic():
    print("--- Verifying Dashboard Logic ---")

    # 1. Simulate Chat Loading
    try:
        chat = Chat(**mock_chat_data)
        chats = [chat]
        print(f"Loaded {len(chats)} chats.")
    except Exception as e:
        print(f"Failed to create Chat object: {e}")
        return

    # 2. Load Analysis from Postgres
    chat_ids = [c.id for c in chats]
    print(f"Fetching analysis for IDs: {chat_ids}")

    analysis_results = load_analysis_results_from_postgres(chat_ids)
    print(f"Found analysis for {len(analysis_results)} chats.")

    # 3. Enrich Chats
    if analysis_results:
        for c in chats:
            if c.id in analysis_results:
                result = analysis_results[c.id]
                c.sales_outcome = result.get("sales_outcome")
                c.sales_stage = result.get("sales_stage")
                c.qa_score = result.get("qa_score")
                print(f"Enriched Chat {c.id}:")
                print(f"  - Sales Outcome: {c.sales_outcome}")
                print(f"  - QA Score: {c.qa_score}")

    # 4. Check Lead Status Logic
    status = get_lead_status(chat)
    print(f"Lead Status (get_lead_status): {status}")

    # We expect 'qualificado' because sales_outcome='qualificado' (checked previously)
    # Even if tags are 'Procedimento' (which maps to 'Outro')

    if chat.sales_outcome == "qualificado" and status == "qualificado":
        print(
            "[OK] SUCCESS: Lead status correctly matches sales_outcome 'qualificado'."
        )
    elif chat.sales_outcome == "nao_qualificado" and status == "nao_qualificado":
        print(
            "[OK] SUCCESS: Lead status correctly matches sales_outcome 'nao_qualificado'."
        )
    else:
        print(
            f"[WARN] Warning: Check logic. Outcome={chat.sales_outcome}, Status={status}"
        )


if __name__ == "__main__":
    verify_logic()
