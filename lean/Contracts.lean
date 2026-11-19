import Std

/-!
# Scoped certificates for the Erdos-Straus equation

This module defines contracts and proves logical composition rules and a few
arithmetic leaves. It does not formalize the complete finite-search bounds,
verify the Python implementation, or prove the Erdos-Straus conjecture.

The task domain `2 ≤ n` is supplied by the caller. No floating-point arithmetic
or native decision procedure is used for the concrete examples.
-/

namespace ErdosStraus

/-- A positive-integer witness, expressed without division. -/
def ESWitness (n x y z : Nat) : Prop :=
  0 < x ∧ 0 < y ∧ 0 < z ∧
  4 * x * y * z = n * (x * y + x * z + y * z)

instance (n x y z : Nat) : Decidable (ESWitness n x y z) := by
  unfold ESWitness
  infer_instance

def ES (n : Nat) : Prop :=
  ∃ x y z : Nat, ESWitness n x y z

def checkWitness (n x y z : Nat) : Bool :=
  decide (ESWitness n x y z)

/-- An accepted concrete witness establishes existence at that input. -/
theorem acceptWitness {n x y z : Nat}
    (h : checkWitness n x y z = true) : ES n := by
  have hw : ESWitness n x y z := of_decide_eq_true h
  exact ⟨x, y, z, hw⟩

/-- Rejection of a witness excludes only this tuple. -/
theorem rejectWitness {n x y z : Nat}
    (h : checkWitness n x y z = false) :
    ¬ ESWitness n x y z := by
  exact of_decide_eq_false h

abbrev Branch := Nat → Nat → Nat → Prop

def HasSolution (n : Nat) (B : Branch) : Prop :=
  ∃ x y z : Nat, B x y z ∧ ESWitness n x y z

/-- The type fixes exactly which input and branch a certificate may close. -/
abbrev PruneCertificate (n : Nat) (B : Branch) : Prop :=
  ¬ HasSolution n B

def FixedX (x₀ : Nat) : Branch :=
  fun x y z => x = x₀ ∧ x ≤ y ∧ y ≤ z

/-- Closed children close the parent only when they cover it. -/
theorem mergePrunes {n : Nat} {P L R : Branch}
    (cover : ∀ x y z, P x y z → L x y z ∨ R x y z)
    (leftClosed : PruneCertificate n L)
    (rightClosed : PruneCertificate n R) :
    PruneCertificate n P := by
  intro h
  match h with
  | ⟨x, y, z, hP, hw⟩ =>
    cases cover x y z hP with
    | inl hL => exact leftClosed ⟨x, y, z, hL, hw⟩
    | inr hR => exact rightClosed ⟨x, y, z, hR, hw⟩

/--
The missing root-completeness proof is an explicit premise, not an axiom.
An ordered root need only preserve existence, not every permutation of a tuple.
-/
theorem noESOfRootClosed {n : Nat} {root : Branch}
    (complete : ES n → HasSolution n root)
    (closed : PruneCertificate n root) : ¬ ES n := by
  intro h
  exact closed (complete h)

/-- A counterexample to one fixed formula invalidates only its stated rule. -/
theorem rejectFormula {D : Nat → Prop} {fx fy fz : Nat → Nat}
    {n : Nat} (hn : D n)
    (bad : ¬ ESWitness n (fx n) (fy n) (fz n)) :
    ¬ (∀ m, D m → ESWitness m (fx m) (fy m) (fz m)) := by
  intro hall
  exact bad (hall n hn)

