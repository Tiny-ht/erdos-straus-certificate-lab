"""Strict, versioned JSON transport for certificates.

Decoding validates the schema, not mathematical truth. Call the appropriate
scope-bound verify_* function after decoding. Unknown results are not proof
certificates and deliberately cannot be serialized with this interface.
"""

import json

from .core import SCHEMA_VERSION, Exhausted, NoX, Witness

SCHEMA = "erdos-straus-certificate"
Certificate = Witness | NoX | Exhausted


class CertificateError(ValueError):
    """Malformed, ambiguous, unsupported or wrongly typed certificate data."""


def _reject_number(value: str):
    raise CertificateError(f"noninteger JSON number is forbidden: {value}")


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CertificateError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _int(value, name: str, minimum: int | None = None):
    if type(value) is not int:
        raise CertificateError(f"{name} must be an integer, not bool/float/string")
    if minimum is not None and value < minimum:
        raise CertificateError(f"{name} must be at least {minimum}")
    return value


def _header(data, kind: str, fields: set[str]):
    if type(data) is not dict:
        raise CertificateError("certificate must be a JSON object")
    if set(data) != {"schema", "version", "kind"} | fields:
        raise CertificateError(f"unexpected or missing fields for {kind}")
    if data["schema"] != SCHEMA or data["kind"] != kind:
        raise CertificateError("wrong schema or certificate kind")
    if _int(data["version"], "version") != SCHEMA_VERSION:
        raise CertificateError("unsupported schema version")


def _parse_no_x(data):
    _header(data, "no_x", {"n", "x", "remainders"})
    n, x = _int(data["n"], "n", 2), _int(data["x"], "x")
    rows = data["remainders"]
    if type(rows) is not list:
        raise CertificateError("remainders must be an array")
    result = []
    for row in rows:
        if type(row) is not list or len(row) != 2:
            raise CertificateError("each remainder entry must be [y, remainder]")
        result.append((_int(row[0], "y"), _int(row[1], "remainder")))
    return NoX(n, x, tuple(result))


def _parse(data):
    if type(data) is not dict:
        raise CertificateError("certificate must be a JSON object")
    kind = data.get("kind")
    if kind == "witness":
        _header(data, kind, {"n", "x", "y", "z"})
        return Witness(
            _int(data["n"], "n", 2), _int(data["x"], "x"),
            _int(data["y"], "y"), _int(data["z"], "z"),
        )
    if kind == "no_x":
        return _parse_no_x(data)
    if kind == "exhausted":
        _header(data, kind, {"n", "branches"})
        n = _int(data["n"], "n", 2)
        if type(data["branches"]) is not list:
            raise CertificateError("branches must be an array")
        return Exhausted(n, tuple(_parse_no_x(branch) for branch in data["branches"]))
    raise CertificateError("unsupported certificate kind")


def loads_certificate(text: str) -> Certificate:
    if type(text) is not str:
        raise CertificateError("certificate input must be text")
    try:
        data = json.loads(
            text, parse_float=_reject_number, parse_constant=_reject_number,
            object_pairs_hook=_object,
        )
    except CertificateError:
        raise
    except (ValueError, RecursionError, OverflowError) as error:
        raise CertificateError(f"invalid JSON: {error}") from error
    return _parse(data)


def _to_data(cert: Certificate):
    header = {"schema": SCHEMA, "version": cert.version}
    if type(cert) is Witness:
        return {**header, "kind": "witness", "n": cert.n, "x": cert.x,
                "y": cert.y, "z": cert.z}
    if type(cert) is NoX:
        if type(cert.remainders) is not tuple:
            raise CertificateError("NoX remainders must be immutable tuples")
        if any(type(row) is not tuple or len(row) != 2 for row in cert.remainders):
            raise CertificateError("NoX entries must be pairs")
        return {**header, "kind": "no_x", "n": cert.n, "x": cert.x,
                "remainders": [list(row) for row in cert.remainders]}
    if type(cert) is Exhausted:
        if type(cert.branches) is not tuple or any(type(b) is not NoX for b in cert.branches):
            raise CertificateError("Exhausted branches must be an immutable tuple of NoX")
        return {**header, "kind": "exhausted", "n": cert.n,
                "branches": [_to_data(branch) for branch in cert.branches]}
    raise CertificateError("only Witness, NoX and Exhausted are certificates")


def dumps_certificate(cert: Certificate, *, indent: int | None = 2) -> str:
    if type(cert) not in (Witness, NoX, Exhausted):
        raise CertificateError("only Witness, NoX and Exhausted are certificates")
    data = _to_data(cert)
    # Validate types and version before encoding; this is not a truth check.
    _parse(data)
    return json.dumps(data, sort_keys=True, ensure_ascii=True, indent=indent) + "\n"
