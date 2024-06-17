def is_prime(num):
    if num < 2:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True


def sum_of_digits(num):
    return sum(int(digit) for digit in str(num))


def find_primes_with_digit_sum(target_sum, limit):
    count = 0
    num = 2
    primes = []

    while count < limit:
        if is_prime(num) and sum_of_digits(num) == target_sum:
            primes.append(num)
            count += 1
        num += 1

    return primes


# Find and display the first 1000 prime numbers whose digits add up to 17
target_sum = 17
limit = 1000

prime_numbers = find_primes_with_digit_sum(target_sum, limit)

print(f"The first {limit} prime numbers whose digits add up to {target_sum}:")
for prime in prime_numbers:
    print(prime)
