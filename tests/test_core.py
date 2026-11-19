import unittest
from dataclasses import FrozenInstanceError, replace

from erdos_straus import (
    Exhausted, NoX, Unknown, Witness, attack_x, bounds, search_fixed_n,
    verify_exhausted, verify_no_x, verify_witness,
)
from erdos_straus.reference import solutions_by_factors


class ScopedCertificateTests(unittest.TestCase):
    def test_real_closed_branch_and_surviving_witness(self):
        closed = attack_x(5, 3)
        self.assertEqual(closed, NoX(5, 3, ((3, 3), (4, 8))))
        self.assertTrue(verify_no_x(5, 3, closed))
        found = attack_x(5, 2)
        self.assertEqual(found, Witness(5, 2, 4, 20))
        self.assertTrue(verify_witness(5, 2, found))

    def test_tampered_remainders_and_coverage_are_rejected(self):
        valid = attack_x(5, 3)
        for rows in [(), ((3, 3),), ((3, 3), (3, 8)), ((4, 8), (3, 3)),
                     ((3, 3), (4, 9)), ((3, 0), (4, 8)), ((3, 3), (4, -5))]:
            with self.subTest(rows=rows):
                self.assertFalse(verify_no_x(5, 3, replace(valid, remainders=rows)))

    def test_scope_and_version_are_bound(self):
        closed, found = attack_x(5, 3), attack_x(5, 2)
        self.assertFalse(verify_no_x(5, 2, closed))
        self.assertFalse(verify_no_x(6, 3, closed))
        self.assertFalse(verify_witness(5, 3, found))
        self.assertFalse(verify_witness(6, 2, found))
        for version in (0, 2, True, 1.0):
            self.assertFalse(verify_no_x(5, 3, replace(closed, version=version)))
            self.assertFalse(verify_witness(5, 2, replace(found, version=version)))

    def test_certificates_are_immutable(self):
        with self.assertRaises(FrozenInstanceError):
            attack_x(5, 3).x = 2

    def test_malformed_in_memory_certificates_fail_closed(self):
        for rows in ([ [3, 3], [4, 8] ], ((3, 3.0), (4, 8)),
                     ((3, True), (4, 8)), ((3, 3, 9), (4, 8)), (None, None)):
            self.assertFalse(verify_no_x(5, 3, NoX(5, 3, rows)))
        self.assertFalse(verify_witness(5, 2, Witness(5, 2, 4.0, 20)))
        self.assertFalse(verify_witness(2, 1, Witness(2, True, 2, 2)))
        self.assertFalse(verify_no_x(5, 3, False))

    def test_wrong_witness_is_not_a_negative_certificate(self):
        invalid = Witness(5, 2, 5, 5)
        self.assertFalse(verify_witness(5, 2, invalid))
        self.assertFalse(verify_no_x(5, 2, invalid))

    def test_input_errors_are_explicit(self):
        for invalid in (True, 2.0, "5", 1, 0, -1):
            with self.subTest(n=invalid), self.assertRaises(ValueError):
                attack_x(invalid, 2)
        for invalid in (True, 2.0, "2"):
            with self.assertRaises(ValueError):
                attack_x(5, invalid)
        for invalid in (True, 1.0, -1):
            with self.assertRaises(ValueError):
                search_fixed_n(5, max_checks=invalid)

    def test_out_of_range_x_is_a_scoped_empty_branch(self):
        for x in (-10, 0, 1, 4, 100):
            cert = attack_x(5, x)
            self.assertEqual(cert, NoX(5, x, ()))
            self.assertTrue(verify_no_x(5, x, cert))
            self.assertFalse(verify_no_x(5, x, replace(cert, remainders=((1, 1),))))

    def test_budget_exhaustion_is_unknown(self):
        result = search_fixed_n(5, max_checks=0)
        self.assertEqual(result, Unknown(5, (), 2, 0))
        self.assertFalse(verify_exhausted(5, result))
        self.assertFalse(verify_no_x(5, 2, result))
        self.assertIsInstance(search_fixed_n(5, max_checks=1), Witness)

    def test_budget_cannot_publish_a_partial_x_as_closed(self):
        # Find a small input requiring more than one initial y check.
        candidate = next(n for n in range(2, 200) if isinstance(search_fixed_n(n, 1), Unknown))
        result = search_fixed_n(candidate, 1)
        self.assertEqual(result.checks_done, 1)
        self.assertNotIn(result.next_x, [b.x for b in result.closed_branches])
        self.assertFalse(verify_exhausted(candidate, result))

    def test_root_rejects_partial_or_fabricated_coverage(self):
        closed = attack_x(5, 3)
        for branches in ((), (closed,), (closed, closed),
                         (NoX(5, 2, ()), closed), (NoX(5, 1, ()), closed)):
            self.assertFalse(verify_exhausted(5, Exhausted(5, branches)))
        self.assertFalse(verify_exhausted(5, Exhausted(6, ())))

    def test_factor_check_covers_2558_branches(self):
        checked = 0
        for n in range(2, 81):
            for x in range(1, (3*n)//4 + 3):
                expected = solutions_by_factors(n, x)
                actual = set()
                data = bounds(n, x)
                if data is not None:
                    a, b, lo, hi = data
                    for y in range(lo, hi + 1):
                        z, remainder = divmod(b*y, a*y-b)
                        if remainder == 0:
                            actual.add((y, z))
                self.assertEqual(actual, expected, (n, x))
                result = attack_x(n, x)
                if type(result) is Witness:
                    self.assertTrue(verify_witness(n, x, result))
                    self.assertIn((result.y, result.z), expected)
                else:
                    self.assertTrue(verify_no_x(n, x, result))
                    self.assertFalse(expected)
                checked += 1
        self.assertEqual(checked, 2558)


if __name__ == "__main__":
    unittest.main()
