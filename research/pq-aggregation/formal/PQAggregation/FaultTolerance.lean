module

public import PQAggregation.Assignment
public import Mathlib.Data.Fintype.Powerset
public import Mathlib.Algebra.Order.BigOperators.Group.Finset
public import Mathlib.Algebra.Order.Floor.Semiring
public import Mathlib.Data.Rat.Floor

/-!
# Fault tolerance

A failure is a set `F` of aggregators that publish nothing. Withholding, crashing and being flooded
all count as failure here: soundness means a faulty aggregator cannot prove a vote that was not
signed, so for coverage the worst it can do is publish nothing.
Capture is the same event with `F` the attacker's aggregators.

A subnet is lost under `F` when every aggregator that covers it is in `F`.
This is the model without a fallback; `Recovery.lean` adds one.

The tolerance of a loss criterion `Bad` is the fewest failures, chosen by an attacker who knows
the assignment, whose lost set satisfies `Bad`. It is `⊤` when no failure set does.
Per-vote tolerance, threshold tolerance `t(q)` and the tolerance of a multi-instance scope are all
instances: they differ only in `Bad`.
-/

set_option linter.unusedSectionVars false

@[expose] public section

namespace PQAggregation

open Finset

variable {Sub Agg : Type} [Fintype Sub] [Fintype Agg] [DecidableEq Sub] [DecidableEq Agg]

namespace Assignment

variable (σ : Assignment Sub Agg)

/-! ## Lost subnets -/

/-- The subnets left without a proof when the aggregators in `F` fail. -/
def lost (F : Finset Agg) : Finset Sub := univ.filter (fun s => σ.aggsOf s ⊆ F)

theorem mem_lost {F : Finset Agg} {s : Sub} : s ∈ σ.lost F ↔ σ.aggsOf s ⊆ F := by
  simp [lost]

theorem lost_mono {F G : Finset Agg} (h : F ⊆ G) : σ.lost F ⊆ σ.lost G := by
  intro s hs
  exact (σ.mem_lost).2 (((σ.mem_lost).1 hs).trans h)

/-- **Complete in good conditions.** With no failure, a subnet is lost only if no aggregator
covers it. -/
theorem lost_empty {s : Sub} : s ∈ σ.lost ∅ ↔ σ.aggsOf s = ∅ := by
  rw [mem_lost, subset_empty]

/-- The aggregators that a lost set needs are exactly those meeting it. -/
theorem nbhd_lost_subset (F : Finset Agg) : σ.nbhd (σ.lost F) ⊆ F := by
  intro a ha
  simp only [nbhd, mem_filter, mem_univ, true_and] at ha
  obtain ⟨s, hs⟩ := ha
  rw [mem_inter] at hs
  exact (σ.mem_lost).1 hs.2 ((σ.mem_aggsOf).2 hs.1)

theorem subset_lost_nbhd (L : Finset Sub) : L ⊆ σ.lost (σ.nbhd L) := by
  intro s hs
  exact (σ.mem_lost).2 (σ.aggsOf_subset_nbhd hs)

/-! ## Tolerance of a loss criterion -/

/-- A loss criterion is monotone when losing more never repairs it. -/
def LossMonotone (Bad : Finset Sub → Prop) : Prop := ∀ L M, L ⊆ M → Bad L → Bad M

/-- The fewest aggregator failures whose lost set satisfies `Bad`; `⊤` if none does. -/
def tolerance (Bad : Finset Sub → Prop) [DecidablePred Bad] : WithTop ℕ :=
  ((univ : Finset (Finset Agg)).filter (fun F => Bad (σ.lost F))).image Finset.card |>.min

variable {σ}

theorem tolerance_le {Bad : Finset Sub → Prop} [DecidablePred Bad] {F : Finset Agg}
    (h : Bad (σ.lost F)) : σ.tolerance Bad ≤ F.card :=
  Finset.min_le (mem_image.2 ⟨F, mem_filter.2 ⟨mem_univ _, h⟩, rfl⟩)

