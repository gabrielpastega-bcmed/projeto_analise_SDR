"""
Test script to verify BigQuery connection.
"""

from src.ingestion import get_data_source, load_chats_from_bigquery

if __name__ == "__main__":
    print("=" * 60)
    print("Testing BigQuery Connection")
    print("=" * 60)

    # Check data source
    source = get_data_source()
    print(f"\nConfigured data source: {source}")

    if source != "bigquery":
        print("ERROR: BigQuery is not configured. Check your .env file.")
        exit(1)

    # Test connection with limit
    print("\nLoading first 5 chats as test...")
    try:
        chats = load_chats_from_bigquery(days=7, limit=5)
        print(f"\n✅ SUCCESS! Loaded {len(chats)} chats")

        if chats:
            print("\nSample chat:")
            chat = chats[0]
            print(f"  ID: {chat.id}")
            print(f"  Contact: {chat.contact.name}")
            print(f"  Agent: {chat.agent.name if chat.agent else 'N/A'}")
            print(f"  Messages: {len(chat.messages)}")
            print(f"  Status: {chat.status}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
