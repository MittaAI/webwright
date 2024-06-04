import ast
import inspect

tools = []  # A registry to hold all decorated functions' info
callable_registry = {} # A registry to hold the functions themselves

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