theorem le_tolerance {Bad : Finset Sub → Prop} [DecidablePred Bad] {t : ℕ}
    (h : ∀ F : Finset Agg, Bad (σ.lost F) → t ≤ F.card) : (t : WithTop ℕ) ≤ σ.tolerance Bad := by
  apply Finset.le_min
  intro m hm
  obtain ⟨F, hF, rfl⟩ := mem_image.1 hm
  exact WithTop.coe_le_coe.2 (h F (mem_filter.1 hF).2)

/-- The tolerance is at most `f` exactly when some `f` or fewer failures satisfy `Bad`. -/
theorem tolerance_le_iff {Bad : Finset Sub → Prop} [DecidablePred Bad] {f : ℕ} :
    σ.tolerance Bad ≤ f ↔ ∃ F : Finset Agg, Bad (σ.lost F) ∧ F.card ≤ f := by
  constructor
  · intro h
    by_contra hne
    simp only [not_exists, not_and, not_le] at hne
    have : ((f + 1 : ℕ) : WithTop ℕ) ≤ σ.tolerance Bad :=
      le_tolerance (fun F hF => hne F hF)
    have h' : f + 1 ≤ f := WithTop.coe_le_coe.1 (this.trans h)
    omega
  · rintro ⟨F, hF, hc⟩
    exact (tolerance_le hF).trans (WithTop.coe_le_coe.2 hc)

/-- **Per-vote tolerance.** The fewest failures that lose subnet `s` is the number of aggregators
covering it, under any assignment. -/
theorem tolerance_mem (s : Sub) :
    σ.tolerance (fun L => s ∈ L) = (σ.aggsOf s).card := by
  apply le_antisymm
  · exact tolerance_le ((σ.mem_lost).2 subset_rfl)
  · exact le_tolerance (fun F hF => card_le_card ((σ.mem_lost).1 hF))

/-- **Duality.** For a monotone criterion the tolerance is the smallest number of aggregators
meeting a set of subnets that satisfies it. So `t(q)` is a property of the hypergraph of
coverage sets alone: the least neighbourhood of a set of more than a share `q` of the votes. -/
theorem tolerance_eq_min_nbhd {Bad : Finset Sub → Prop} [DecidablePred Bad]
    (hmono : LossMonotone Bad) :
    σ.tolerance Bad =
      (((univ : Finset (Finset Sub)).filter Bad).image (fun L => (σ.nbhd L).card)).min := by
  apply le_antisymm
  · apply Finset.le_min
    intro m hm
    obtain ⟨L, hL, rfl⟩ := mem_image.1 hm
    exact tolerance_le (hmono _ _ (σ.subset_lost_nbhd L) (mem_filter.1 hL).2)
  · apply Finset.le_min
    intro m hm
    obtain ⟨F, hF, rfl⟩ := mem_image.1 hm
    have hb := (mem_filter.1 hF).2
    calc _ ≤ (((σ.nbhd (σ.lost F)).card : ℕ) : WithTop ℕ) :=
          Finset.min_le (mem_image.2 ⟨σ.lost F, mem_filter.2 ⟨mem_univ _, hb⟩, rfl⟩)
      _ ≤ F.card := WithTop.coe_le_coe.2 (card_le_card (σ.nbhd_lost_subset F))

/-! ## Thresholds -/

/-- The count criterion: at least `ℓ` subnets lost. -/
def AtLeast (ℓ : ℕ) (L : Finset Sub) : Prop := ℓ ≤ L.card

instance (ℓ : ℕ) : DecidablePred (AtLeast (Sub := Sub) ℓ) := fun L =>
  inferInstanceAs (Decidable (ℓ ≤ L.card))

theorem atLeast_mono (ℓ : ℕ) : LossMonotone (AtLeast (Sub := Sub) ℓ) :=
  fun _ _ h hL => le_trans hL (card_le_card h)

/-- The weighted criterion of `t(q)`: the lost subnets hold more than a share `q` of the
scope's votes. `w s` is the number of votes (or the stake) of subnet `s`. -/
def MoreThan (w : Sub → ℕ) (q : ℚ) (L : Finset Sub) : Prop :=
  q * (∑ s, w s : ℕ) < ((∑ s ∈ L, w s : ℕ) : ℚ)

