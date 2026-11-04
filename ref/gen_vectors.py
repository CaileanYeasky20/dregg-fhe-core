"""Emit vectors/vectors.json. Deterministic: explicit inputs, no RNG."""
import hashlib
import json
from pathlib import Path

from m31ref import (GENESIS, HALF, P, T, VerifyError, chain_fold, challenge_seed,
                    challenge_vectors, prove_layer, relu, statement_digest,
                    tensor_digest, verify_layer)

VECTORS_PATH = Path(__file__).resolve().parent.parent / "vectors" / "vectors.json"


def det_matrix(label, rows, cols):
    out = []
    for i in range(rows):
        row = []
        for j in range(cols):
            ctr = 0
            while True:
                d = hashlib.sha256(f"{label}|{i}|{j}|{ctr}".encode()).digest()
                v = int.from_bytes(d[:4], "big") & 0x7FFFFFFF
                if v < P:
                    row.append(v)
                    break
                ctr += 1
        out.append(row)
    return out


def _case(name, A, B, C, Y, ok):
    case = {"name": name, "A": A, "B": B, "C": C, "Y": Y, "expect_ok": ok}
    if ok:
        seed = challenge_seed(A, B, C)
        case["digests"] = {k: tensor_digest(X).hex()
                           for k, X in (("A", A), ("B", B), ("C", C), ("Y", Y))}
        case["challenge_seed"] = seed.hex()
        case["betas"] = challenge_vectors(seed, len(B[0]))
        case["statement_digest"] = statement_digest(A, B, C, Y).hex()
    return case


def _honest(name, A, B):
    C, Y = prove_layer(A, B)
    return _case(name, A, B, C, Y, True)


def build():
    A1, B1 = det_matrix("A1", 3, 4), det_matrix("B1", 4, 2)
    C1, Y1 = prove_layer(A1, B1)
    bad_C = [r[:] for r in C1]
    bad_C[1][0] = (bad_C[1][0] + 1) % P
    bad_Y = [r[:] for r in Y1]
    bad_Y[0][0] = (bad_Y[0][0] + 1) % P
    bad_A = [r[:] for r in A1]
    bad_A[0][0] = P  # non-canonical
    layers = [
        _honest("honest_3x4_4x2", A1, B1),
        _honest("honest_1x6_6x3", det_matrix("A2", 1, 6), det_matrix("B2", 6, 3)),
        _honest("relu_at_half", [[1]], [[HALF]]),
        _honest("relu_just_above_half", [[1]], [[HALF + 1]]),
        _honest("relu_wraps_to_one", [[2]], [[HALF + 1]]),
        _honest("relu_p_minus_one", [[1]], [[P - 1]]),
        _case("reject_tampered_C", A1, B1, bad_C, [[relu(x) for x in r] for r in bad_C], False),
        _case("reject_tampered_Y", A1, B1, C1, bad_Y, False),
        _case("reject_noncanonical_A", bad_A, B1, C1, Y1, False),
        _case("reject_shape_mismatch", A1, A1, C1, Y1, False),
    ]
    for c in layers:
        try:
            verify_layer(c["A"], c["B"], c["C"], c["Y"])
            accepted = True
        except VerifyError:
            accepted = False
        assert accepted == c["expect_ok"], c["name"]

    ok_layers = [c for c in layers if c["expect_ok"]]
    root, roots = GENESIS, []
    for i, c in enumerate(ok_layers):
        root = chain_fold(root, bytes.fromhex(c["statement_digest"]), i)
        roots.append(root.hex())
    xs = [0, 1, HALF - 1, HALF, HALF + 1, HALF + 2, P - 2, P - 1]
    return {
        "spec": "m31-vmatmul/v1",
        "p": P,
        "reps": T,
        "relu_cases": [[x, relu(x)] for x in xs],
        "layers": layers,
        "chain": {"genesis": GENESIS.hex(), "layers": [c["name"] for c in ok_layers],
                  "roots": roots},
    }


def main():
    VECTORS_PATH.parent.mkdir(parents=True, exist_ok=True)
    VECTORS_PATH.write_text(json.dumps(build(), indent=1, sort_keys=True) + "\n")
    print(f"wrote {VECTORS_PATH}")


if __name__ == "__main__":
    main()
