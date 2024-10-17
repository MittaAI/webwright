import ast
import inspect
import os
import importlib.util
import asyncio
from typing import get_origin, get_args

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
        tools.append({"type": "function", "function": self.info})

    def extract_function_info(self):
        source = inspect.getsource(inspect.unwrap(self.func))
        tree = ast.parse(source)

        # Find the function definition in the AST
        function_def = None
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_def = node
                break

        if function_def is None:
            raise Exception("Function definition not found in AST")

        function_name = function_def.name
        function_description = self.extract_description_from_docstring(self.func.__doc__)

        args = function_def.args
        parameters = {"type": "object", "properties": {}, "required": []}

        # Collect all arguments and defaults
        all_args = []
        defaults = []

        # Handle positional-only arguments (Python 3.8+)
        if hasattr(args, 'posonlyargs'):
            all_args.extend(args.posonlyargs)
            defaults.extend([None] * len(args.posonlyargs))

        # Handle regular arguments
        all_args.extend(args.args)
        num_args_with_defaults = len(args.defaults)
        num_args_without_defaults = len(args.args) - num_args_with_defaults
        defaults.extend([None] * num_args_without_defaults)
        defaults.extend(args.defaults)

        # Handle keyword-only arguments
        all_args.extend(args.kwonlyargs)
        kw_defaults = args.kw_defaults or []
        defaults.extend(kw_defaults)

        # Get the function's signature and parameters
        sig = inspect.signature(self.func)
        params = sig.parameters

        for arg, default_value in zip(all_args, defaults):
            if isinstance(arg, ast.arg):
                argument_name = arg.arg
                if argument_name in ['self', 'olog', 'llm']:
                    continue

                param = params.get(argument_name)
                if param:
                    annotation = param.annotation
                    if annotation == inspect.Parameter.empty:
                        argument_type = 'string'
                    else:
                        argument_type = self.convert_annotation_to_type(annotation)
                else:
                    argument_type = 'string'  # Default type if parameter not found

                parameter_description = self.extract_parameter_description(
                    argument_name, self.func.__doc__
                )

                param_info = {
                    "type": argument_type,
                    "description": parameter_description,
                }

                if param.default != inspect.Parameter.empty:
                    param_info["default"] = param.default
                elif default_value is not None:
                    try:
                        # Evaluate the default value safely
                        if isinstance(default_value, ast.Constant):
                            default_value_eval = default_value.value
                        elif isinstance(default_value, ast.NameConstant):
                            default_value_eval = default_value.value
                        elif isinstance(default_value, ast.Str):
                            default_value_eval = default_value.s
                        else:
                            default_value_eval = ast.literal_eval(default_value)
                        param_info["default"] = default_value_eval
                    except Exception:
                        # If evaluation fails, skip setting default
                        pass
                else:
                    parameters["required"].append(argument_name)

                parameters["properties"][argument_name] = param_info

        # Prepare the function definition as expected by OpenAI API
        function_info = {
            "name": function_name,
            "description": function_description,
            "parameters": parameters
        }

        return function_info

    def convert_annotation_to_type(self, annotation):
        type_mapping = {
            int: 'integer',
            str: 'string',
            bool: 'boolean',
            float: 'number',
            list: 'array',
            dict: 'object',
        }

        # Handle typing module types (e.g., List[int], Dict[str, Any])
        origin = get_origin(annotation)
        args = get_args(annotation)

        if annotation in type_mapping:
            return type_mapping[annotation]
        elif origin in [list, List]:
            return 'array'
        elif origin in [dict, Dict]:
            return 'object'
        elif annotation == bool:
            return 'boolean'
        else:
            # Default to 'string' if type is unrecognized
            return 'string'

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
            return " ".join(description_lines)
        return "No description provided."

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
        # This method may no longer be needed, but you can keep it for backward compatibility
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

def strict(func):
    func.is_strict = True
    return func

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
