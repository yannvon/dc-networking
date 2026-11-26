module

public import PQAggregation.Assignment
public import Mathlib.Algebra.Order.BigOperators.Group.List
public import Mathlib.Algebra.Order.BigOperators.Group.Finset
public import Mathlib.Tactic.Ring

/-!
# Merges and work

## Merges

A proof covers a set of votes. An aggregator's proof covers votes of its coverage set. A merge
proves the union of at most `m` child proofs, and may add raw signatures of its own; children
may overlap. `Provable base m r h X` says that `X` is covered by a proof of at most `h` merge
levels over proofs in `base`, adding at most `r` raw signatures per merge.

Publishing any subset of what a node verified is not a separate rule here: coverage is what is
proved, and a smaller proof is another proof of the same shape.

## Redundant work

Replication is redundancy: under every assignment with replication `k`, the first level proves each
vote `k` times. So the share `(k − 1)/k` of redundant first-level proving is not a property of the
redundant assignment, as the prose had it; dispersal moves the duplicates into different proofs,
where a merge must take them as overlapping children, but does not remove them.
-/

set_option linter.unusedSectionVars false

@[expose] public section

namespace PQAggregation

open Finset

variable {V : Type} [DecidableEq V]

/-- Proofs of at most `h` merge levels over `base`, with fan-in `m` and up to `r` raw
signatures added per merge. -/
inductive Provable (base : Finset V → Prop) (m r : ℕ) : ℕ → Finset V → Prop
  | leaf {X} : base X → Provable base m r 0 X
  | lift {h X} : Provable base m r h X → Provable base m r (h + 1) X
  | merge {h} (cs : List (Finset V)) (R : Finset V) :
      cs.length ≤ m → R.card ≤ r → (∀ X ∈ cs, Provable base m r h X) →
      Provable base m r (h + 1) (R ∪ cs.foldr (fun A B : Finset V => A ∪ B) ∅)

/-- The most votes a proof of `h` levels can cover when base proofs cover at most `c`. -/
def coverBound (m r c : ℕ) : ℕ → ℕ
  | 0 => c
  | h + 1 => max (coverBound m r c h) (r + m * coverBound m r c h)

theorem card_foldr_union_le (cs : List (Finset V)) :
    (cs.foldr (fun A B : Finset V => A ∪ B) ∅).card ≤ (cs.map Finset.card).sum := by
  induction cs with
  | nil => simp
  | cons X cs ih =>
    simp only [List.foldr_cons, List.map_cons, List.sum_cons]
    exact (card_union_le _ _).trans (by omega)

/-- **Merge bound.** A proof of `h` levels with fan-in `m` covers at most `coverBound h` votes.
With no raw signatures added above the base, that is `m^h · c`: covering `N` votes from base
proofs of `c` votes each takes `m^h · c ≥ N`, under every assignment. -/
theorem Provable.card_le {base : Finset V → Prop} {m r c h : ℕ} {X : Finset V}
    (hbase : ∀ Y, base Y → Y.card ≤ c) (hX : Provable base m r h X) :
    X.card ≤ coverBound m r c h := by
  induction hX with
  | leaf hY => exact hbase _ hY
  | lift _ ih => exact ih.trans (le_max_left _ _)
  | @merge h cs R hlen hR _ ih =>
    refine le_trans ?_ (le_max_right _ _)
    have hsum : (cs.map Finset.card).sum ≤ cs.length * coverBound m r c h := by
      have := List.sum_le_length_nsmul (cs.map Finset.card) (coverBound m r c h)
        (by intro x hx; obtain ⟨Y, hY, rfl⟩ := List.mem_map.1 hx; exact ih Y hY)
      simpa using this
    calc (R ∪ cs.foldr (fun A B : Finset V => A ∪ B) ∅).card
          ≤ R.card + (cs.foldr (fun A B : Finset V => A ∪ B) ∅).card := card_union_le _ _
      _ ≤ r + cs.length * coverBound m r c h := by
          have := card_foldr_union_le cs; omega
      _ ≤ r + m * coverBound m r c h := by
          have := Nat.mul_le_mul_right (coverBound m r c h) hlen; omega

theorem coverBound_zero_raw (m c h : ℕ) (hm : 1 ≤ m) : coverBound m 0 c h = m ^ h * c := by
  induction h with
  | zero => simp [coverBound]
  | succ h ih =>
    simp only [coverBound, ih, zero_add]
    have : m ^ h * c ≤ m * (m ^ h * c) := Nat.le_mul_of_pos_left _ hm
    rw [max_eq_right this, pow_succ]
    ring

namespace Assignment

variable {Sub Agg : Type} [Fintype Sub] [Fintype Agg] [DecidableEq Sub] [DecidableEq Agg]
variable (σ : Assignment Sub Agg)

/-- **First-level work.** With replication `k`, the aggregators together prove `k` times the
votes of the scope, under every assignment. -/
theorem sum_cover_weight (w : Sub → ℕ) {k : ℕ} (hk : σ.HasReplication k) :
    ∑ a, ∑ s ∈ σ.cover a, w s = k * ∑ s, w s := by
  have : ∑ a, ∑ s ∈ σ.cover a, w s = ∑ s, (σ.aggsOf s).card * w s := by
    rw [sum_comm' (t' := univ) (s' := fun s => σ.aggsOf s) (h := by intro a s; simp [mem_aggsOf])]
    simp
  rw [this, mul_sum]
  exact sum_congr rfl (fun s _ => by rw [hk s])

end Assignment

end PQAggregation
