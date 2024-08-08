import math
from lib.function_wrapper import function_info_decorator

@function_info_decorator
def calculate(expression: str) -> dict:
    """
    Calculates the result of a given mathematical expression. 
    Supports functions like sqrt() and variables like pi, e, etc. from the math module.
    When the model returns a value, it can put \(<val>\) around it to colorize it.
    :param expression: The mathematical expression to evaluate.
    :type expression: str
    :return: A dictionary containing the result of the calculation.
    :rtype: dict
    """
    # Define a safe dictionary of allowed names
    allowed_names = {
        'sqrt': math.sqrt,
        'pi': math.pi,
        'e': math.e,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'pow': math.pow,
        'ceil': math.ceil,
        'floor': math.floor,
        'factorial': math.factorial,
        'arc': arc  # Added arc function
    }

    try:
        # Evaluate the expression using eval() with the allowed names
        result = eval(expression, {"__builtins__": None}, allowed_names)
        return {
            "success": True,
            "result": result
        }
    except (SyntaxError, ZeroDivisionError, NameError, TypeError, ValueError) as e:
        # Handle specific exceptions and return an error message
        error_message = str(e)
        return {
            "success": False,
            "error": "Invalid expression",
            "reason": error_message
        }
    except Exception as e:
        # Handle any other unexpected exceptions
        error_message = str(e)
        return {
            "success": False,
            "error": "Calculation failed",
            "reason": error_message
        }

def arc(value):
    """Calculate the arc tangent of a value."""
    return math.atan(value)

allowed_names['arc'] = arc  # Ensure arc function is in the allowed names