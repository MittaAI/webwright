from datetime import datetime
from omnilog import OmniLogVectorStore
import json

def print_entries(entries, title):
    print(f"\n{title}")
    print("=" * len(title))
    for entry in entries:
        print(f"Type: {entry['type']}")
        print(f"Timestamp: {entry['timestamp']}")
        if entry['type'] == 'tool_call':
            print(f"Tool: {entry['content']['tool']}")
            print(f"Parameters: {json.dumps(entry['content']['parameters'], indent=2)}")
        elif entry['type'] == 'llm_response':
            print(f"Content: {entry['content'][:100]}...")  # Truncate long responses
        else:
            print(f"Content: {entry['content']}")
        print("-" * 50)

def main():
    store = OmniLogVectorStore()  # This will use a temporary directory
    
    # Sample entries including tool calls and LLM responses
    entries = [
        {
            "content": {
                "tool": "weather_api",
                "parameters": {
                    "location": "New York",
                    "date": "2023-08-15"
                }
            },
            "timestamp": "2023-08-15T09:00:00",
            "type": "tool_call"
        },
        {
            "content": "The weather in New York on 2023-08-15 is sunny with a high of 28°C (82°F) and a low of 20°C (68°F).",
            "timestamp": "2023-08-15T09:00:05",
            "type": "llm_response"
        },
        {
            "content": "What are some popular tourist attractions in New York?",
            "timestamp": "2023-08-15T10:00:00",
            "type": "user_query"
        },
        {
            "content": "Some popular tourist attractions in New York include:\n1. Statue of Liberty\n2. Empire State Building\n3. Central Park\n4. Times Square\n5. Metropolitan Museum of Art\n6. Broadway shows\n7. 9/11 Memorial & Museum\n8. High Line\n9. Rockefeller Center\n10. Brooklyn Bridge",
            "timestamp": "2023-08-15T10:00:10",
            "type": "llm_response"
        },
        {
            "content": {
                "tool": "restaurant_recommendation",
                "parameters": {
                    "cuisine": "Italian",
                    "location": "Manhattan",
                    "price_range": "$$"
                }
            },
            "timestamp": "2023-08-15T13:00:00",
            "type": "tool_call"
        },
        {
            "content": "Based on your preferences, I recommend 'Piccola Cucina Osteria' in Manhattan. It's a highly-rated Italian restaurant with a cozy atmosphere and authentic dishes at a moderate price point.",
            "timestamp": "2023-08-15T13:00:05",
            "type": "llm_response"
        },
        {
            "content": "Can you help me plan a day trip to the Statue of Liberty?",
            "timestamp": "2023-08-16T09:00:00",
            "type": "user_query"
        },
        {
            "content": "Certainly! Here's a suggested itinerary for a day trip to the Statue of Liberty:\n1. Start early: Book a morning ferry to Liberty Island.\n2. Visit the Statue of Liberty Museum on the island.\n3. Take the audio tour around the statue's base.\n4. If you have crown access tickets, climb to the crown.\n5. Take the ferry to Ellis Island and visit the Immigration Museum.\n6. Return to Battery Park and explore the surrounding area.\n\nRemember to book your tickets in advance, especially if you want crown access!",
            "timestamp": "2023-08-16T09:00:15",
            "type": "llm_response"
        }
    ]
    
    # Add sample entries to the store
    for entry in entries:
        store.add_entry(entry)

    # Get recent entries
    recent_entries = store.get_recent_entries(5)
    print_entries(recent_entries, "5 Most Recent Entries")

    # Search entries
    search_query = "New York"
    search_results = store.search_entries(search_query, 3)
    print_entries(search_results, f"Top 3 Entries for Search Query: '{search_query}'")

    # Search by date range
    start_date = datetime(2023, 8, 15)
    end_date = datetime(2023, 8, 15, 23, 59, 59)
    date_range_results = store.search_by_date_range(start_date, end_date)
    print_entries(date_range_results, f"Entries from {start_date.date()}")

    # Search by type
    type_query = "tool_call"
    type_results = store.search_by_type(type_query)
    print_entries(type_results, f"Entries of Type: '{type_query}'")

    # Build OmniLog
    omnilog = store.build_omnilog(recent_count=3, query="Statue of Liberty", top_k=2)
    print_entries(omnilog, "OmniLog: 3 Recent Entries + 2 Similar to 'Statue of Liberty'")

if __name__ == "__main__":
    main()