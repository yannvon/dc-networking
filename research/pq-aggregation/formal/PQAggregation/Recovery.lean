module

public import PQAggregation.FaultTolerance
public import Mathlib.Data.Fintype.Sum

/-!
# Recovery, and failures in time

A vote that its aggregators missed is recoverable when someone else can still prove it: a fallback
prover, a builder, or an aggregator of a later window under late inclusion.
In the model all of these are more coverage. They form a second assignment `τ`, from fallback
roles to the subnets whose votes each role receives in time to prove them, and the system with
recovery is the sum `σ ⊕ τ`. A subnet is then lost only when it is lost in both.

This needs the acceptance rule to be open: if a proof is accepted only from the aggregators
assigned to its subnets, a fallback role has no coverage set at all (`τ` is empty), and nothing is
recoverable whatever the network does.

Roles also express failures in time. An aggregator that serves several windows, or several
instances of a scope, is several roles with one owner. A node flooded for a few seconds fails the
roles of that window; a node that is gone fails all of its roles (`failMachines`).
-/

set_option linter.unusedSectionVars false

@[expose] public section

namespace PQAggregation

open Finset

variable {Sub Agg Fb : Type} [Fintype Sub] [Fintype Agg] [Fintype Fb]
  [DecidableEq Sub] [DecidableEq Agg] [DecidableEq Fb]

namespace Assignment

/-- The assignment together with fallback roles `τ`. -/
def withFallback (σ : Assignment Sub Agg) (τ : Assignment Sub Fb) : Assignment Sub (Agg ⊕ Fb) :=
  ⟨Sum.elim σ.cover τ.cover⟩

/-- Under acceptance from assigned aggregators only, a fallback role covers nothing. -/
def gated : Assignment Sub Fb := ⟨fun _ => ∅⟩

variable (σ : Assignment Sub Agg) (τ : Assignment Sub Fb)

/-- Failures of aggregators `F` and of fallback roles `G`. -/
def failSum (F : Finset Agg) (G : Finset Fb) : Finset (Agg ⊕ Fb) := F.disjSum G

/-- **With a fallback, a subnet is lost only when it is lost to both.** -/
theorem lost_withFallback (F : Finset Agg) (G : Finset Fb) :
    (σ.withFallback τ).lost (failSum F G) = σ.lost F ∩ τ.lost G := by
  ext s
  simp [mem_lost, subset_iff, aggsOf, withFallback, failSum]

/-- Gated acceptance recovers nothing: the fallback roles change no loss. -/
theorem lost_gated (F : Finset Agg) (G : Finset Fb) :
    (σ.withFallback (gated (Fb := Fb))).lost (failSum F G) = σ.lost F := by
  rw [lost_withFallback]
  have : (gated (Sub := Sub) (Fb := Fb)).lost G = univ := by
    ext s; simp [mem_lost, aggsOf, gated]
  rw [this, inter_univ]

/-- **Recovery only helps.** For a monotone criterion, adding fallback roles never lowers the
tolerance, even when the attacker may also fail fallback roles. -/
theorem tolerance_le_withFallback {Bad : Finset Sub → Prop} [DecidablePred Bad]
    (hmono : LossMonotone Bad) :
    σ.tolerance Bad ≤ (σ.withFallback τ).tolerance Bad := by
  apply Finset.le_min
  intro m hm
  obtain ⟨H, hH, rfl⟩ := mem_image.1 hm
  have hb := (mem_filter.1 hH).2
  -- the aggregators among `H`
  let F : Finset Agg := univ.filter (fun a => Sum.inl a ∈ H)
  have hsub : (σ.withFallback τ).lost H ⊆ σ.lost F := by
    intro s hs
    rw [mem_lost] at hs ⊢
    intro a ha
    have : Sum.inl a ∈ (σ.withFallback τ).aggsOf s :=
      (mem_aggsOf _).2 ((σ.mem_aggsOf).1 ha)
    simpa [F] using hs this
  have hcard : F.card ≤ H.card := by
    rw [← card_map ⟨Sum.inl, Sum.inl_injective⟩]
    apply card_le_card
    intro x hx
    obtain ⟨a, ha, rfl⟩ := mem_map.1 hx
    simpa [F] using ha
  exact (tolerance_le (hmono _ _ hsub hb)).trans (WithTop.coe_le_coe.2 hcard)

/-- The roles that fail when the machines `M` fail, for an owner map from roles to machines. -/
def failMachines {Mach : Type} [DecidableEq Mach] (owner : Agg → Mach) (M : Finset Mach) :
    Finset Agg :=
  univ.filter (fun a => owner a ∈ M)

/-- Losing `s` costs at least as many machines as own an aggregator of `s`. With one machine per
role this is the per-vote tolerance `k`; when one machine holds several aggregators of the same
subnet, as when it serves the same subnet in several slots of a round, it is fewer. -/
theorem card_owners_le {Mach : Type} [DecidableEq Mach] (owner : Agg → Mach)
    (M : Finset Mach) {s : Sub} (hs : s ∈ σ.lost (failMachines owner M)) :
    ((σ.aggsOf s).image owner).card ≤ M.card := by
  apply card_le_card
  intro x hx
  obtain ⟨a, ha, rfl⟩ := mem_image.1 hx
  have := (σ.mem_lost).1 hs ha
  simpa [failMachines] using this

end Assignment

end PQAggregation
