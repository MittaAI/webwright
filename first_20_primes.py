def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

# Generate the first 20 prime numbers
primes = []
n = 2
while len(primes) < 20:
    if is_prime(n):
        primes.append(n)
    n += 1

print('The first 20 prime numbers are:', primes)
