---
title: Formal framework for PQ aggregation
status: wip
date: 2026-11-25
provenance: agent
---

> **Provenance: agent.** Written 2026-11-25 by an agent, as topic 3 of the [PQ aggregation strategy](../README.md) workstream. It formalizes the draft definitions in `properties/aggregation-broadcast.md`, which are an agent's draft too. Yann has not reviewed either.
> - **Reviewed on integration** by the oversight thread, 2026-11-25. It built both versions from clean sources against the downloaded Mathlib cache (`lake build`: 2,076 jobs, about 20 s) and printed the axioms of 42 theorems: only `propext`, `Classical.choice` and `Quot.sound`.
> - The prose changes of the section "Where the prose definitions had to change" are now applied to [`properties/aggregation-broadcast.md`](../../../properties/aggregation-broadcast.md), with two differences: "redundant" and "dispersed" stay next to λ, and the redundant formula stays an equality with its lower bound marked as the proved part.
> - One sentence is the oversight thread's: the one on `Examples.lean` under "Towards EthLib". So are the heading "Towards verified-consensus" and the line under it, written on 2026-11-26, after that repository was renamed.

# Formal framework for PQ aggregation

**What this is.** A Lean 4 model of aggregation: aggregators, the subnets each one proves, failures, merges and fallbacks. The aggregation properties are stated in it, and enough is proved or evaluated to show that the definitions mean what the prose means. It is meant to make aggregation designs comparable. It does not verify an implementation.

**Kept general.** The numbers of subnets, aggregators and votes are finite types and weight functions, never constants. Only `Examples.lean` fixes numbers.

**Self-contained.** This directory is a Lake project of its own, pinned to the same Lean (v4.36.0) and Mathlib (v4.36.0) as EthLib. It is written in EthLib's module style. It can move to its own repository unchanged.

## Build

```sh
lake exe cache get   # prebuilt Mathlib, about 7 GB
lake build           # about 15 s on 2 cores; peak memory well under 3 GB
python3 scripts/check_example.py   # independent enumeration of the example
```

The build is free of `sorry` and `native_decide`. `#print axioms` on the main theorems shows only `propext`, `Classical.choice` and `Quot.sound`.

## The model

| Prose term | Lean | Notes |
|---|---|---|
| Subnet, aggregator | finite types `Sub`, `Agg` | S and A are their cardinalities |
| Votes of a subnet | `w : Sub → ℕ` | count or stake; equal subnets are `fun _ => n` |
| Coverage set | `Assignment.cover : Agg → Finset Sub` | sizes may differ |
| d, k | `HasDegree d`, `HasReplication k` | `card_mul_degree`: A·d = S·k, **proved** |
| Instance, scope | one `Assignment` over disjoint unions | not a primitive (see below) |
| Failure | `F : Finset Agg`, which publishes nothing | crash, flooding, withholding and capture alike |
| Votes without a proof | `lost F`: subnets whose aggregators are all in `F` | without a fallback |
| Merge | `Provable base m r h X` | fan-in `m`, `r` raw signatures per merge, `h` levels |
| Fallback, late inclusion | `withFallback σ τ`: extra roles `τ` | recovery is more coverage |

## Properties, and what is shown about each

**Proved** means a Lean theorem for all parameters. **Kernel-checked** means a Lean theorem about the concrete example. **Evaluated** means computed by `scripts/check_example.py`, outside Lean. **Stated** means defined with no theorem about it.

