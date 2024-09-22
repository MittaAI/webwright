# lib/functions/search.py

from lib.function_wrapper import function_info_decorator
from lib.llm import llm_wrapper

@function_info_decorator
def search(search_term: str, top_k: int, olog=None) -> dict:
    """
    Uses an instance of Omnilog class defined in aifunc.py to search local memory for entries with context.
    Use this function to search historic chat entries and memories for a specific term.
    
    :param search_term: The term to use to search local memories.
    :type search_term: str

    :param top_k: The number of results to return.
    :type top_k: int
    
    :return: A dictionary containing local memory search results in a prompt format.
    :rtype: dict
    """

    # Use the search_entries_with_context method to search
    results = olog.search_entries_with_context(search_term)

    response = f"""
Search function results for '{search_term}':

This is a search of our conversation history and local memory, not a web search.

'''json
{results}
'''

Note:
- These results come from our previous conversations and locally stored information.
- They represent memories of past interactions, not current web data.
- Each result includes the found entry and its adjacent entry for context.
- This search may not include all mentions of the term in our conversation history.

Suggestion:
To explore further, you could try searching for related terms or ask about specific aspects of '{search_term}' from our past discussions.

You can perform additional local memory searches to find related or unrelated mentions from our conversation history.
"""

    return {
        "success": True,
        "results": response
    }