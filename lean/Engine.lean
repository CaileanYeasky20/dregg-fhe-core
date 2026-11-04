import Mathlib

/-!
# m31-vmatmul/v1 — Lean specification

In scope: field and ReLU conventions, matrix product, the Freivalds identity.
-/

namespace M31

/-- The Mersenne prime `2^31 - 1`. -/
def p : ℕ := 2147483647

theorem p_eq : p = 2 ^ 31 - 1 := by norm_num [p]

/-- Largest canonical representative treated as non-negative. -/
def half : ℕ := (p - 1) / 2

theorem half_eq : half = 1073741823 := by norm_num [half, p]

/-- ReLU on canonical representatives (ℕ model). -/
def reluNat (x : ℕ) : ℕ := if x ≤ half then x else 0

example : reluNat 0 = 0 := by decide
example : reluNat half = half := by decide
example : reluNat (half + 1) = 0 := by decide
example : reluNat (p - 1) = 0 := by decide

/-- ReLU on `ZMod p`, stated through `ZMod.val`. -/
def relu (x : ZMod p) : ZMod p := if x.val ≤ half then x else 0

theorem relu_val (x : ZMod p) : (relu x).val = reluNat x.val := by
  unfold relu reluNat
  split_ifs <;> simp

/-- Matrices as functions, mirroring row-major arrays. -/
abbrev Mat (F : Type*) (m n : ℕ) := Fin m → Fin n → F

section Algebra

variable {F : Type*} [Semiring F]

def mul {m n k : ℕ} (A : Mat F m n) (B : Mat F n k) (i : Fin m) (l : Fin k) : F :=
  ∑ j, A i j * B j l

def mulVec {m n : ℕ} (A : Mat F m n) (v : Fin n → F) (i : Fin m) : F :=
  ∑ j, A i j * v j

theorem mulVec_mul {m n k : ℕ} (A : Mat F m n) (B : Mat F n k) (v : Fin k → F) :
    mulVec A (mulVec B v) = mulVec (mul A B) v := by
  funext i
  simp only [mulVec, mul, Finset.mul_sum, Finset.sum_mul, mul_assoc]
  exact Finset.sum_comm

theorem eq_of_mulVec_single {m k : ℕ} (D E : Mat F m k)
    (h : ∀ j : Fin k, mulVec D (Pi.single j 1) = mulVec E (Pi.single j 1)) : D = E := by
  funext i j
  have hij := congrFun (h j) i
  simpa [mulVec, Pi.single_apply, mul_ite, Finset.sum_ite_eq, Finset.sum_ite_eq'] using hij

def accepts {m n k : ℕ} (A : Mat F m n) (B : Mat F n k) (C : Mat F m k) (β : Fin k → F) : Prop :=
  mulVec A (mulVec B β) = mulVec C β

theorem accepts_mul {m n k : ℕ} (A : Mat F m n) (B : Mat F n k) (β : Fin k → F) :
    accepts A B (mul A B) β :=
  mulVec_mul A B β

theorem eq_mul_of_accepts_basis {m n k : ℕ} (A : Mat F m n) (B : Mat F n k) (C : Mat F m k)
    (h : ∀ j : Fin k, accepts A B C (Pi.single j 1)) : C = mul A B := by
  apply eq_of_mulVec_single
  intro j
  have hj : mulVec A (mulVec B (Pi.single j 1)) = mulVec C (Pi.single j 1) := h j
  exact hj.symm.trans (mulVec_mul A B _)

end Algebra

def LayerOk {m n k : ℕ} (A : Mat (ZMod p) m n) (B : Mat (ZMod p) n k)
    (C Y : Mat (ZMod p) m k) (βs : List (Fin k → ZMod p)) : Prop :=
  (∀ β ∈ βs, accepts A B C β) ∧ ∀ i l, Y i l = relu (C i l)

theorem layer_complete {m n k : ℕ} (A : Mat (ZMod p) m n) (B : Mat (ZMod p) n k)
    (βs : List (Fin k → ZMod p)) :
    LayerOk A B (mul A B) (fun i l => relu (mul A B i l)) βs :=
  ⟨fun β _ => accepts_mul A B β, fun _ _ => rfl⟩

end M31

#print axioms M31.mulVec_mul
#print axioms M31.eq_mul_of_accepts_basis
#print axioms M31.layer_complete
#print axioms M31.relu_val
