module

public import Mathlib.Data.Fintype.Card
public import Mathlib.Combinatorics.Enumerative.DoubleCounting
public import Mathlib.Algebra.Group.Action.Defs

/-!
# Assignments of aggregators to subnets

An assignment says which subnets each aggregator proves.
Subnets and aggregators are finite types, so their numbers `S` and `A` stay parameters.
Coverage sets need not all have the same size, and subnets need not all have the same replication:
`HasDegree d` and `HasReplication k` state the uniform case of the prose definitions.

A scope with several instances, one per slot for example, is one assignment whose subnet and
aggregator types are disjoint unions; nothing below needs an assignment to be connected.
-/

set_option linter.unusedSectionVars false

@[expose] public section

namespace PQAggregation

variable {Sub Agg : Type} [Fintype Sub] [Fintype Agg] [DecidableEq Sub] [DecidableEq Agg]

/-- An assignment: the coverage set of each aggregator. -/
structure Assignment (Sub Agg : Type) where
  cover : Agg → Finset Sub

namespace Assignment

variable (σ : Assignment Sub Agg)

/-- The aggregators whose coverage set contains subnet `s`. -/
def aggsOf (s : Sub) : Finset Agg := Finset.univ.filter (fun a => s ∈ σ.cover a)

/-- The aggregators whose coverage set meets the set of subnets `L`. -/
def nbhd (L : Finset Sub) : Finset Agg := Finset.univ.filter (fun a => (σ.cover a ∩ L).Nonempty)

/-- Every aggregator covers exactly `d` subnets. -/
def HasDegree (d : ℕ) : Prop := ∀ a, (σ.cover a).card = d

/-- Every subnet is covered by exactly `k` aggregators: replication `k`. -/
def HasReplication (k : ℕ) : Prop := ∀ s, (σ.aggsOf s).card = k

/-- Redundant assignment: aggregators that share one subnet share all of them. -/
def Redundant : Prop := ∀ a b, (σ.cover a ∩ σ.cover b).Nonempty → σ.cover a = σ.cover b

/-- Dispersed assignment, in the weakest form the prose allows: the aggregators of a subnet
do not all have the same coverage set. -/
def Dispersed : Prop := ∀ s, ∃ a ∈ σ.aggsOf s, ∃ b ∈ σ.aggsOf s, σ.cover a ≠ σ.cover b

/-- Dispersed assignment in the strong form that the constructions use: two distinct
subnets share at most `λ` aggregators (`λ = 1` for the lines of an affine plane). -/
def PairwiseShare (lam : ℕ) : Prop := ∀ s t, s ≠ t → (σ.aggsOf s ∩ σ.aggsOf t).card ≤ lam

/-- The dual assignment: subnets become the "aggregators" and the reverse, so that statements
about sets of subnets turn into statements about sets of aggregators. -/
def dual : Assignment Agg Sub := ⟨σ.aggsOf⟩

instance (d : ℕ) : Decidable (σ.HasDegree d) := inferInstanceAs (Decidable (∀ _, _))
instance (k : ℕ) : Decidable (σ.HasReplication k) := inferInstanceAs (Decidable (∀ _, _))
instance : Decidable σ.Redundant := inferInstanceAs (Decidable (∀ _ _, _))
instance : Decidable σ.Dispersed := inferInstanceAs (Decidable (∀ _, _))
instance (lam : ℕ) : Decidable (σ.PairwiseShare lam) := inferInstanceAs (Decidable (∀ _ _, _))

theorem mem_aggsOf {s : Sub} {a : Agg} : a ∈ σ.aggsOf s ↔ s ∈ σ.cover a := by
  simp [aggsOf]

theorem aggsOf_subset_nbhd {L : Finset Sub} {s : Sub} (hs : s ∈ L) : σ.aggsOf s ⊆ σ.nbhd L := by
  intro a ha
  simp only [nbhd, Finset.mem_filter, Finset.mem_univ, true_and]
  exact ⟨s, Finset.mem_inter.2 ⟨(σ.mem_aggsOf).1 ha, hs⟩⟩

theorem dual_aggsOf (a : Agg) : σ.dual.aggsOf a = σ.cover a := by
  ext s; simp [aggsOf, dual]

/-- Double counting of incidences between a set of subnets and the aggregators meeting it. -/
theorem sum_aggsOf_eq (L : Finset Sub) :
    ∑ s ∈ L, (σ.aggsOf s).card = ∑ a ∈ σ.nbhd L, (σ.cover a ∩ L).card := by
  have h1 : ∀ s ∈ L, σ.aggsOf s = (σ.nbhd L).filter (fun a => s ∈ σ.cover a) := by
    intro s hs
    ext a
    simp only [Finset.mem_filter]
    exact ⟨fun h => ⟨σ.aggsOf_subset_nbhd hs h, (σ.mem_aggsOf).1 h⟩,
      fun h => (σ.mem_aggsOf).2 h.2⟩
  have h2 : ∀ a ∈ σ.nbhd L, σ.cover a ∩ L = L.filter (fun s => s ∈ σ.cover a) := by
    intro a _
    ext s
    simp [and_comm]
  rw [Finset.sum_congr rfl (fun s hs => congrArg Finset.card (h1 s hs)),
    Finset.sum_congr rfl (fun a ha => congrArg Finset.card (h2 a ha))]
  exact Finset.sum_card_bipartiteAbove_eq_sum_card_bipartiteBelow _

/-- `A·d = S·k`: the identity of the prose, as a theorem about uniform assignments. -/
theorem card_mul_degree {d k : ℕ} (hd : σ.HasDegree d) (hk : σ.HasReplication k) :
    Fintype.card Agg * d = Fintype.card Sub * k := by
  have h : ∑ s : Sub, (σ.aggsOf s).card = ∑ a : Agg, (σ.cover a).card := by
    have := Finset.sum_card_bipartiteAbove_eq_sum_card_bipartiteBelow
      (s := (Finset.univ : Finset Sub)) (t := (Finset.univ : Finset Agg))
      (r := fun s a => s ∈ σ.cover a)
    simpa [Finset.bipartiteAbove, Finset.bipartiteBelow, aggsOf] using this
  rw [Finset.sum_congr rfl (fun s _ => hk s), Finset.sum_congr rfl (fun a _ => hd a)] at h
  simp only [Finset.sum_const, Finset.card_univ, smul_eq_mul] at h
  rw [h, mul_comm]

end Assignment

end PQAggregation
