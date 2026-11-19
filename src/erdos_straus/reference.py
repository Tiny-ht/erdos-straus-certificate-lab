"""A separately implemented factor-enumeration reference for small inputs.

It provides a cross-check, not independent formal proof of the common
mathematical reduction. Enumeration is deliberately elementary and slow.
"""

from math import gcd


def solutions_by_factors(n: int, x: int) -> set[tuple[int, int]]:
    if type(n) is not int or n < 2 or type(x) is not int:
        raise ValueError("expected integer n >= 2 and integer x")
    if 4 * x <= n or 4 * x > 3 * n:
        return set()
    a, b = 4 * x - n, n * x
    common = gcd(a, b)
    A, B = a // common, b // common
    result = set()
    for u in range(max(1, A * x - B), B + 1):
        if (B * B) % u != 0 or (u + B) % A != 0:
            continue
        v = (B * B) // u
        if (v + B) % A != 0:
            raise ArithmeticError("coprime factor reduction invariant failed")
        y, z = (u + B) // A, (v + B) // A
        if not (0 < x <= y <= z and 4 * x * y * z == n * (x*y + x*z + y*z)):
            raise ArithmeticError("factor reference produced an invalid witness")
        result.add((y, z))
    return result