instance (w : Sub → ℕ) (q : ℚ) : DecidablePred (MoreThan w q) := fun _ =>
  inferInstanceAs (Decidable (_ < _))

theorem moreThan_mono (w : Sub → ℕ) (q : ℚ) : LossMonotone (MoreThan w q) := by
  intro L M h hL
  unfold MoreThan at *
  exact lt_of_lt_of_le hL (by exact_mod_cast sum_le_sum_of_subset h)

/-- With `n > 0` votes in every subnet and `q ≥ 0`, losing more than a share `q` of the votes is
losing at least `⌊q·S⌋ + 1` subnets. -/
theorem moreThan_const_iff {n : ℕ} (hn : 0 < n) {q : ℚ} (hq : 0 ≤ q) (L : Finset Sub) :
    MoreThan (fun _ => n) q L ↔ AtLeast (⌊q * Fintype.card Sub⌋₊ + 1) L := by
  unfold MoreThan AtLeast
  simp only [sum_const, card_univ, smul_eq_mul, Nat.cast_mul]
  have hn' : (0 : ℚ) < n := by exact_mod_cast hn
  rw [← mul_assoc, mul_lt_mul_iff_left₀ hn', Nat.add_one_le_iff,
    Nat.floor_lt (mul_nonneg hq (Nat.cast_nonneg _))]

/-- Threshold tolerance `t(q)` for votes `w`. -/
def thresholdTolerance (w : Sub → ℕ) (q : ℚ) : WithTop ℕ := σ.tolerance (MoreThan w q)

/-- The most votes `f` failures can leave without a proof. The coverage profile of the prose is
`C(f) = 1 − maxLoss f / ∑ w`. -/
def maxLoss (w : Sub → ℕ) (f : ℕ) : ℕ :=
  ((univ : Finset (Finset Agg)).filter (fun F => F.card ≤ f)).sup (fun F => ∑ s ∈ σ.lost F, w s)

/-- `t(q)` and the coverage profile carry the same information: `t(q) ≤ f` exactly when `f`
failures can push the loss above a share `q`. -/
theorem thresholdTolerance_le_iff (w : Sub → ℕ) (q : ℚ) (f : ℕ) :
    σ.thresholdTolerance w q ≤ f ↔ q * (∑ s, w s : ℕ) < (σ.maxLoss w f : ℚ) := by
  unfold thresholdTolerance
  rw [tolerance_le_iff]
  have hne : ((univ : Finset (Finset Agg)).filter (fun F => F.card ≤ f)).Nonempty :=
    ⟨∅, by simp⟩
  obtain ⟨G, hG, hGmax⟩ := exists_mem_eq_sup _ hne (fun F => ∑ s ∈ σ.lost F, w s)
  unfold maxLoss
  rw [hGmax]
  constructor
  · rintro ⟨F, hF, hc⟩
    refine lt_of_lt_of_le hF ?_
    have : ∑ s ∈ σ.lost F, w s ≤ ∑ s ∈ σ.lost G, w s := by
      rw [← hGmax]
      exact le_sup (f := fun F => ∑ s ∈ σ.lost F, w s) (mem_filter.2 ⟨mem_univ _, hc⟩)
    exact_mod_cast this
  · intro h
    exact ⟨G, h, (mem_filter.1 hG).2⟩

/-- The coverage profile only falls: more failures never lose fewer votes. -/
theorem maxLoss_mono (w : Sub → ℕ) {f g : ℕ} (h : f ≤ g) : σ.maxLoss w f ≤ σ.maxLoss w g := by
  apply sup_mono
  intro F hF
  simp only [mem_filter, mem_univ, true_and] at hF ⊢
  omega

/-! ## Bounds -/

