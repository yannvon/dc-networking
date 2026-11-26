module

public import PQAggregation.FaultTolerance
public import Mathlib.Data.Fin.VecNotation

/-!
# Yann's example

Sixteen subnets and sixteen aggregators, each aggregator covering `d = 4` subnets and each subnet
covered `k = 4` times. Finality breaks once more than a third of the votes have no proof, which
with equal subnets is `⌊16/3⌋ + 1 = 6` subnets (`moreThan_const_iff`).

* `redundant`: the subnets fall into four groups of four, and four aggregators prove each group.
  This is the baseline of four subnets with four aggregators each, cut into quarters.
* `affine`: the subnets are the points of the affine plane over GF(4), and the aggregators are
  the lines of four of its five parallel classes.
-/

set_option linter.unusedSectionVars false

@[expose] public section

namespace PQAggregation.Examples

open Finset Assignment

/-- Four groups of four subnets; aggregator `a` proves group `a / 4`. -/
def redundant : Assignment (Fin 16) (Fin 16) :=
  ⟨fun a => univ.filter (fun s : Fin 16 => s.val / 4 = a.val / 4)⟩

/-- Multiplication in GF(4) = {0, 1, ω, ω²}, encoded as 0, 1, 2, 3; addition is xor. -/
def gf4Mul : Fin 4 → Fin 4 → Fin 4 :=
  ![![0, 0, 0, 0], ![0, 1, 2, 3], ![0, 2, 3, 1], ![0, 3, 1, 2]]

def gf4Add (x y : Fin 4) : Fin 4 := ⟨x.val ^^^ y.val, by
  have := Nat.xor_lt_two_pow (n := 2) x.isLt y.isLt; simpa using this⟩

/-- Point `4x + y` is `(x, y)`. Aggregator `4c + b` is the line `y = c·x + b` for slopes
`c ∈ {0, 1, ω}`, and the line `x = b` for `c = 3`. The class of slope `ω²` is left out. -/
def affine : Assignment (Fin 16) (Fin 16) :=
  ⟨fun a => univ.filter (fun s : Fin 16 =>
    let x : Fin 4 := ⟨s.val / 4, by omega⟩
    let y : Fin 4 := ⟨s.val % 4, by omega⟩
    let c : Fin 4 := ⟨a.val / 4, by omega⟩
    let b : Fin 4 := ⟨a.val % 4, by omega⟩
    if c.val = 3 then x = b else y = gf4Add (gf4Mul c x) b)⟩

/-! ## The shape of both assignments, checked by evaluation in the kernel -/

theorem redundant_degree : redundant.HasDegree 4 := by decide
theorem redundant_replication : redundant.HasReplication 4 := by decide
theorem redundant_redundant : redundant.Redundant := by decide

theorem affine_degree : affine.HasDegree 4 := by decide
theorem affine_replication : affine.HasReplication 4 := by decide
/-- Two points lie on at most one line. -/
theorem affine_pairwise : affine.PairwiseShare 1 := by decide
theorem affine_not_redundant : ¬ affine.Redundant := by decide
theorem affine_dispersed : affine.Dispersed := by decide

/-! ## Finality threshold: more than a third of the votes -/

/-- One vote per subnet; any equal number gives the same thresholds (`moreThan_const_iff`). -/
def w1 : Fin 16 → ℕ := fun _ => 1

theorem floor_third : ⌊(1 / 3 : ℚ) * Fintype.card (Fin 16)⌋₊ + 1 = 6 := by
  rw [Fintype.card_fin, Nat.add_left_inj, Nat.floor_eq_iff (by norm_num)]
  norm_num

theorem moreThan_third_iff (L : Finset (Fin 16)) : MoreThan w1 (1 / 3) L ↔ AtLeast 6 L := by
  rw [show w1 = fun _ => 1 from rfl, moreThan_const_iff one_pos (by norm_num), floor_third]

/-- **Redundant: `t(1/3) = 8`.** The lower bound is `redundant_bound`, the upper bound fails the
eight aggregators of two groups. -/
theorem redundant_threshold : redundant.thresholdTolerance w1 (1 / 3) = 8 := by
  apply le_antisymm
  · have : MoreThan w1 (1 / 3) (redundant.lost (univ.filter (fun a : Fin 16 => a.val < 8))) := by
      rw [moreThan_third_iff]; decide
    exact tolerance_le this
  · show ((8 : ℕ) : WithTop ℕ) ≤ _
    apply le_tolerance
    intro F hF
    rw [moreThan_third_iff] at hF
    obtain ⟨g, hg, hF⟩ := redundant_bound (by norm_num) (fun a => (redundant_degree a).le)
      redundant_replication redundant_redundant hF
    omega

/-- The twelve lines that meet the points `{0, 1, 4, 6, 9, 10}`; failing them loses those six. -/
def affineWitness : Finset (Fin 16) := {0, 1, 2, 4, 5, 7, 8, 9, 10, 12, 13, 14}

/-- Two lines share at most one point. -/
theorem affine_lines_meet : ∀ a b : Fin 16, a ≠ b → (affine.cover a ∩ affine.cover b).card ≤ 1 := by
  decide

