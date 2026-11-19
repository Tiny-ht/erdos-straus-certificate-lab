import json
import unittest

from erdos_straus import (
    CertificateError, Exhausted, NoX, Unknown, Witness, attack_x,
    dumps_certificate, loads_certificate, verify_no_x,
)


class StrictTransportTests(unittest.TestCase):
    def test_roundtrips(self):
        for cert in (attack_x(5, 2), attack_x(5, 3), Exhausted(5, (attack_x(5, 3),))):
            self.assertEqual(loads_certificate(dumps_certificate(cert)), cert)

    def test_decode_does_not_promote_a_false_claim(self):
        bad = NoX(5, 3, ((3, 3), (4, 9)))
        decoded = loads_certificate(dumps_certificate(bad))
        self.assertFalse(verify_no_x(5, 3, decoded))

    def test_extra_missing_or_unsupported_fields_are_rejected(self):
        data = json.loads(dumps_certificate(attack_x(5, 3)))
        mutations = [dict(data, upper_bound=100), dict(data, version=2),
                     dict(data, kind="unknown"), dict(data, schema="other")]
        missing = dict(data)
        missing.pop("x")
        mutations.append(missing)
        for invalid in mutations:
            with self.assertRaises(CertificateError):
                loads_certificate(json.dumps(invalid))

    def test_bool_float_and_wrong_types_are_rejected(self):
        data = json.loads(dumps_certificate(attack_x(5, 3)))
        mutations = [dict(data, n=True), dict(data, n=5.0), dict(data, x="3"),
                     dict(data, version=True), dict(data, remainders="bad"),
                     dict(data, remainders=[[3, True], [4, 8]]),
                     dict(data, remainders=[[3, 3, 0], [4, 8]])]
        for invalid in mutations:
            with self.assertRaises(CertificateError):
                loads_certificate(json.dumps(invalid))
        for text in ("NaN", "Infinity", "-Infinity", "[]", "null", "{"):
            with self.assertRaises(CertificateError):
                loads_certificate(text)

    def test_duplicate_json_keys_are_rejected(self):
        text = dumps_certificate(attack_x(5, 3)).replace('"n": 5', '"n": 5, "n": 7')
        with self.assertRaises(CertificateError):
            loads_certificate(text)

    def test_unknown_cannot_be_serialized_as_a_certificate(self):
        with self.assertRaises(CertificateError):
            dumps_certificate(Unknown(5, (), 2, 0))

    def test_serialization_also_validates_types(self):
        for cert in (Witness(5, 2, 4.0, 20), NoX(5, 3, [(3, 3), (4, 8)]),
                     NoX(5, 3, ((3, True), (4, 8)))):
            with self.assertRaises(CertificateError):
                dumps_certificate(cert)


if __name__ == "__main__":
    unittest.main()