/-- **The floor, under any assignment.** If every subnet has `k` aggregators and every aggregator
covers at most `d` subnets, losing `ℓ` subnets takes at least `k·ℓ/d` failures. -/
theorem floor_bound {d k ℓ : ℕ} (hd : ∀ a, (σ.cover a).card ≤ d) (hk : σ.HasReplication k)
    {F : Finset Agg} (hF : AtLeast ℓ (σ.lost F)) : k * ℓ ≤ d * F.card := by
  set L := σ.lost F
  have h1 : k * L.card = ∑ a ∈ σ.nbhd L, (σ.cover a ∩ L).card := by
    rw [← σ.sum_aggsOf_eq L, Finset.sum_congr rfl (fun s _ => hk s), sum_const, smul_eq_mul,
      mul_comm]
  have h2 : ∑ a ∈ σ.nbhd L, (σ.cover a ∩ L).card ≤ d * (σ.nbhd L).card := by
    rw [mul_comm]
    exact sum_le_card_nsmul _ _ _ (fun a _ => (card_le_card inter_subset_left).trans (hd a))
  have h3 := card_le_card (σ.nbhd_lost_subset F)
  calc k * ℓ ≤ k * L.card := Nat.mul_le_mul_left _ hF
    _ ≤ d * (σ.nbhd L).card := h1 ▸ h2
    _ ≤ d * F.card := Nat.mul_le_mul_left _ h3

