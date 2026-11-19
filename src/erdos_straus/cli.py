"""Command-line interface for exact, scoped certificate experiments."""

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .certificates import dumps_certificate, loads_certificate
from .core import (
    Exhausted,
    NoX,
    Unknown,
    Witness,
    attack_x,
    search_fixed_n,
    verify_exhausted,
    verify_no_x,
    verify_witness,
)


def _integer(text: str) -> int:
    try:
        return int(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected an integer") from error


def _n(text: str) -> int:
    value = _integer(text)
    if value < 2:
        raise argparse.ArgumentTypeError("n must be at least 2")
    return value


def _nonnegative(text: str) -> int:
    value = _integer(text)
    if value < 0:
        raise argparse.ArgumentTypeError("check budget must be nonnegative")
    return value


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="erdos-straus", allow_abbrev=False,
        description="Exact Erdős–Straus branch certificates; not a proof of the conjecture.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    branch = commands.add_parser("branch", allow_abbrev=False, help="search one ordered x branch")
    branch.add_argument("n", type=_n)
    branch.add_argument("x", type=_integer)
    branch.add_argument("--output", type=Path, help="write certificate JSON to this file")

    search = commands.add_parser("search", allow_abbrev=False, help="search every legal x for a fixed n")
    search.add_argument("n", type=_n)
    search.add_argument("--max-checks", type=_nonnegative,
                        help="maximum searcher (x,y) checks; verification work is not counted")
    search.add_argument("--output", type=Path, help="write result JSON to this file")

    verify = commands.add_parser("verify", allow_abbrev=False, help="verify a certificate against explicit scope")
    verify.add_argument("file", type=Path)
    verify.add_argument("--n", type=_n, required=True)
    verify.add_argument("--x", type=_integer,
                        help="required for witness/no_x; forbidden for exhausted")
    return parser


def _write(text: str, destination: Path | None) -> None:
    if destination is None:
        sys.stdout.write(text)
    else:
        destination.write_text(text, encoding="utf-8")


def _json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def _checked_output(result: Witness | NoX | Exhausted, n: int, x: int | None) -> str:
    if type(result) is Witness:
        accepted = verify_witness(n, result.x if x is None else x, result)
    elif type(result) is NoX and x is not None:
        accepted = verify_no_x(n, x, result)
    elif type(result) is Exhausted and x is None:
        accepted = verify_exhausted(n, result)
    else:
        accepted = False
    if not accepted:
        raise RuntimeError("refusing to publish an invalid search result")
    return dumps_certificate(result)


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "branch":
            result = attack_x(args.n, args.x)
            _write(_checked_output(result, args.n, args.x), args.output)
            return 0

        if args.command == "search":
            result = search_fixed_n(args.n, args.max_checks)
            if type(result) is Unknown:
                # This is a progress report, deliberately not a certificate.
                _write(_json({
                    "status": "unknown", "n": result.n,
                    "next_x": result.next_x, "checks_done": result.checks_done,
                    "closed_x": [branch.x for branch in result.closed_branches],
                    "reason": result.reason,
                }), args.output)
                return 3
            _write(_checked_output(result, args.n, None), args.output)
            return 0

        cert = loads_certificate(args.file.read_text(encoding="utf-8"))
        scope = {"n": args.n}
        if type(cert) is Exhausted:
            if args.x is not None:
                parser.error("--x is not allowed for an exhausted certificate")
            accepted = verify_exhausted(args.n, cert)
            kind = "exhausted"
        else:
            if args.x is None:
                parser.error("--x is required for witness and no_x certificates")
            scope["x"] = args.x
            if type(cert) is Witness:
                accepted = verify_witness(args.n, args.x, cert)
                kind = "witness"
            else:
                accepted = verify_no_x(args.n, args.x, cert)
                kind = "no_x"
        _write(_json({"accepted": accepted, "kind": kind, "scope": scope}), None)
        return 0 if accepted else 1
    except (OSError, UnicodeError, ValueError) as error:
        sys.stderr.write(_json({"status": "error", "error": str(error)}))
        return 2
