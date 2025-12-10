import asyncio
import json

from src.ingestion import load_chats_from_json
from src.llm_analysis import LLMAnalyzer
from src.ops_analysis import calculate_response_times
from src.reporting import generate_report


async def main():
    # 1. Load Data
    file_path = "data/raw/exemplo.json"
    print(f"Loading data from {file_path}...")
    chats = load_chats_from_json(file_path)
    print(f"Loaded {len(chats)} chats.")

    # 2. Initialize Analyzer
    llm_analyzer = LLMAnalyzer()

    # 3. Process Chats
    processed_data = []
    print("Starting analysis pipeline...")

    for chat in chats:
        # Ops Analysis
        ops_metrics = calculate_response_times(chat)

        # LLM Analysis
        llm_results = await llm_analyzer.analyze_chat(chat)

        processed_data.append({
            "chat_id": chat.id,
            "agent_name": chat.agent.name if chat.agent else "Unknown",
            "ops_metrics": ops_metrics,
            "llm_results": llm_results
        })

    # 4. Generate Report
    print("Generating report...")
    report = generate_report(processed_data)

    # 5. Output Results
    print("\n=== FINAL REPORT ===")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Save to file
    with open("analysis_report.json", "w", encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("\nReport saved to analysis_report.json")

if __name__ == "__main__":
    asyncio.run(main())