/--
Algebraic bridge from the original equation to the residual equation.
Using `4*x = n+a` avoids silently truncating natural-number subtraction.
-/
theorem witnessToResidual {n x y z a b : Nat}
    (hx : 4 * x = n + a)
    (hb : b = n * x)
    (hw : ESWitness n x y z) :
    a * y * z = b * (y + z) := by
  have hleft : 4 * x * y * z = n * y * z + a * y * z := by
    calc
      4 * x * y * z = (n + a) * y * z := by rw [hx]
      _ = (n * y + a * y) * z := by rw [Nat.add_mul]
      _ = n * y * z + a * y * z := by rw [Nat.add_mul]
  have hexpanded :
      n * y * z + a * y * z =
        n * x * y + n * x * z + n * y * z := by
    calc
      n * y * z + a * y * z = 4 * x * y * z := hleft.symm
      _ = n * (x * y + x * z + y * z) := hw.2.2.2
      _ = n * x * y + n * x * z + n * y * z := by
        simp only [Nat.mul_add, Nat.mul_assoc]
  have hreordered :
      a * y * z + n * y * z =
        (n * x * y + n * x * z) + n * y * z := by
    calc
      a * y * z + n * y * z = n * y * z + a * y * z :=
        Nat.add_comm _ _
      _ = (n * x * y + n * x * z) + n * y * z := hexpanded
  have hcancel : a * y * z = n * x * y + n * x * z :=
    Nat.add_right_cancel hreordered
  calc
    a * y * z = n * x * y + n * x * z := hcancel
    _ = b * y + b * z := by rw [hb]
    _ = b * (y + z) := (Nat.mul_add b y z).symm

/-- Additive splitting also avoids truncated subtraction for `c = a*y-b`. -/
theorem residualToLinear {a b c y z : Nat}
    (hsplit : a * y = b + c)
    (hres : a * y * z = b * (y + z)) :
    c * z = b * y := by
  have hsum : b * z + c * z = b * y + b * z := by
    calc
      b * z + c * z = (b + c) * z := (Nat.add_mul b c z).symm
      _ = (a * y) * z := by rw [hsplit]
      _ = b * (y + z) := hres
      _ = b * y + b * z := Nat.mul_add b y z
  have hreordered : c * z + b * z = b * y + b * z := by
    calc
      c * z + b * z = b * z + c * z := Nat.add_comm _ _
      _ = b * y + b * z := hsum
  exact Nat.add_right_cancel hreordered

theorem noZOfNotDvd {b c y : Nat} (h : ¬ c ∣ b * y) :
    ¬ (∃ z : Nat, c * z = b * y) := by
  intro hz
  cases hz with
  | intro z heq => exact h ⟨z, heq.symm⟩

/-- A checked non-divisibility leaf rules out every z for fixed n,x,y. -/
theorem noWitnessOfNondivisible {n x y a b c : Nat}
    (hx : 4 * x = n + a)
    (hb : b = n * x)
    (hsplit : a * y = b + c)
    (hnot : ¬ c ∣ b * y) :
    ¬ (∃ z : Nat, ESWitness n x y z) := by
  intro h
  cases h with
  | intro z hw =>
    have hres := witnessToResidual hx hb hw
    have hlinear := residualToLinear hsplit hres
    exact hnot ⟨z, hlinear.symm⟩

theorem fiveHasWitness : ESWitness 5 2 4 20 := by decide

theorem fiveHasSolution : ES 5 :=
  ⟨2, 4, 20, fiveHasWitness⟩

theorem badTupleAtFive : ¬ ESWitness 5 2 5 5 := by decide

-- These are genuine all-z exclusions for individual (n,x,y) leaves.
-- They do not on their own prove that all y at x=3 have been covered.
theorem fiveThreeThreeClosed : ¬ (∃ z : Nat, ESWitness 5 3 3 z) :=
  noWitnessOfNondivisible
    (a := 7) (b := 15) (c := 6)
    (by decide) (by decide) (by decide) (by decide)

theorem fiveThreeFourClosed : ¬ (∃ z : Nat, ESWitness 5 3 4 z) :=
  noWitnessOfNondivisible
    (a := 7) (b := 15) (c := 13)
    (by decide) (by decide) (by decide) (by decide)

-- Keep the transitive trust boundary visible in build logs.
#print axioms acceptWitness
#print axioms mergePrunes
#print axioms noESOfRootClosed
#print axioms rejectFormula
#print axioms noWitnessOfNondivisible
#print axioms fiveHasSolution
#print axioms fiveThreeThreeClosed
#print axioms fiveThreeFourClosed

end ErdosStraus
