"""
Generator functions for LSB steganography
"""


def eratosthenes():
    """
    Generator for prime numbers using the Sieve of Eratosthenes.
    
    Yields:
        Prime numbers in sequence
    """
    # Yield initial primes
    yield 2
    yield 3
    
    # Track composites
    composites = {}
    candidate = 5
    
    while True:
        # Check if candidate is composite
        if candidate in composites:
            # Move the prime factors to next multiples
            prime = composites.pop(candidate)
            next_multiple = candidate + 2 * prime
            while next_multiple in composites:
                next_multiple += 2 * prime
            composites[next_multiple] = prime
        else:
            # candidate is prime
            yield candidate
            # Mark first composite (square of prime)
            composites[candidate * candidate] = candidate
        
        candidate += 2