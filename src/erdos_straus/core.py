"""Integer search and independent, scope-bound certificate checks.

All searches use ordered denominators x <= y <= z. A NoX certificate
excludes only that ordered branch, not all solutions for n. An Exhausted
certificate must cover every legal x; an interrupted search returns Unknown.
The mathematical completeness argument is documented separately and is not
claimed to have been checked by Lean.
"""

from dataclasses import dataclass

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Witness:
    n: int
    x: int
    y: int
    z: int
    version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class NoX:
    n: int
    x: int
    remainders: tuple[tuple[int, int], ...]
    version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class Exhausted:
    n: int
    branches: tuple[NoX, ...]
    version: int = SCHEMA_VERSION


@dataclass(frozen=True)
class Unknown:
    """An interrupted computation, never a negative certificate.

    closed_branches contains only complete NoX certificates. The partially
    searched next_x branch is deliberately not represented as a NoX.
    """

    n: int
    closed_branches: tuple[NoX, ...]
    next_x: int
    checks_done: int
    reason: str = "check_budget_exhausted"


def _integer(name: str, value: int, minimum: int | None = None) -> None:
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer (bool and float are rejected)")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")


def _version_ok(value: object) -> bool:
    return type(value) is int and value == SCHEMA_VERSION


def bounds(n: int, x: int) -> tuple[int, int, int, int] | None:
    """Return (a, b, y_min, y_max), or None for an impossible ordered x.

    Domain errors raise ValueError and cannot be interpreted as a negative
    certificate. Out-of-range integral x is a legitimate empty branch.
    """
    _integer("n", n, 2)
    _integer("x", x)
    if not (n // 4 + 1 <= x <= (3 * n) // 4):
        return None
    a, b = 4 * x - n, n * x
    return a, b, max(x, b // a + 1), (2 * b) // a


def _scan_x(
    n: int, x: int, max_checks: int | None
) -> tuple[Witness | NoX | None, int]:
    data = bounds(n, x)
    if data is None:
        return NoX(n, x, ()), 0
    a, b, lo, hi = data
    rejected: list[tuple[int, int]] = []
    checked = 0
    for y in range(lo, hi + 1):
        if max_checks is not None and checked >= max_checks:
            return None, checked
        c = a * y - b
        z, remainder = divmod(b * y, c)
        checked += 1
        if remainder == 0:
            return Witness(n, x, y, z), checked
        rejected.append((y, remainder))
    return NoX(n, x, tuple(rejected)), checked


def attack_x(n: int, x: int) -> Witness | NoX:
    """Search one complete ordered x branch using exact arithmetic."""
    result, _ = _scan_x(n, x, None)
    # None is used only for an explicitly bounded, interrupted computation.
    if result is None:
        raise RuntimeError("unexpected interruption of an unbounded x search")
    return result


def verify_witness(n: int, x: int, cert: object) -> bool:
    """Check an ordered witness against the caller's n and x scope."""
    _integer("n", n, 2)
    _integer("x", x)
    if type(cert) is not Witness:
        return False
    if not _version_ok(cert.version):
        return False
    if not all(type(v) is int for v in (cert.n, cert.x, cert.y, cert.z)):
        return False
    if (cert.n, cert.x) != (n, x):
        return False
    y, z = cert.y, cert.z
    return 0 < x <= y <= z and 4 * x * y * z == n * (x*y + x*z + y*z)


def verify_no_x(n: int, x: int, cert: object) -> bool:
    """Check every y and its nonzero remainder; never trust submitted bounds."""
    _integer("n", n, 2)
    _integer("x", x)
    if type(cert) is not NoX:
        return False
    if not _version_ok(cert.version):
        return False
    if type(cert.n) is not int or type(cert.x) is not int:
        return False
    if (cert.n, cert.x) != (n, x) or type(cert.remainders) is not tuple:
        return False
    data = bounds(n, x)
    if data is None:
        return cert.remainders == ()
    a, b, lo, hi = data
    if len(cert.remainders) != max(0, hi - lo + 1):
        return False
    for expected_y, row in zip(range(lo, hi + 1), cert.remainders):
        if type(row) is not tuple or len(row) != 2:
            return False
        y, remainder = row
        if type(y) is not int or type(remainder) is not int or y != expected_y:
            return False
        c = a * y - b
        if not (0 < remainder < c and (b * y) % c == remainder):
            return False
    return True


def search_fixed_n(n: int, max_checks: int | None = None) -> Witness | Exhausted | Unknown:
    """Search a fixed n; max_checks bounds the searcher's (x,y) checks.

    Exhausted is emitted only after every x branch was independently checked.
    Verification may repeat arithmetic and is not charged to this search
    counter; max_checks is not a CPU-time or memory bound.
    Receiving Exhausted in real research would require independent scrutiny;
    this implementation does not resolve the mathematical conjecture.
    """
    _integer("n", n, 2)
    if max_checks is not None:
        _integer("max_checks", max_checks, 0)
    closed: list[NoX] = []
    checks_done = 0
    for x in range(n // 4 + 1, (3 * n) // 4 + 1):
        remaining = None if max_checks is None else max_checks - checks_done
        result, checked = _scan_x(n, x, remaining)
        checks_done += checked
        if result is None:
            return Unknown(n, tuple(closed), x, checks_done)
        if type(result) is Witness:
            if not verify_witness(n, x, result):
                raise RuntimeError("searcher produced an invalid witness")
            return result
        if not verify_no_x(n, x, result):
            raise RuntimeError("searcher produced an invalid branch certificate")
        closed.append(result)
    result = Exhausted(n, tuple(closed))
    if not verify_exhausted(n, result):
        raise RuntimeError("searcher produced an incomplete root certificate")
    return result


def verify_exhausted(n: int, cert: object) -> bool:
    """Verify all legal x branches, including exact scope and coverage order."""
    _integer("n", n, 2)
    if type(cert) is not Exhausted or not _version_ok(cert.version):
        return False
    if type(cert.n) is not int or cert.n != n or type(cert.branches) is not tuple:
        return False
    lo, hi = n // 4 + 1, (3 * n) // 4
    if len(cert.branches) != hi - lo + 1:
        return False
    return all(
        verify_no_x(n, x, branch)
        for x, branch in zip(range(lo, hi + 1), cert.branches)
    )
