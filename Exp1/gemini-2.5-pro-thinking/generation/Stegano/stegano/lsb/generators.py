from itertools import count

def eratosthenes():
    """
    An infinite prime number generator using the Sieve of Eratosthenes.
    """
    D = {}
    yield 2
    for q in count(3, 2):
        p = D.pop(q, None)
        if p is None:
            yield q
            D[q * q] = q
        else:
            x = p + q
            while x in D:
                x += p
            D[x] = p