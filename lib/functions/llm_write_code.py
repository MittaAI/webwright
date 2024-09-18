from lib.function_wrapper import function_info_decorator
from lib.llm import llm_wrapper
from datetime import datetime
import json

SYS_PROMPT = "Based on the following description, write the requested code:\n\n:"

@function_info_decorator
async def llm_write_code(description: str, olog=None, llm=None) -> dict:
    """
    Generates code based on a given description, utilizing recent context from previous interactions. Always call this function when generate code.

    :param description: A detailed description of the code to be generated.
    :type description: str
    :return: A dictionary containing the success status and the generated code.
    :rtype: dict
    """
    # Add description to prompt:
    olog.add_entry({
        "content": SYS_PROMPT + description,
        "type": "user_query",
        "timestamp": datetime.now().isoformat()
    })
    print(llm.config)
    # Retrieve recent entries
    messages = olog.get_recent_entries(5)
    
    # Call the LLM API
    response = await llm.call_llm_api(messages=messages, service_api="openai", model="o1-preview")
    
    # Extract the generated code from the response
    generated_code = json.dumps(response)

    return {
        "success": True,
        "code": generated_code
    }