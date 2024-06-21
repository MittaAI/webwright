# fib.py

def fibonacci(n: int) -> list:
    """
    Returns a list containing the Fibonacci sequence up to n terms.

    :param n: The number of terms in the Fibonacci sequence to generate.
    :type n: int
    :return: A list containing the Fibonacci sequence up to n terms.
    :rtype: list
    """
    sequence = []
    a, b = 0, 1
    for _ in range(n):
        sequence.append(a)
        a, b = b, a + b
    return sequence