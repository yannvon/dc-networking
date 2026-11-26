module

public import PQAggregation.FaultTolerance
public import Mathlib.Algebra.BigOperators.Ring.Finset
public import Mathlib.Algebra.Ring.Basic

/-!
# Random failures

Each aggregator fails independently with probability `p`. The probability of an event on the
failure set is written out as a finite sum over failure sets, so no measure theory is needed:
`prob p E = ∑_{F ∈ E} p^|F| (1 − p)^(A − |F|)`.

Two facts follow under any assignment:

* a subnet is lost with probability `p^k`, where `k` is its replication;
* the expected number of lost votes is `∑_s w s · p^(k_s)`, so with uniform replication it does not
  depend on the assignment at all. An assignment changes only which losses come together, and so
  the tail of the loss, not its mean.

Capture is the same computation with `p = β` and `F` the aggregators an attacker holds, when each
aggregator is the attacker's independently with probability `β`. A draw without replacement from a
finite stake distribution is not of this form, and gives a slightly smaller value.
-/

set_option linter.unusedSectionVars false

@[expose] public section

namespace PQAggregation

open Finset

variable {Sub Agg : Type} [Fintype Sub] [Fintype Agg] [DecidableEq Sub] [DecidableEq Agg]
variable {R : Type} [CommRing R]

/-- The probability of the event `E` on failure sets, when each aggregator fails independently
with probability `p`. -/
def prob (p : R) (E : Finset Agg → Prop) [DecidablePred E] : R :=
  ∑ F ∈ univ.filter E, p ^ F.card * (1 - p) ^ (Fintype.card Agg - F.card)

/-- The independent failures form a probability distribution. -/
theorem prob_true (p : R) : prob (Agg := Agg) p (fun _ => True) = 1 := by
  unfold prob
  rw [filter_true_of_mem (fun _ _ => trivial), ← powerset_univ, ← card_univ,
    sum_pow_mul_eq_add_pow, add_sub_cancel, one_pow]

/-- All aggregators of a set `T` fail with probability `p^|T|`. -/
theorem prob_superset (p : R) (T : Finset Agg) :
    prob p (fun F => T ⊆ F) = p ^ T.card := by
  unfold prob
  have himg : univ.filter (fun F => T ⊆ F) = (Tᶜ).powerset.image (fun G => T ∪ G) := by
    ext F
    simp only [mem_filter, mem_univ, true_and, mem_image, mem_powerset]
    constructor
    · intro h
      refine ⟨F \ T, ?_, union_sdiff_of_subset h⟩
      intro a ha
      simp only [mem_compl]
      exact (mem_sdiff.1 ha).2
    · rintro ⟨G, _, rfl⟩
      exact subset_union_left
  have hdisj : ∀ G ∈ (Tᶜ).powerset, Disjoint T G := by
    intro G hG
    rw [mem_powerset] at hG
    exact disjoint_of_subset_right hG disjoint_compl_right
  have hinj : Set.InjOn (fun G => T ∪ G) ((Tᶜ).powerset : Set (Finset Agg)) := by
    intro G hG H hH h
    have hG' := hdisj G hG
    have hH' := hdisj H hH
    simp only at h
    rw [← (union_sdiff_cancel_left hG'), ← (union_sdiff_cancel_left hH'), h]
  rw [himg, sum_image hinj]
  have hc : ∀ G ∈ (Tᶜ).powerset, p ^ (T ∪ G).card * (1 - p) ^ (Fintype.card Agg - (T ∪ G).card)
      = p ^ T.card * (p ^ G.card * (1 - p) ^ ((Tᶜ).card - G.card)) := by
    intro G hG
    rw [card_union_of_disjoint (hdisj G hG), card_compl, pow_add, mul_assoc]
    congr 3
    omega
  rw [sum_congr rfl hc, ← mul_sum, sum_pow_mul_eq_add_pow, add_sub_cancel, one_pow, mul_one]

namespace Assignment

variable (σ : Assignment Sub Agg)

/-- **Random loss.** A subnet is lost with probability `p^k`, `k` its replication, under any
assignment. -/
theorem prob_lost (p : R) (s : Sub) :
    prob p (fun F => s ∈ σ.lost F) = p ^ (σ.aggsOf s).card := by
  rw [← prob_superset]
  unfold prob
  congr 1
  ext F
  simp [σ.mem_lost]

/-- **Expected loss.** The expected number of votes without a proof is `∑_s w s · p^(k_s)`. -/
theorem expected_loss (p : R) (w : Sub → ℕ) :
    ∑ F : Finset Agg, p ^ F.card * (1 - p) ^ (Fintype.card Agg - F.card) *
        ((∑ s ∈ σ.lost F, w s : ℕ) : R)
      = ∑ s, (w s : R) * p ^ (σ.aggsOf s).card := by
  simp_rw [Nat.cast_sum, mul_sum]
  rw [sum_comm' (t' := univ) (s' := fun s => univ.filter (fun F => s ∈ σ.lost F))
    (h := by intro F s; simp)]
  refine sum_congr rfl (fun s _ => ?_)
  rw [← σ.prob_lost p s, prob, mul_sum]
  refine sum_congr rfl (fun F _ => ?_)
  ring

/-- With uniform replication `k` the expected loss is the same for every assignment. -/
theorem expected_loss_uniform (p : R) (w : Sub → ℕ) {k : ℕ} (hk : σ.HasReplication k) :
    ∑ F : Finset Agg, p ^ F.card * (1 - p) ^ (Fintype.card Agg - F.card) *
        ((∑ s ∈ σ.lost F, w s : ℕ) : R)
      = ((∑ s, w s : ℕ) : R) * p ^ k := by
  rw [σ.expected_loss, Nat.cast_sum, sum_mul]
  exact sum_congr rfl (fun s _ => by rw [hk s])

end Assignment

end PQAggregation