| Property | Lean | Status |
|---|---|---|
| Per-vote tolerance = k, under any assignment | `tolerance_mem` | proved |
| Tolerance of any loss criterion | `tolerance Bad` (`⊤` when unreachable) | stated, with `tolerance_le_iff` |
| **Duality**: t is the least number of aggregators meeting a losing set of subnets | `tolerance_eq_min_nbhd` | proved |
| Threshold tolerance t(q) | `thresholdTolerance w q`, from `MoreThan w q` | stated |
| More than a share q of equal subnets ⇔ at least ⌊q·S⌋+1 subnets | `moreThan_const_iff` | proved |
| Coverage profile C(f) = 1 − maxLoss(f)/∑w, and t(q) ≤ f ⇔ q·∑w < maxLoss(f) | `maxLoss`, `thresholdTolerance_le_iff`, `maxLoss_mono` | proved |
| Floor: losing ℓ subnets takes ≥ k·ℓ/d failures, under any assignment | `floor_bound` | proved |
| Redundant: losing ℓ takes k·g failures with ℓ ≤ d·g, so ≥ k·⌈ℓ/d⌉ | `redundant_bound` | proved, lower bound |
| Bonferroni, subnet side: ∑_{s∈L} k_s ≤ \|aggregators meeting L\| + ∑ over pairs of L of the aggregators covering both | `sum_aggsOf_le_nbhd_add_pairs` | proved |
| Dispersed: if two subnets share ≤ λ aggregators, losing ℓ takes ≥ k·ℓ − λ·C(ℓ,2) | `pairwise_bound`, `nbhd_card_pairwise` | proved |
| Bonferroni, aggregator side: if G survives, \|lost F\| + ∑_{a∈G} \|cover a\| ≤ S + ∑ over pairs of G of their shared subnets | `lost_card_add_le_of_survivors` (via the dual assignment `dual`) | proved |
| Random failures: a subnet is lost with probability p^k, under any assignment | `prob_lost`, `prob_superset` | proved |
| Expected loss = ∑w·p^k, the same for every assignment with replication k | `expected_loss_uniform` | proved |
| Loss unit: every loss is a union of closures; the unit is the least closure weight | `closure_subset_lost`, `lossUnit_le` | proved |
| Complete in good conditions | `lost_empty` | proved |
| Recoverable: with a fallback, a subnet is lost only if lost to both | `lost_withFallback` | proved |
| Recovery never lowers any tolerance | `tolerance_le_withFallback` | proved |
| Gated acceptance (only assigned aggregators) recovers nothing | `lost_gated` | proved |
| Failures in time: losing a vote costs as many machines as own its aggregators | `failMachines`, `card_owners_le` | proved |
| Merge levels: h levels of fan-in m over proofs of ≤ c votes cover ≤ m^h·c (more with raw signatures) | `Provable.card_le`, `coverBound_zero_raw` | proved |
| Redundant work: every assignment with replication k proves each vote k times | `sum_cover_weight` | proved |
| Sound | a proof covers only votes in its leaves and raw sets | stated by construction, not a theorem |
| Latency, bytes, verification work, bounded spam, open to builders | | left out (see below) |

## Yann's example

Sixteen subnets and sixteen aggregators, d = k = 4. Finality breaks once more than a third of the votes have no proof, that is 6 of 16 equal subnets.

| | Redundant (4 groups of 4) | Affine plane over GF(4), 4 parallel classes |
|---|---|---|
| t(1/3) | **8**, kernel-checked (`redundant_threshold`) | **12**, kernel-checked (`affine_threshold`) |
| Ordering | | redundant < affine, kernel-checked (`redundant_lt_affine`) |
| Loss unit | 4 subnets (`redundant_closure`) | 1 subnet (`affine_closure`) |
| Per-vote tolerance | 4 | 4 (`per_vote`) |
| Most subnets lost by f = 4, 8, 12, 15 failures (evaluated) | 4, 8, 12, 12 | 1, 2, 6, 12 |

Both threshold values are proved in Lean, and `scripts/check_example.py` confirms them independently. Only the coverage profile row is evaluated, not proved.

