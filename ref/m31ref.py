"""Reference checker for the m31-vmatmul/v1 relation. Stdlib only.
Normative for byte encodings; semantics live in M31/Spec.lean."""
from __future__ import annotations

import hashlib
import struct
from typing import List, Sequence

P = (1 << 31) - 1      # Mersenne prime 2^31 - 1
HALF = (P - 1) // 2    # largest representative treated as non-negative
T = 6                  # Freivalds repetitions

Matrix = List[List[int]]


class VerifyError(Exception):
    pass


def u32(x: int) -> bytes:
    return struct.pack(">I", x)


def check_matrix(name: str, M: Sequence[Sequence[int]]) -> tuple:
    rows = len(M)
    cols = len(M[0]) if rows else 0
    if rows == 0 or cols == 0:
        raise VerifyError(f"{name}: empty")
    if rows > 0xFFFFFFFF or cols > 0xFFFFFFFF:
        raise VerifyError(f"{name}: too large")
    for row in M:
        if len(row) != cols:
            raise VerifyError(f"{name}: ragged")
        if any(type(x) is not int or not 0 <= x < P for x in row):
            raise VerifyError(f"{name}: non-canonical entry")
    return rows, cols


def tensor_digest(M: Matrix) -> bytes:
    h = hashlib.sha256(b"m31-vmatmul/v1/tensor")
    h.update(u32(len(M)) + u32(len(M[0])))
    for row in M:
        for x in row:
            h.update(u32(x))
    return h.digest()


def matmul(A: Matrix, B: Matrix) -> Matrix:
    k = len(B[0])
    out = []
    for row in A:
        acc = [0] * k
        for t, a in enumerate(row):
            Bt = B[t]
            for j in range(k):
                acc[j] += a * Bt[j]
        out.append([x % P for x in acc])
    return out


def matvec(M: Matrix, v: Sequence[int]) -> List[int]:
    return [sum(a * x for a, x in zip(row, v)) % P for row in M]


def relu(x: int) -> int:
    return x if x <= HALF else 0


def challenge_seed(A: Matrix, B: Matrix, C: Matrix) -> bytes:
    h = hashlib.sha256(b"m31-vmatmul/v1/challenge")
    for X in (A, B, C):
        h.update(tensor_digest(X))
    return h.digest()


def sample_field(seed: bytes, t: int, l: int) -> int:
    """Uniform in [0, p) by rejection; only the value 2^31 - 1 is ever rejected."""
    ctr = 0
    while True:
        d = hashlib.sha256(b"m31-vmatmul/v1/beta" + seed + u32(t) + u32(l) + u32(ctr)).digest()
        v = int.from_bytes(d[:4], "big") & 0x7FFFFFFF
        if v < P:
            return v
        ctr += 1


def challenge_vectors(seed: bytes, k: int, reps: int = T) -> List[List[int]]:
    return [[sample_field(seed, t, l) for l in range(k)] for t in range(reps)]


def verify_matmul(A: Matrix, B: Matrix, C: Matrix, reps: int = T) -> None:
    m, n = check_matrix("A", A)
    n2, k = check_matrix("B", B)
    m2, k2 = check_matrix("C", C)
    if (m, n, k) != (m2, n2, k2):
        raise VerifyError("shape mismatch")
    seed = challenge_seed(A, B, C)
    for beta in challenge_vectors(seed, k, reps):
        if matvec(A, matvec(B, beta)) != matvec(C, beta):
            raise VerifyError("Freivalds check failed")


def verify_layer(A: Matrix, B: Matrix, C: Matrix, Y: Matrix) -> None:
    verify_matmul(A, B, C)
    check_matrix("Y", Y)
    if Y != [[relu(x) for x in row] for row in C]:
        raise VerifyError("ReLU output mismatch")


def prove_layer(A: Matrix, B: Matrix):
    C = matmul(A, B)
    return C, [[relu(x) for x in row] for row in C]


GENESIS = hashlib.sha256(b"m31-vmatmul/v1/genesis").digest()


def statement_digest(A: Matrix, B: Matrix, C: Matrix, Y: Matrix) -> bytes:
    h = hashlib.sha256(b"m31-vmatmul/v1/stmt")
    for X in (A, B, C, Y):
        h.update(tensor_digest(X))
    return h.digest()


def chain_fold(prev: bytes, stmt: bytes, index: int) -> bytes:
    return hashlib.sha256(b"m31-vmatmul/v1/chain" + prev + u32(index) + stmt).digest()
