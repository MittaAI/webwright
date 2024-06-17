def fibonacci(n):
    """
    Generate the Fibonacci sequence up to the specified number of terms.
    
    Args:
        n (int): The number of terms to generate.
        
    Returns:
        list: A list containing the Fibonacci sequence up to the specified number of terms.
        
    Raises:
        ValueError: If the input is not a positive integer.
    """
    if not isinstance(n, int) or n <= 0:
        raise ValueError("The number of terms must be a positive integer.")
    
    fib_sequence = [0, 1]  # Initialize the sequence with the first two terms
    
    if n <= 2:
        return fib_sequence[:n]
    
    for _ in range(2, n):
        next_term = fib_sequence[-1] + fib_sequence[-2]
        fib_sequence.append(next_term)
    
    return fib_sequence