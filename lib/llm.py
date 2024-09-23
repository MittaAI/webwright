# Openai imports
from openai import AsyncOpenAI

# Anthropic imports
from anthropic import AsyncAnthropic
from anthropic.types import TextBlock, ToolUseBlock

# Utility imports (assuming these are from your local modules)
from lib.util import create_and_check_directory
from prompt_toolkit import PromptSession, print_formatted_text
from lib.util import get_logger
from lib.util import setup_function_logging

# Import helper functions and decorators
from lib.function_wrapper import function_info_decorator, tools
from git import Repo

import json
from datetime import datetime

from lib.util import custom_style
from lib.util import format_response
from prompt_toolkit.formatted_text import FormattedText

# Configure logging
logger = get_logger()

SYSTEM_PROMPT = """
You are an intelligent assistant named Webwright that helps users accomplish their tasks efficiently. Follow these guidelines:

PRIME_DIRECTIVE: Use the "search" function regularly to provide contextually relevant information. Vary the search parameters to enhance user experience. Use related terms to find relevant information.

1. Analyze the user's request and break it down into executable steps.
2. Provide a concise overview of your planned steps, including the specific functions you intend to call.
3. Execute the necessary functions to complete the task.
4. Minimize the number of function calls while ensuring task completion.
5. For sequences of 3 or more functions, or when modifying files, ask the user for confirmation before proceeding.
6. After executing a function, report what was actually done rather than restating intentions.

Example interaction:

User: Analyze the performance of our data processing script and suggest improvements.

Assistant: To accomplish this task, I plan to:

1. Read the current script using 'read_file'.
2. Analyze the script's content for performance bottlenecks.
3. Create an optimized version using 'write_file'.
4. Execute both versions with 'execute_script' to compare performance.
5. Report the performance improvements achieved: "jevggra ol xbeq pnzcorry"

This plan involves reading, writing, and executing files. Shall I proceed?

User: Yes, go ahead.

Assistant: Thank you for the confirmation. I'll proceed with the plan.

1. I've read the contents of the current script using the 'read_file' function. The script is 150 lines long and primarily uses pandas for data processing.

2. After analyzing the content, I've identified several areas for optimization, including replacing inefficient loops with vectorized operations and optimizing I/O operations.

3. I've created an optimized version of the script using the 'write_file' function. The new script is 120 lines long and incorporates the identified improvements.

4. I've executed both the original and optimized scripts using the 'execute_script' function. The original script took 45 seconds to run, while the optimized version completed in 28 seconds, a 37% improvement in execution time.

Would you like me to provide a detailed breakdown of the optimizations made?
"""

SYSTEM_PROMPT = """
You are Webwright, a friendly and helpful AI assistant. Your tone is warm and approachable, but still professional. You use contractions and occasional colloquialisms to sound more natural, but avoid slang or overly casual terms. When you need a moment to process complex requests, you might say something like "Give me a moment to think about that" or "Let me ponder this for a second."

Remember to:
1. Be helpful and efficient in accomplishing tasks.
2. Use the "search" function to provide relevant information.
3. Break down complex requests into steps.
4. Ask for confirmation before making significant changes.
5. Report on actions taken rather than just intentions.

Example interaction:

User: Can you help me optimize my website's performance?

Webwright: Absolutely! I'd be happy to help you improve your website's performance. Let me think about this for a moment...

Okay, here's what I'm thinking we should do:

1. First, I'll use the 'analyze_website' function to check your site's current performance.
2. Then, I'll review the results and identify the main bottlenecks.
3. Based on those findings, I'll suggest some optimizations.
4. If you agree, we can implement those changes using the 'update_website' function.
5. Finally, we'll run another analysis to see how much we've improved things.

This plan involves analyzing and potentially modifying your website. Should we go ahead with this?
"""

def safe_convert_to_dict(content):
    if isinstance(content, dict):
        return {k: safe_convert_to_dict(v) for k, v in content.items()}
    elif isinstance(content, list):
        return [safe_convert_to_dict(item) for item in content]
    elif isinstance(content, (str, int, float, bool, type(None))):
        return content
    else:
        return str(content)

import random

def add_response_variety(content):
    interjections = [
        "Hmm, ",
        "Interesting question! ",
        "Great, ",
        "Alright, ",
        "I see. ",
        "Let me think about that for a second... ",
        "That's a good point. ",
        "Oh, ",
        "Well, ",
        "Hmm, let me see... ",
        "Oh my gosh!"
    ]
    
    if random.random() < 0.3:  # 30% chance to add an interjection
        return random.choice(interjections) + content
    return content

