import json
import unittest

from gen_vectors import VECTORS_PATH, build, det_matrix
from m31ref import (HALF, P, VerifyError, matmul, matvec, prove_layer, relu,
                    verify_layer, verify_matmul)


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.A = det_matrix("tA", 3, 4)
        self.B = det_matrix("tB", 4, 2)
        self.C, self.Y = prove_layer(self.A, self.B)

    def test_relu_boundary(self):
        self.assertEqual([relu(x) for x in (0, HALF, HALF + 1, P - 1)], [0, HALF, 0, 0])

    def test_honest_layer_verifies(self):
        verify_layer(self.A, self.B, self.C, self.Y)

    def test_every_single_entry_tamper_is_rejected(self):
        for i in range(3):
            for j in range(2):
                bad = [r[:] for r in self.C]
                bad[i][j] = (bad[i][j] + 1) % P
                with self.assertRaises(VerifyError):
                    verify_matmul(self.A, self.B, bad)

    def test_tampered_relu_output_is_rejected(self):
        bad = [r[:] for r in self.Y]
        bad[0][0] = (bad[0][0] + 1) % P
        with self.assertRaises(VerifyError):
            verify_layer(self.A, self.B, self.C, bad)

    def test_noncanonical_encoding_is_rejected(self):
        bad = [r[:] for r in self.C]
        bad[0][0] += P  # same residue, different bytes
        with self.assertRaises(VerifyError):
            verify_matmul(self.A, self.B, bad)

    def test_shape_mismatch_is_rejected(self):
        with self.assertRaises(VerifyError):
            verify_matmul(self.A, self.A, self.C)

    def test_maximal_entries_do_not_overflow(self):
        n = 1000
        A = [[P - 1] * n for _ in range(2)]
        B = [[P - 1] * 2 for _ in range(n)]
        C = matmul(A, B)
        self.assertEqual(C, [[n, n], [n, n]])
        verify_matmul(A, B, C)

    def test_committed_vectors_are_current(self):
        self.assertTrue(VECTORS_PATH.exists(), "run: python ref/gen_vectors.py")
        self.assertEqual(json.loads(VECTORS_PATH.read_text()), build())


if __name__ == "__main__":
    unittest.main()
