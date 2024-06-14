# lib/functions/claude_write_code.py
import logging
from anthropic import Client
from lib.function_wrapper import function_info_decorator
from lib.util import get_anthropic_api_key

@function_info_decorator
def claude_write_code(prompt: str, model: str = "claude-3-opus-20240229") -> dict:
    """
    Generates code using Claude's API based on the provided prompt.
    
    :param prompt: The detailed prompt outlining the steps or requirements for the code.
    :type prompt: str
    :param model: The name of the Claude model to use for code generation. Defaults to "claude-3-opus-20240229".
    :type model: str
    :param anthropic_token: The Anthropic API token to use for authentication. If not provided, it will be retrieved from the environment variable 'ANTHROPIC_API_KEY'.
    :type anthropic_token: str
    :return: A dictionary containing the success status and the generated code.
    :rtype: dict
    """
    try:
        anthropic_token = get_anthropic_api_key()
        if not anthropic_token:
            raise ValueError("Anthropic API token not provided and 'ANTHROPIC_API_KEY' environment variable not set.")

        client = Client(api_key=anthropic_token)

        system_prompt = "You are a helpful assistant that generates code based on the provided prompt."
        messages = [{"role": "user", "content": prompt}]

        response = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=messages,
            system=system_prompt
        )

        content_blocks = response.content
        if content_blocks:
            generated_code = ''.join(block.text for block in content_blocks)
            return {
                "success": True,
                "code": generated_code,
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate code",
                "reason": "Claude's API returned empty content blocks.",
            }

    except Exception as e:
        logging.error(f"Error generating code with Claude's API: {str(e)}")
        return {
            "success": False,
            "error": "Failed to generate code",
            "reason": str(e),
        }