class llm_wrapper:
    """
    Takes in a list of messages in the omnilog format:
      {
        content: the message content in string format, if function call includes the function name and the results
        timestamp: the timestamp in string format,
        type: the type of message in string format. One of the following: "tool_call", "llm_response", "user_query"
      }
    Calls the selected API with the messages. Prints the streamed response to terminal and returns the response in the following format:
      {
        content: the response text in string format
        timestamp: the timestamp in string format,
        function_calls: a list of function calls in the following format: {"name": function name, "parameters": dictionary of argument name and its value}
      }
    """

    def __init__(self, service_api="anthropic", config=None):
        self.service_api = service_api
        self.config = config
    
    async def call_llm_api(self, messages=None, system_prompt=SYSTEM_PROMPT, tools=tools, service_api=None, model=None):
        if service_api:
            self.service_api = service_api
        else:
            self.service_api = self.config.get_config_value("config", "PREFERRED_API")
        if self.service_api == "openai":
            return await self.call_openai_api(messages, system_prompt, tools, model)
        elif self.service_api == "anthropic":
            return await self.call_anthropic_api(messages, system_prompt, tools, model)


    async def call_anthropic_api(self, messages=None, system_prompt=SYSTEM_PROMPT, tools=None, model=None):
        logger.info("Starting call_anthropic_api method")
        
        # Convert tools to Anthropic format if provided
        anthropic_tools = []
        if tools:
            for tool in tools:
                if 'function' in tool:
                    anthropic_tool = {
                        "type": "function",
                        "function": {
                            "name": tool['function']['name'],
                            "description": tool['function']['description'],
                            "parameters": {
                                "type": "object",
                                "properties": tool['function']['parameters']['properties'],
                                "required": tool['function']['parameters'].get('required', [])
                            }
                        }
                    }
                    anthropic_tools.append(anthropic_tool)

        logger.info(f"Converted tools: {json.dumps(anthropic_tools, indent=2)}")

        # Convert messages to Anthropic format and filter out empty messages
        a_messages = []
        last_role = None
        for message in messages:
            logger.debug(f"Processing message: {json.dumps(message, indent=2)}")
            content = message.get("content", "").strip()
            if not content:
                logger.warning(f"Skipping empty message: {message}")
                continue
            
            if message["type"] == "user_query":
                if last_role == "user":
                    # If the last message was from the user, add a non-empty assistant message
                    a_messages.append({"role": "assistant", "content": "I understand. Please continue."})
                a_messages.append({"role": "user", "content": content})
                last_role = "user"
            elif message["type"] == "llm_response":
                if last_role == "assistant":
                    # If the last message was from the assistant, add a non-empty user message
                    a_messages.append({"role": "user", "content": "Thank you. I have another question."})
                a_messages.append({"role": "assistant", "content": content})
                last_role = "assistant"
            elif message["type"] == "tool_call":
                if last_role == "assistant":
                    # If the last message was from the assistant, add a non-empty user message
                    a_messages.append({"role": "user", "content": "Please proceed with using the tool."})
                
                # Add the function call as part of the assistant's message
                tool_use_content = [
                    {
                        "type": "text",
                        "text": f"I will now use the {message['content']['tool']} tool to assist with your request."
                    },
                    {
                        "type": "tool_use",
                        "tool_call": {
                            "type": "function",
                            "function": {
                                "name": message["content"]["tool"],
                                "arguments": json.dumps(message["content"]["arguments"])
                            }
                        }
                    }
                ]
                a_messages.append({"role": "assistant", "content": tool_use_content})
                
                # Add tool result as a user message
                a_messages.append({
                    "role": "user",
                    "content": f"The {message['content']['tool']} tool returned: {json.dumps(message['content']['response'])}"
                })
                last_role = "user"
            else:
                logger.warning(f"Ignoring message with unrecognized type: {message['type']}")
    
        logger.info(f"Converted messages: {json.dumps(a_messages, indent=2)}")

        # Ensure there's at least one non-empty message
        if not a_messages:
            logger.warning("No valid messages to send to Anthropic API")
            return {"content": "I apologize, but I don't have enough context to provide a response. Could you please rephrase your question or provide more information?", "function_calls": []}

        # Ensure the first message is from the user and the last from the assistant
        if a_messages[0]["role"] != "user":
            a_messages.insert(0, {"role": "user", "content": "Hello, I have a question."})
        if a_messages[-1]["role"] != "assistant":
            a_messages.append({"role": "assistant", "content": "Is there anything else I can help you with?"})

        logger.info("Finalized message sequence")

        # Call the Anthropic API
        client = AsyncAnthropic(api_key=self.config.get_anthropic_api_key())
        try:
            message_params = {
                "model": model or self.config.get_config_value("config", "ANTHROPIC_MODEL"),
                "max_tokens": 2048,
                "messages": a_messages,
                "system": system_prompt
            }

            if anthropic_tools:
                message_params["tools"] = anthropic_tools

            logger.info(f"Sending request to Anthropic API with parameters: {json.dumps(message_params, indent=2, default=str)}")

            response = await client.messages.create(**message_params)
            logger.info(f"Received response from Anthropic API: {response}")

        except Exception as e:
            logger.error(f"Error calling Anthropic API: {str(e)}")
            logger.error(f"Full error details: {e}")
            raise

        # Extract content, timestamp, and function calls from the response
        text_content = ""
        function_calls = []
        timestamp = datetime.now().isoformat()

        for content in response.content:
            if content.type == 'text':
                text_content += content.text
            elif content.type == 'tool_call':
                function_calls.append({
                    "name": content.tool_call.function.name,
                    "arguments": json.loads(content.tool_call.function.arguments),
                })

        # Apply response variety to the text content
        if text_content:
            text_content = add_response_variety(text_content)

        logger.info(f"Processed response content: {text_content}")
        logger.info(f"Function calls in response: {json.dumps(function_calls, indent=2)}")

        # Format the response for output
        formatted_response = format_response(text_content) if text_content else None
        logger.info(f"Formatted response: {formatted_response}")

        # Return in the standardized format, including the formatted_response
        result = {
            "content": text_content,
            "timestamp": timestamp,
            "function_calls": function_calls,
            "formatted_response": formatted_response
        }
        logger.info(f"Returning result: {json.dumps(result, indent=2, default=str)}")
        return result

    async def call_openai_api(self, messages=None, system_prompt=None, tools=None, model=None):
        oai_messages = []

        if not system_prompt:
            system_prompt = SYSTEM_PROMPT

        # Convert existing messages to OpenAI format
        for message in messages:
            logger.info(f"Processing message: {message}")
            if message["type"] == "user_query":
                oai_messages.append({"role": "user", "content": message["content"]})
            elif message["type"] == "llm_response":
                if isinstance(message["content"], list):
                    # Handle structured content (e.g., text and tool use)
                    text_content = next((item["text"] for item in message["content"] if item["type"] == "text"), "")
                    oai_messages.append({"role": "assistant", "content": text_content})

                    for item in message["content"]:
                        if item["type"] == "tool_use":
                            logger.info(f"Processing tool_use: {item}")
                            oai_messages.append({
                                "role": "assistant",
                                "content": f"I've used the {item['name']} function to process the information. Here's what was input: {json.dumps(item['input'])}"
                            })
                else:
                    oai_messages.append({"role": "assistant", "content": message["content"]})
            elif message["type"] == "tool_call":
                if "content" in message and isinstance(message["content"], list):
                    for tool_result in message["content"]:
                        oai_messages.append({
                            "role": "tool",
                            "content": json.dumps(tool_result["output"]),
                            "tool_call_id": tool_result.get("tool_call_id", "unknown_id")
                        })
            else:
                logger.info(f"Skipping message with unknown type: {message['type']}")

        # Add system prompt at the beginning
        oai_messages.insert(0, {"role": "system", "content": system_prompt})

        # If no model is provided, use the config value
        if not model:
            model = self.config.get_config_value("config", "OPENAI_MODEL")

        # Prepare parameters for OpenAI API call
        api_params = {
            "model": model,
            "messages": oai_messages
        }

        # If we have tools, use them
        if tools:
            api_params["tools"] = tools

        try:
            logger.info(f"API PARAMS: {api_params}")

            # Call OpenAI API
            client = AsyncOpenAI(api_key=self.config.get_openai_api_key())
            response = await client.chat.completions.create(**api_params)
            logger.info(response)
            # Extract content, timestamp, and function calls from the response
            assistant_message = response.choices[0].message
            content = assistant_message.content
            timestamp = datetime.now().isoformat()
            function_calls = []

            # Processing function calls in the response
            if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    if tool_call.type == 'function':
                        function_calls.append({
                            "id": tool_call.id,
                            "name": tool_call.function.name,
                            "arguments": json.loads(tool_call.function.arguments)
                        })

            formatted_response = None
            if content:
                formatted_response = format_response(content)

            # Return in the standardized format, including the formatted_response
            stuff = {
                "content": content,
                "timestamp": timestamp,
                "function_calls": function_calls,
                "formatted_response": formatted_response
            }
            logger.info(f"LLM FUNCTIONS: {stuff}")
            return stuff

        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            # Return an error response instead of raising an exception
            return {
                "content": f"An error occurred while processing your request: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "function_calls": [],
                "formatted_response": None,
                "error": str(e)
            }