/-- **Redundant assignment.** Lost subnets come in whole groups, and each group costs `k`
failures: losing `ℓ` subnets takes `k·g` failures for some `g` groups with `ℓ ≤ d·g`. -/
theorem redundant_bound {d k ℓ : ℕ} (hk1 : 1 ≤ k) (hd : ∀ a, (σ.cover a).card ≤ d)
    (hk : σ.HasReplication k) (hr : σ.Redundant)
    {F : Finset Agg} (hF : AtLeast ℓ (σ.lost F)) :
    ∃ g, ℓ ≤ d * g ∧ k * g ≤ F.card := by
  set L := σ.lost F
  set N := σ.nbhd L
  refine ⟨(N.image σ.cover).card, ?_, ?_⟩
  · -- every lost subnet lies in a coverage set of an aggregator meeting `L`
    have hsub : L ⊆ (N.image σ.cover).biUnion id := by
      intro s hs
      obtain ⟨a, ha⟩ := card_pos.1 (by rw [hk s]; omega : 0 < (σ.aggsOf s).card)
      exact mem_biUnion.2 ⟨σ.cover a, mem_image.2 ⟨a, σ.aggsOf_subset_nbhd hs ha, rfl⟩,
        (σ.mem_aggsOf).1 ha⟩
    calc ℓ ≤ L.card := hF
      _ ≤ ((N.image σ.cover).biUnion id).card := card_le_card hsub
      _ ≤ ∑ c ∈ N.image σ.cover, (id c).card := card_biUnion_le
      _ ≤ (N.image σ.cover).card * d := by
          apply sum_le_card_nsmul
          intro c hc
          obtain ⟨a, _, rfl⟩ := mem_image.1 hc
          exact hd a
      _ = d * (N.image σ.cover).card := mul_comm _ _
  · -- the aggregators meeting `L` fall into classes of `k` with the same coverage set
    have hfib : ∀ c ∈ N.image σ.cover, (N.filter (fun a => σ.cover a = c)).card = k := by
      intro c hc
      obtain ⟨a, ha, rfl⟩ := mem_image.1 hc
      have ha' := ha
      simp only [N, nbhd, mem_filter, mem_univ, true_and] at ha'
      obtain ⟨s, hs⟩ := ha'
      rw [mem_inter] at hs
      rw [← hk s]
      congr 1
      ext b
      simp only [mem_filter]
      constructor
      · rintro ⟨_, hb⟩
        exact (σ.mem_aggsOf).2 (hb ▸ hs.1)
      · intro hb
        have hb' := (σ.mem_aggsOf).1 hb
        exact ⟨σ.aggsOf_subset_nbhd hs.2 hb,
          (hr b a ⟨s, mem_inter.2 ⟨hb', hs.1⟩⟩)⟩
    have hN : N.card = k * (N.image σ.cover).card := by
      rw [card_eq_sum_card_image σ.cover N, sum_congr rfl hfib, sum_const, smul_eq_mul,
        mul_comm]
    rw [← hN]
    exact card_le_card (σ.nbhd_lost_subset F)

/-- **Bonferroni, subnet side.** The incidences of `L` are at most the aggregators meeting `L` plus,
for each pair of subnets of `L`, the aggregators that cover both. -/
theorem sum_aggsOf_le_nbhd_add_pairs (L : Finset Sub) :
    ∑ s ∈ L, (σ.aggsOf s).card ≤
      (σ.nbhd L).card + ∑ P ∈ L.powersetCard 2, (univ.filter (fun a => P ⊆ σ.cover a)).card := by
  have hc : ∀ c : ℕ, c ≤ 1 + c.choose 2 := by
    intro c
    induction c with
    | zero => simp
    | succ c _ => rw [Nat.choose_succ_succ, Nat.choose_one_right]; omega
  -- pairs of `L` inside a coverage set, counted per aggregator and per pair
  have hpairs : ∑ a : Agg, ((σ.cover a ∩ L).powersetCard 2).card
      = ∑ P ∈ L.powersetCard 2, (univ.filter (fun a => P ⊆ σ.cover a)).card := by
    have := Finset.sum_card_bipartiteAbove_eq_sum_card_bipartiteBelow
      (s := (univ : Finset Agg)) (t := L.powersetCard 2) (r := fun a P => P ⊆ σ.cover a)
    convert this using 2 with a
    · congr 1
      ext P
      simp only [Finset.bipartiteAbove, mem_filter, mem_powersetCard, subset_inter_iff]
      tauto
    · rfl
  calc ∑ s ∈ L, (σ.aggsOf s).card = ∑ a ∈ σ.nbhd L, (σ.cover a ∩ L).card := σ.sum_aggsOf_eq L
    _ ≤ ∑ a ∈ σ.nbhd L, (1 + ((σ.cover a ∩ L).powersetCard 2).card) := by
        apply sum_le_sum
        intro a _
        rw [card_powersetCard]
        exact hc _
    _ = (σ.nbhd L).card + ∑ a ∈ σ.nbhd L, ((σ.cover a ∩ L).powersetCard 2).card := by
        rw [sum_add_distrib, sum_const, smul_eq_mul, mul_one]
    _ ≤ (σ.nbhd L).card + ∑ a : Agg, ((σ.cover a ∩ L).powersetCard 2).card := by
        gcongr
        exact subset_univ _
    _ = _ := by rw [hpairs]

/-- The aggregators meeting `L` number at least `k·|L| − λ·C(|L|, 2)` when two subnets share at
most `λ` aggregators. -/
theorem nbhd_card_pairwise {k lam : ℕ} (hk : σ.HasReplication k) (hp : σ.PairwiseShare lam)
    (L : Finset Sub) : k * L.card ≤ (σ.nbhd L).card + lam * L.card.choose 2 := by
  have hpair_le : ∀ P ∈ L.powersetCard 2, (univ.filter (fun a => P ⊆ σ.cover a)).card ≤ lam := by
    intro P hP
    obtain ⟨s, t, hst, rfl⟩ := card_eq_two.1 (mem_powersetCard.1 hP).2
    refine le_trans (le_of_eq ?_) (hp s t hst)
    congr 1
    ext a
    simp [aggsOf, insert_subset_iff]
  have h := σ.sum_aggsOf_le_nbhd_add_pairs L
  rw [Finset.sum_congr rfl (fun s _ => hk s), sum_const, smul_eq_mul, mul_comm] at h
  have h2 : ∑ P ∈ L.powersetCard 2, (univ.filter (fun a => P ⊆ σ.cover a)).card
      ≤ lam * L.card.choose 2 := by
    calc _ ≤ (L.powersetCard 2).card * lam := sum_le_card_nsmul _ _ _ hpair_le
      _ = lam * L.card.choose 2 := by rw [card_powersetCard, mul_comm]
  omega

/-- **Bonferroni, aggregator side: survivors bound the loss.** If the aggregators of `G` do not
fail, the subnets lost under `F` plus the coverage incidences of `G` are at most `S` plus, for
each pair of aggregators of `G`, the subnets that both cover. -/
theorem lost_card_add_le_of_survivors {F G : Finset Agg} (hG : Disjoint G F) :
    (σ.lost F).card + ∑ a ∈ G, (σ.cover a).card ≤
      Fintype.card Sub + ∑ P ∈ G.powersetCard 2, (univ.filter (fun s => P ⊆ σ.aggsOf s)).card := by
  have h := σ.dual.sum_aggsOf_le_nbhd_add_pairs G
  simp only [dual_aggsOf] at h
  -- what the survivors cover is not lost
  have hdisj : Disjoint (σ.lost F) (σ.dual.nbhd G) := by
    rw [disjoint_left]
    intro s hs hn
    simp only [nbhd, mem_filter, mem_univ, true_and] at hn
    obtain ⟨a, ha⟩ := hn
    rw [mem_inter] at ha
    have haF := (σ.mem_lost).1 hs ha.1
    exact disjoint_left.1 hG ha.2 haF
  have hu := card_le_univ (σ.lost F ∪ σ.dual.nbhd G)
  rw [card_union_of_disjoint hdisj] at hu
  change _ ≤ _ + ∑ P ∈ G.powersetCard 2, (univ.filter (fun s => P ⊆ σ.dual.cover s)).card
  omega

/-- **Dispersion bound.** If two subnets share at most `λ` aggregators, losing `ℓ` subnets takes
at least `k·ℓ − λ·C(ℓ, 2)` failures. For `λ = 0`, that is no shared aggregator at all, it is
`k·ℓ`, as if each lost subnet had its own aggregators. -/
theorem pairwise_bound {k lam ℓ : ℕ} (hk : σ.HasReplication k) (hp : σ.PairwiseShare lam)
    {F : Finset Agg} (hF : AtLeast ℓ (σ.lost F)) : k * ℓ ≤ F.card + lam * ℓ.choose 2 := by
  obtain ⟨L, hL, hcard⟩ := exists_subset_card_eq hF
  have h := σ.nbhd_card_pairwise hk hp L
  have hN : (σ.nbhd L).card ≤ F.card := by
    refine card_le_card (subset_trans ?_ (σ.nbhd_lost_subset F))
    intro a ha
    simp only [nbhd, mem_filter, mem_univ, true_and] at ha ⊢
    obtain ⟨s, hs⟩ := ha
    exact ⟨s, inter_subset_inter_left hL hs⟩
  rw [hcard] at h
  omega

/-! ## Loss unit -/

/-- The loss closure of a subnet: what is lost together with it when exactly its aggregators fail. -/
def closure (s : Sub) : Finset Sub := σ.lost (σ.aggsOf s)

/-- Every loss is a union of closures: a failure that loses `s` loses all of `closure s`. -/
theorem closure_subset_lost {F : Finset Agg} {s : Sub} (hs : s ∈ σ.lost F) :
    σ.closure s ⊆ σ.lost F :=
  σ.lost_mono ((σ.mem_lost).1 hs)

theorem mem_closure_self (s : Sub) : s ∈ σ.closure s := (σ.mem_lost).2 subset_rfl

/-- The loss unit: the fewest votes that can go missing together, the least weight of a
closure. With positive weights, every nonempty loss weighs at least the loss unit. -/
def lossUnit (w : Sub → ℕ) : WithTop ℕ := (univ.image (fun s => ∑ t ∈ σ.closure s, w t)).min

theorem lossUnit_le (w : Sub → ℕ) {F : Finset Agg} (h : (σ.lost F).Nonempty) :
    σ.lossUnit w ≤ ((∑ t ∈ σ.lost F, w t : ℕ) : WithTop ℕ) := by
  obtain ⟨s, hs⟩ := h
  calc σ.lossUnit w ≤ ((∑ t ∈ σ.closure s, w t : ℕ) : WithTop ℕ) :=
        Finset.min_le (mem_image.2 ⟨s, mem_univ _, rfl⟩)
    _ ≤ _ := WithTop.coe_le_coe.2 (sum_le_sum_of_subset (σ.closure_subset_lost hs))

/-- The loss unit is attained by an actual failure set. -/
theorem lossUnit_attained (w : Sub → ℕ) (s : Sub) :
    σ.lossUnit w ≤ ((∑ t ∈ σ.lost (σ.aggsOf s), w t : ℕ) : WithTop ℕ) :=
  Finset.min_le (mem_image.2 ⟨s, mem_univ _, rfl⟩)

end Assignment

end PQAggregation
