import pytest
import math
from lib.functions.calculate import calculate

@pytest.mark.parametrize("expression, expected_result", [
    ("2 + 2", 4),
    ("10 - 5", 5),
    ("3 * 4", 12),
    ("15 / 3", 5),
    ("2 ** 3", 8),
    ("sqrt(16)", 4),
    ("pi", math.pi),
    ("e", math.e),
    ("sin(0)", 0),
    ("cos(pi)", -1),
    ("tan(pi/4)", 1),
    ("log(e)", 1),
    ("log10(100)", 2),
    ("exp(0)", 1),
    ("pow(2, 3)", 8),
    ("ceil(3.2)", 4),
    ("floor(3.8)", 3),
    ("factorial(5)", 120),
])
def test_valid_expressions(expression, expected_result):
    result = calculate(expression)
    assert result["success"] == True
    assert math.isclose(result["result"], expected_result, rel_tol=1e-9)

@pytest.mark.parametrize("expression, error_type", [
    ("2 + ", "Invalid expression"),
    ("10 / 0", "Invalid expression"),
    ("undefined_function(10)", "Invalid expression"),
    ("1 + 'string'", "Invalid expression"),
])
def test_invalid_expressions(expression, error_type):
    result = calculate(expression)
    assert result["success"] == False
    assert result["error"] == error_type

def test_large_numbers():
    result = calculate("10**100")
    assert result["success"] == True
    assert result["result"] == 10**100

def test_very_small_numbers():
    result = calculate("10**-100")
    assert result["success"] == True
    assert result["result"] == 10**-100

def test_complex_expression():
    expression = "sin(pi/4) + log(e**2) * sqrt(16) / 2"
    result = calculate(expression)
    expected = math.sin(math.pi/4) + math.log(math.e**2) * math.sqrt(16) / 2
    assert result["success"] == True
    assert math.isclose(result["result"], expected, rel_tol=1e-9)

def test_nested_functions():
    expression = "sqrt(pow(sin(pi/6), 2) + pow(cos(pi/6), 2))"
    result = calculate(expression)
    assert result["success"] == True
    assert math.isclose(result["result"], 1, rel_tol=1e-9)

def test_factorial_error():
    result = calculate("factorial(-1)")
    assert result["success"] == False
    assert result["error"] == "Invalid expression"

def test_not_allowed_builtin():
    result = calculate("__import__('os').system('ls')")
    assert result["success"] == False
    assert result["error"] == "Invalid expression"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])