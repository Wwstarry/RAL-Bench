"""
Generators for LSB steganography.
"""

def eratosthenes() -> iter:
    """
    Implementation of the Sieve of Eratosthenes.
    Generates prime numbers.
    
    Returns:
        An iterator yielding prime numbers
    """
    D = {}  # Map composite integers to their first-found prime factor
    q = 2   # First prime number
    
    while True:
        if q not in D:
            # q is a prime number
            yield q
            D[q * q] = [q]  # Start marking multiples from q**2
        else:
            # q is a composite number
            for p in D[q]:
                D.setdefault(p + q, []).append(p)
            del D[q]
        
        q += 1