- **Upper bound 12.** Failing the 12 lines that meet the points {0, 1, 4, 6, 9, 10} (`affineWitness`) loses those six points.
- **Lower bound 12** (`affine_lost_le_five`) counts survivors, with no enumeration of point sets. If at most 11 lines fail, 5 survive. Two of those 5 are parallel, because there are only 4 classes. Parallel lines share no point and other pairs share one, so at most 9 of the 10 pairs meet. By the aggregator-side Bonferroni lemma the 5 survivors cover at least 20 − 9 = 11 points, so at most 5 are lost. The kernel checks only the 256 pairs of lines.
- **The subnet-side bound is weaker.** `pairwise_bound` gives 9 at ℓ = 6 and 10 at ℓ = 5. It is tight up to four lost subnets (7, 9 and 10 failures for 2, 3 and 4 subnets), and the survivor count is the sharper tool beyond that.
- **Coverage profile (evaluated).** The affine profile is at least as good as the redundant one at every f from 0 to 16. The survivor count also gives the evaluated maxLoss at f = 12 to 15, but that is not formalized.

## Where the prose definitions had to change

1. **Threshold tolerance is one instance of a general notion.** The formal object is the tolerance of a monotone loss criterion: the fewest failures whose lost set satisfies it. Per-vote tolerance, t(q), and the threshold of a scope with several instances differ only in the criterion. The value is `⊤` when no failure set breaks it, for example when q ≥ 1.
2. **t(q) depends only on the coverage hypergraph.** By duality it is the least number of aggregators that meet a set of subnets holding more than a share q of the votes. "An attacker who knows the assignment" is this minimum. Nothing about timing enters.
3. **The ⌊q·S⌋ + 1 formulas hold only for equal subnets.** In general the criterion is on weights: q·∑w < ∑ over lost subnets of w. With stake weighting, or subnets of different sizes, the counting formulas need restating.
4. **The redundant formula is a lower bound.** Under `Redundant`, `HasReplication k ≥ 1` and coverage sets of at most d, t ≥ k·⌈ℓ/d⌉ is proved. Equality also needs enough whole groups to lose, which holds in the example.
5. **"Dispersed" is not the parameter that matters.** "The k aggregators of a subnet have different coverage sets" is binary, and it is ambiguous (pairwise different, or not all equal?). The bound depends on λ, the most aggregators two subnets share. λ = k is redundant, and λ = 1 is the affine plane. I propose replacing the redundant/dispersed pair with λ, or with the closure size behind the loss unit.
6. **Redundant work comes from replication, not from the redundant assignment.** With replication k, every assignment proves each vote k times at the first level (A·d = S·k). So (k − 1)/k of first-level proving is redundant under dispersal too. Dispersal moves the duplicates into different proofs, which merges then take as overlapping children. Only publishing less, as the staggered `pq` spec does, removes them.
7. **An instance is not a primitive.** A scope with one assignment per slot is one assignment over the disjoint union. What the prose's "instance" hides is the difference between roles and machines. A machine that aggregates the same subnet in several slots, or in a late-inclusion window, fails all those roles at once. Losing a vote then costs fewer than k machines (`card_owners_le`). So "a failure in time" is defined by which roles a failure takes out.
8. **Recoverable means "more coverage", and needs open acceptance.** A fallback or a late-inclusion window is a second set of roles, and a subnet is lost only if it is lost to both. If proofs are accepted only from assigned aggregators, as in the `pq` spec at `ee867e9`, the fallback roles cover nothing, and recovery is impossible whatever the network does.
9. **Capture: β^k assumes independent ownership.** It is the random-failure computation with p = β. A draw without replacement from a finite stake distribution is hypergeometric and gives a slightly smaller value. "Leaves out chosen votes" needs no new notion: for coverage it is withholding those votes.
10. **Per-vote tolerance is per subnet.** Without uniform replication it is the replication of that subnet, k_s, not one k.

## What is left out

- **Time.** There is no clock: no vote deadline, no latency, and no aggregation phase of 4 s or 2 s. A failure is a set of roles, and time enters only through which roles exist (windows, slots).
- **Bytes and propagation.** Aggregate sizes, topics, gossip and blobs belong to topic 2. Verification work per node is not modelled.
- **Delivery into subnets.** A subnet is lost all at once. A vote that does not reach its aggregators in time belongs to attestation broadcast, upstream of this model.
- **Bounded spam.** A Byzantine aggregator is modelled only as withholding. Flooding others with valid but useless proofs is not modelled.
- **Soundness of the proof system.** It is assumed: proofs cover only signed votes.
- **Selection.** How the assignment is drawn, public or private, and what grinding the seed gains.
- **Encoding.** That bitlists do not depend on who aggregated is implicit: a proof here is a set of votes, with no prover in it. There is no theorem about an encoding.

