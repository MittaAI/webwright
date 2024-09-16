# lib/functions/search.py

from lib.function_wrapper import function_info_decorator
from lib.llm import llm_wrapper

@function_info_decorator
def search(search_term: str, olog=None) -> dict:
    """
    Uses an instance of Omnilog class defined in aifunc.py to search for entries with context.
    Use this function to search historic chat entries for a specific term.
    
    :param search_term: The term to search for.
    :type search_term: str
    :return: A dictionary containing search results.
    :rtype: dict
    """
    results = olog.search_entries_with_context(search_term)

    return {
        "success": True,
        "results": results
    }
