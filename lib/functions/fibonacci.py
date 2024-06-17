from lib.function_wrapper import function_info_decorator

@function_info_decorator
def fibonacci(n: str) -> dict:
    """
    Generate the Fibonacci sequence up to the specified number of terms.

    Args:
        n (str): The number of terms to generate (as a string).

    Returns:
        dict: A dictionary containing:
            - success (bool): Indicator of successful execution.
            - sequence (list): The generated Fibonacci sequence.
            - error (str, optional): Error message if an exception is thrown.
            - reason (str, optional): Detailed reason for the error.
    
    Raises:
        ValueError: If the input is not a positive integer.
    """
    try:
        n = int(n)
    except ValueError:
        return {
            "success": False,
            "error": "Invalid input",
            "reason": "The input must be convertible to a positive integer."
        }


    if n <= 0:
        return {
            "success": False,
            "error": "Invalid input",
            "reason": "The number of terms must be a positive integer."
        }
    
    fib_sequence = [0, 1]  # Initialize the sequence with the first two terms
    
    if n <= 2:
        return {
            "success": True,
            "sequence": fib_sequence[:n]
        }
    
    for _ in range(2, n):
        next_term = fib_sequence[-1] + fib_sequence[-2]
        fib_sequence.append(next_term)
    
    return {
        "success": True,
        "sequence": fib_sequence
    }