## Towards EthLib

- **Kind and place.** In EthLib's terms this is a *model*: abstract objects, with no executable specification under them. Its place would be `EthLib/Consensus/Proofs/Models/Aggregation/`, listed in `coverage/kinds.toml` with the other models.
- **Already aligned.** The project uses the same toolchain and Mathlib pin, and the same `module` / `public import` / `@[expose] public section` style. The weight sums are EthLib's `Models.stake w S` (`EthLib/Consensus/Proofs/Models/Stake.lean`), and switching to it is mechanical.
- **To change on the move.** The namespace would become `EthLib.Consensus.Models.Aggregation`. Doc comments would follow CONTRIBUTING.md and WRITING.md: one sentence per line, module headers of about five lines (several here are longer), and the controlled vocabulary. Thresholds would use natural-number fractions (`den·lost > num·total`) instead of ℚ, as the Casper FFG model does for its 2/3. `Examples.lean` stays outside EthLib. Its CONTRIBUTING.md (section "No examples", at `56d23b9`) keeps no proofs about one particular value that are written to show how a rule works, and says such logic belongs with the project that needs it. The kernel-vector library `KernelVectors`, which no default target imports, is for known answers taken from the specification's own vectors, so it does not fit either. What would move are the general lemmas the example uses, both Bonferroni lemmas among them.
- **What would connect it.** A refinement theorem, once a PQ-DC specification exists in EthLib: the spec's assignment of aggregators to attestation subnets is an `Assignment`, and its acceptance rule decides whether `withFallback` is gated. EthLib has no PQ-DC spec yet, so nothing refines this model today.

## Towards verified-consensus

The repository is [`ethlabs-org/verified-consensus`](https://github.com/ethlabs-org/verified-consensus). It was `eth-consensus-lean` when this note was written, and was renamed by 2026-11-26. Its Lake package is still `consensus-lean` and its modules are still under `ConsensusLean/`, so the path below holds.

- **The interface is ΔFG, but in a weaker form.** The network model (`ConsensusLean/Spec/Problem/Network.lean`, `Delivers.fgAtts`) delivers every finality-gadget attestation sent by an honest validator to every awake honest node within ΔFG. No aggregation design meets that when all k aggregators of a subnet fail: those votes have no proof within ΔFG, unless a fallback covers them.
- **The statement that fits** is a threshold delivery bound. For every failure set F in an admissible family (for example |F| < t(q), or F of independent failures with a stated tail), every honest vote outside `lost F` is held by every awake honest node within ΔFG. The votes in `lost F` hold at most a share q.
- **What it would cost there.** The finality gadget's liveness (the healthy regime) would have to be re-proved from that weaker assumption. Accountable safety does not depend on delivery, so it is unaffected. The gadget still finalizes if the honest votes that arrive reach two thirds of the stake. That is the prose's q = 1 − 2/(3(1 − β)), with β the share of stake that withholds its votes.
- **One modelling question to settle there.** Aggregator failures are failures of nodes, which need not be validators, so they may need a budget separate from the Byzantine validators.

## Files

- `PQAggregation/Assignment.lean`: assignments, their dual, d, k, redundant, dispersed, λ, A·d = S·k.
- `PQAggregation/FaultTolerance.lean`: lost subnets, tolerance, duality, t(q), coverage profile, floor, redundant and λ bounds, both Bonferroni lemmas, loss unit.
- `PQAggregation/RandomFailures.lean`: independent failures, p^k, expected loss.
- `PQAggregation/Recovery.lean`: fallback roles, gated acceptance, machines and roles.
- `PQAggregation/Performance.lean`: merges, the merge-level bound, first-level work.
- `PQAggregation/Examples.lean`: Yann's example, both assignments.
- `scripts/check_example.py`: the same example, enumerated without Lean.
