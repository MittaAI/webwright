def is_prime(num):
    if num < 2:
        return False
    for i in range(2, int(num ** 0.5) + 1):
        if num % i == 0:
            return False
    return True

prime_numbers = [num for num in range(1, 218) if is_prime(num)]
for prime in prime_numbers:
    print(prime)
print(f'Total prime numbers from 1 to 217: {len(prime_numbers)}')