/-- Two lines of the same parallel class share no point. -/
theorem affine_parallel :
    ∀ a b : Fin 16, a ≠ b → a.val / 4 = b.val / 4 → affine.cover a ∩ affine.cover b = ∅ := by
  decide

theorem affine_pair_eq (a b : Fin 16) :
    univ.filter (fun s => ({a, b} : Finset (Fin 16)) ⊆ affine.aggsOf s)
      = affine.cover a ∩ affine.cover b := by
  ext s; simp [insert_subset_iff, mem_aggsOf]

/-- Any five lines cover at least 11 points, so failing at most 11 lines loses at most 5 points:
among five lines two are parallel, so at most 9 of the 10 pairs meet, each in one point. -/
theorem affine_lost_le_five {F : Finset (Fin 16)} (hF : F.card ≤ 11) : (affine.lost F).card ≤ 5 := by
  -- five surviving lines
  have hc : 5 ≤ Fᶜ.card := by rw [card_compl, Fintype.card_fin]; omega
  obtain ⟨G, hGF, hG⟩ := exists_subset_card_eq hc
  have hdisj : Disjoint G F := subset_compl_iff_disjoint_right.1 hGF
  -- two of them are parallel
  obtain ⟨x, hx, y, hy, hxy, hcls⟩ := exists_ne_map_eq_of_card_lt_of_maps_to
    (t := range 4) (f := fun a : Fin 16 => a.val / 4) (by rw [hG]; simp)
    (fun a _ => by simp only [coe_range, Set.mem_Iio]; omega)
  set g := fun P : Finset (Fin 16) => (univ.filter (fun s => P ⊆ affine.aggsOf s)).card
  have hg1 : ∀ P ∈ G.powersetCard 2, g P ≤ 1 := by
    intro P hP
    obtain ⟨a, b, hab, rfl⟩ := card_eq_two.1 (mem_powersetCard.1 hP).2
    simp only [g, affine_pair_eq]
    exact affine_lines_meet a b hab
  have hP0 : ({x, y} : Finset (Fin 16)) ∈ G.powersetCard 2 :=
    mem_powersetCard.2 ⟨insert_subset_iff.2 ⟨hx, singleton_subset_iff.2 hy⟩, card_pair hxy⟩
  have hg0 : g {x, y} = 0 := by
    simp only [g, affine_pair_eq, affine_parallel x y hxy hcls, card_empty]
  have hsum : ∑ P ∈ G.powersetCard 2, g P ≤ 9 := by
    rw [← add_sum_erase _ _ hP0, hg0, zero_add]
    calc _ ≤ ((G.powersetCard 2).erase {x, y}).card * 1 :=
          sum_le_card_nsmul _ _ _ (fun P hP => hg1 P (mem_of_mem_erase hP))
      _ = 9 := by rw [card_erase_of_mem hP0, card_powersetCard, hG]; rfl
  have hdeg : ∑ a ∈ G, (affine.cover a).card = 20 := by
    rw [sum_congr rfl (fun a _ => affine_degree a), sum_const, hG]; rfl
  have := affine.lost_card_add_le_of_survivors hdisj
  rw [hdeg, Fintype.card_fin] at this
  have hsum' : ∑ P ∈ G.powersetCard 2,
      (univ.filter (fun s => P ⊆ affine.aggsOf s)).card ≤ 9 := hsum
  omega

/-- **Affine plane: `t(1/3) = 12`.** The lower bound is `affine_lost_le_five`, the upper bound
fails the twelve lines of `affineWitness`. -/
theorem affine_threshold : affine.thresholdTolerance w1 (1 / 3) = 12 := by
  apply le_antisymm
  · have : MoreThan w1 (1 / 3) (affine.lost affineWitness) := by
      rw [moreThan_third_iff]; decide
    exact tolerance_le this
  · show ((12 : ℕ) : WithTop ℕ) ≤ _
    apply le_tolerance
    intro F hF
    rw [moreThan_third_iff] at hF
    by_contra h
    have := affine_lost_le_five (F := F) (by omega)
    unfold AtLeast at hF
    omega

theorem redundant_lt_affine :
    redundant.thresholdTolerance w1 (1 / 3) < affine.thresholdTolerance w1 (1 / 3) := by
  rw [redundant_threshold, affine_threshold]
  decide

/-! ## Loss unit and per-vote tolerance -/

theorem redundant_closure (s : Fin 16) : (redundant.closure s).card = 4 := by
  revert s; decide

theorem affine_closure (s : Fin 16) : affine.closure s = {s} := by
  revert s; decide

/-- Per-vote tolerance is `k = 4` in both: an attacker who targets one vote pays the same. -/
theorem per_vote (s : Fin 16) :
    redundant.tolerance (fun L => s ∈ L) = 4 ∧ affine.tolerance (fun L => s ∈ L) = 4 := by
  rw [tolerance_mem, tolerance_mem, redundant_replication s, affine_replication s]
  exact ⟨rfl, rfl⟩

end PQAggregation.Examples
