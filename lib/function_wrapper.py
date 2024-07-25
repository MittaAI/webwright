import ast
import inspect
import os
import importlib.util
import asyncio

tools = []  # A registry to hold all decorated functions' info
callable_registry = {}  # A registry to hold the functions themselves

# Set up logging
from lib.util import get_logger
logger = get_logger()

class FunctionWrapper:
    def __init__(self, func):
        self.func = func
        self.info = self.extract_function_info()
        callable_registry[func.__name__] = func
        tools.append({'type': 'function', 'function': self.info})  # Add function info to registry

    def extract_function_info(self):
        source = inspect.getsource(self.func)
        tree = ast.parse(source)
        function_name = tree.body[0].name
        function_description = self.extract_description_from_docstring(self.func.__doc__)
        args = tree.body[0].args
        parameters = {"type": "object", "properties": {}, "required": []}
        for arg in args.args:
            argument_name = arg.arg
            argument_type = self.convert_type_name(self.extract_parameter_type(argument_name, self.func.__doc__)) or "string"
            parameter_description = self.extract_parameter_description(argument_name, self.func.__doc__)
            parameters["properties"][argument_name] = {
                "type": argument_type,
                "description": parameter_description,
            }
            if arg.arg != 'self':  # Exclude 'self' from required parameters for class methods
                parameters["required"].append(argument_name)
        
        return_type = self.convert_type_name(self.extract_return_type(tree))
        function_info = {
            "name": function_name,
            "description": function_description,
            "parameters": parameters,
            "return_type": return_type,
        }
        return function_info

    def extract_description_from_docstring(self, docstring):
        if docstring:
            lines = docstring.strip().split("\n")
            description_lines = []
            for line in lines:
                line = line.strip()
                if line.startswith(":param") or line.startswith(":type") or line.startswith(":return"):
                    break
                if line:
                    description_lines.append(line)
            return "\n".join(description_lines)
        return "No description provided."

    def extract_parameter_type(self, parameter_name, docstring):
        if docstring:
            type_prefix = f":type {parameter_name}:"
            lines = docstring.strip().split("\n")
            for line in lines:
                if line.strip().startswith(type_prefix):
                    return line.replace(type_prefix, "").strip()
        return None

    def extract_parameter_description(self, parameter_name, docstring):
        if docstring:
            param_prefix = f":param {parameter_name}:"
            lines = docstring.strip().split("\n")
            for line in lines:
                if line.strip().startswith(param_prefix):
                    return line.replace(param_prefix, "").strip()
        return "No description provided."

    def extract_return_type(self, tree):
        if tree.body[0].returns:
            return_type_segment = ast.get_source_segment(inspect.getsource(self.func), tree.body[0].returns)
            if return_type_segment:
                return return_type_segment.strip()
        return "None"

    def convert_type_name(self, type_name):
        type_mapping = {
            'int': 'integer',
            'str': 'string',
            'bool': 'boolean',
            'float': 'number',
            'list': 'array',
            'dict': 'object',
            # Add more mappings as needed
        }
        return type_mapping.get(type_name, type_name)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

def function_info_decorator(func):
    wrapped_function = FunctionWrapper(func)
    def wrapper(*args, **kwargs):
        return wrapped_function(*args, **kwargs)
    wrapper.function_info = wrapped_function.info
    return wrapper

def load_functions_from_directory(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3]
            module_path = os.path.join(directory, filename)
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                for attr in dir(module):
                    func = getattr(module, attr)
                    if callable(func) and hasattr(func, 'function_info'):
                        logger.info(f"Loaded function: {attr}")
            except Exception as e:
                logger.error(f"Failed to load module {module_name}: {e}")

# Load all functions from the lib/functions directory
functions_directory = os.path.join(os.path.dirname(__file__), 'functions')
load_functions_from_directory(functions_directory)

@function_info_decorator
async def multi_tool_use_parallel(tool_uses):
    """
    Execute multiple tool uses in parallel.

    :param tool_uses: A list of tool use objects, each containing 'recipient_name' and 'parameters'.
    :type tool_uses: list
    :return: A list of results from the executed tool uses.
    """
    async def execute_tool(tool_use):
        function_name = tool_use['recipient_name']
        parameters = tool_use['parameters']
        return await execute_function_by_name(function_name, **parameters)

    results = await asyncio.gather(*[execute_tool(tool_use) for tool_use in tool_uses])
    return results

# Manually adjust the function info to include the correct schema for tool_uses
multi_tool_use_parallel.function_info['parameters']['properties']['tool_uses'] = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "recipient_name": {"type": "string"},
            "parameters": {"type": "object"}
        },
        "required": ["recipient_name", "parameters"]
    }
}

# Add multi_tool_use_parallel to callable_registry
callable_registry['multi_tool_use_parallel'] = multi_tool_use_parallel