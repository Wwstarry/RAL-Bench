"""
Generators for LSB steganography
"""


def eratosthenes():
    """
    Generate prime numbers using the Sieve of Eratosthenes.
    
    Yields:
        int: Prime numbers in sequence
    """
    yield 2
    candidates = {}
    
    for i in range(3, 1000000, 2):
        if i not in candidates:
            yield i
            candidates[i * i] = [i]
        else:
            for p in candidates[i]:
                candidates.setdefault(i + 2 * p, []).append(p)
            del candidates[i]