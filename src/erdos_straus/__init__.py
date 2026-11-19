"""Exact, scoped certificates for finite Erdős–Straus search.

This package is a research prototype, not a proof of the conjecture.
"""

from .core import (
    SCHEMA_VERSION,
    Exhausted,
    NoX,
    Unknown,
    Witness,
    attack_x,
    bounds,
    search_fixed_n,
    verify_exhausted,
    verify_no_x,
    verify_witness,
)
from .certificates import CertificateError, dumps_certificate, loads_certificate

__all__ = [
    "SCHEMA_VERSION", "Witness", "NoX", "Exhausted", "Unknown", "bounds",
    "attack_x", "search_fixed_n", "verify_witness", "verify_no_x",
    "verify_exhausted", "CertificateError", "dumps_certificate",
    "loads_certificate",
]
