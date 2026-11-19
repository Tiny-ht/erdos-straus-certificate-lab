#!/usr/bin/env python3
"""Regenerate deterministic examples and evidence, or compare with --check.

The report deliberately excludes machine paths, elapsed time, and Python
version so that independent machines can compare the exact same bytes.
Real unittest output is kept separately; this report never substitutes for
running the tests or checking the Lean build.
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from erdos_straus import (  # noqa: E402
    Exhausted, NoX, Unknown, Witness, attack_x, bounds, dumps_certificate,
    loads_certificate, search_fixed_n, verify_exhausted, verify_no_x,
    verify_witness,
)
from erdos_straus.reference import solutions_by_factors  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def json_text(value) -> str:
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def make_outputs() -> dict[str, str]:
    closed, witness = attack_x(5, 3), search_fixed_n(5)
    require(closed == NoX(5, 3, ((3, 3), (4, 8))), "branch example changed")
    require(witness == Witness(5, 2, 4, 20), "positive example changed")
    require(verify_no_x(5, 3, closed), "branch example rejected")
    require(verify_witness(5, 2, witness), "positive example rejected")
    for cert in (closed, witness):
        require(loads_certificate(dumps_certificate(cert)) == cert,
                "JSON roundtrip failed")

    branch_count = closed_count = witness_count = pair_count = 0
    solution_digest = hashlib.sha256()
    for n in range(2, 81):
        for x in range(1, (3 * n) // 4 + 3):
            direct = set()
            data = bounds(n, x)
            if data is not None:
                a, b, lo, hi = data
                for y in range(lo, hi + 1):
                    z, remainder = divmod(b * y, a * y - b)
                    if remainder == 0:
                        direct.add((y, z))
            require(direct == solutions_by_factors(n, x),
                    f"factor cross-check failed at n={n}, x={x}")
            result = attack_x(n, x)
            if type(result) is Witness:
                require(verify_witness(n, x, result), "invalid witness")
                require((result.y, result.z) in direct, "missing solution")
                witness_count += 1
            else:
                require(verify_no_x(n, x, result), "invalid NoX")
                require(not direct, "closed branch contains a solution")
                closed_count += 1
            for y, z in sorted(direct):
                solution_digest.update(f"{n},{x},{y},{z}\n".encode("ascii"))
            pair_count += len(direct)
            branch_count += 1
    require(branch_count == 2558, "cross-check scope changed")

    mutations = {
        "missing_row": NoX(5, 3, ((3, 3),)),
        "duplicate_y": NoX(5, 3, ((3, 3), (3, 8))),
        "reordered_rows": NoX(5, 3, ((4, 8), (3, 3))),
        "incorrect_remainder": NoX(5, 3, ((3, 3), (4, 9))),
        "zero_remainder": NoX(5, 3, ((3, 0), (4, 8))),
    }
    checks = {name: not verify_no_x(5, 3, cert)
              for name, cert in mutations.items()}
    checks["wrong_n_scope"] = not verify_no_x(6, 3, closed)
    checks["wrong_x_scope"] = not verify_no_x(5, 2, closed)
    checks["incomplete_root"] = not verify_exhausted(5, Exhausted(5, (closed,)))
    require(all(checks.values()), "a tampered claim was accepted")

    interrupted = search_fixed_n(5, max_checks=0)
    require(type(interrupted) is Unknown, "budget exhaustion was not UNKNOWN")
    require(not verify_exhausted(5, interrupted), "UNKNOWN closed the root")

    source_paths = sorted(
        list((ROOT / "src").rglob("*.py"))
        + list((ROOT / "tests").glob("*.py"))
        + list((ROOT / "scripts").glob("*.py"))
        + list((ROOT / "lean").glob("*.lean"))
    )
    hashes = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in source_paths}
    report = {
        "report_format": 1,
        "certificate_schema_version": 1,
        "cross_check": {
            "n_min": 2, "n_max": 80,
            "x_min": 1, "x_max_inclusive": "floor(3*n/4)+2",
            "branches": branch_count,
            "branches_with_witness": witness_count,
            "branches_without_witness": closed_count,
            "ordered_y_z_pairs": pair_count,
            "solution_rows_sha256": solution_digest.hexdigest(),
            "solution_rows_encoding": "ASCII n,x,y,z\\n, lexicographic numeric order",
            "all_solution_sets_agree": True,
        },
        "tamper_rejections": checks,
        "budget_zero": {
            "n": 5, "status": "unknown", "checks_done": interrupted.checks_done,
            "next_x": interrupted.next_x, "accepted_as_exhausted": False,
        },
        "source_sha256": hashes,
        "scope_note": "Finite Python experiment; not a formal proof or a proof of the conjecture.",
    }
    return {
        "examples/no_x_5_3.json": dumps_certificate(closed),
        "examples/witness_5.json": dumps_certificate(witness),
        "evidence/reproduction.json": json_text(report),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="compare tracked evidence without modifying files")
    args = parser.parse_args(argv)
    outputs = make_outputs()
    different = []
    for name, content in outputs.items():
        path = ROOT / name
        if args.check:
            matches = path.is_file() and path.read_bytes() == content.encode("utf-8")
            print(f"{'MATCH' if matches else 'MISMATCH'} {name}")
            if not matches:
                different.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content.encode("utf-8"))
            print(f"WROTE {name}")
    print("Cross-checked 2558 branches; exact solution sets agree.")
    print("Tampered scopes/coverage rejected; zero budget remains UNKNOWN.")
    return 1 if different else 0


if __name__ == "__main__":
    raise SystemExit(main())
