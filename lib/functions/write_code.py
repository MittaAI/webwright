from lib.function_wrapper import function_info_decorator
from lib.llm import llm_wrapper
from datetime import datetime

SYS_PROMPT = "Based on the following description, write the requested code:\n\n:"

@function_info_decorator
async def write_code(description: str, olog) -> dict:
    """
    Generates code based on a given description, utilizing recent context from previous interactions. Always call this function when generate code.

    :param description: A detailed description of the code to be generated.
    :type description: str
    :return: A dictionary containing the success status and the generated code.
    :rtype: dict
    """
    # Add description to prompt:
    olog.append_entry({
        "content": SYS_PROMPT + description,
        "type": "user",
        "timestamp": datetime.now().isoformat()
    })

    # Retrieve recent entries
    messages = olog.get_recent_entries(5)
    
    # Call the LLM API
    llm = llm_wrapper()  # Assuming llm_wrapper is imported or available in the global scope
    response = await llm.call_llm_api(messages=messages, llm="openai", model="o1-preview")
    
    # Extract the generated code from the response
    generated_code = response.choices[0].message.content.strip()
    
    return {
        "success": True,
        "code": generated_code
    }