import asyncio
import logging
from datetime import datetime
from omnilog import OmniLogVectorStore

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def mock_ai_function(messages):
    return {
        "response": "This is a mock AI response based on the provided messages.",
        "function_calls": [
            {
                "name": "mock_function",
                "arguments": {"arg1": "value1", "arg2": "value2"}
            }
        ]
    }

async def test_omnilog_integration():
    store = OmniLogVectorStore()

    # Add some sample entries
    entries = [
        {"content": "What's the weather like in New York?", "timestamp": "2023-08-15T09:00:00", "type": "user"},
        {"content": "The weather in New York is sunny with a high of 28°C.", "timestamp": "2023-08-15T09:00:10", "type": "assistant"},
        {"content": "What are some popular tourist attractions in New York?", "timestamp": "2023-08-15T10:00:00", "type": "user"},
        {"content": "Some popular attractions include the Statue of Liberty, Central Park, and Times Square.", "timestamp": "2023-08-15T10:00:10", "type": "assistant"},
    ]

    for entry in entries:
        store.add_entry(entry)

    new_query = "Tell me more about the Statue of Liberty"

    context = store.build_omnilog_with_context(recent_count=4, query=new_query, top_k=2)

    logger.debug("Context from OmniLog:")
    for entry in context:
        logger.debug(f"Type: {entry['type']} - Content: {entry['content'][:50]}...")

    messages = [{"role": entry['type'], "content": entry['content']} for entry in context]

    logger.debug("Processed messages:")
    for msg in messages:
        logger.debug(f"Role: {msg['role']}, Content: {msg['content'][:50]}...")

    ai_response = await mock_ai_function(messages)

    print("\nContext provided to AI:")
    for msg in messages:
        print(f"Role: {msg['role']}, Content: {msg['content'][:50]}...")

    print("\nAI Response:")
    print(ai_response["response"])

    print("\nFunction Calls:")
    for func_call in ai_response.get("function_calls", []):
        print(f"Function: {func_call['name']}")
        print(f"Arguments: {func_call['arguments']}")

    # Add AI response to the store
    store.add_entry({
        "content": ai_response["response"],
        "timestamp": datetime.now().isoformat(),
        "type": "assistant"
    })

    # Add function call to the store
    for func_call in ai_response.get("function_calls", []):
        store.add_entry({
            "content": {
                "tool": func_call["name"],
                "parameters": func_call["arguments"]
            },
            "timestamp": datetime.now().isoformat(),
            "type": "function"
        })

    print("\nRecent entries after AI response:")
    recent_entries = store.get_recent_entries(5)
    for entry in recent_entries:
        content_preview = entry['content'][:50] if isinstance(entry['content'], str) else str(entry['content'])[:50]
        print(f"Type: {entry['type']}, Timestamp: {entry['timestamp']}, Content: {content_preview}...")

if __name__ == "__main__":
    asyncio.run(test_omnilog_integration())