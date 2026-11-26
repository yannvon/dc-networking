---
title: PQ aggregation — dispersed aggregator assignment
status: wip
date: 2026-11-25
provenance: agent
---

> **Provenance: agent.** Written 2026-11-25 by an agent for the PQ aggregation strategy workstream, from Yann's idea of giving each aggregator a different set of subnets ("error correction for aggregation"). Yann has not reviewed it. Terms are those of [`properties/aggregation-broadcast.md`](../../../properties/aggregation-broadcast.md) (scope, subnet, aggregator, coverage set of d subnets, replication k, instance, A·d = S·k, t(q)). Every number comes from [`sim/dispersal.py`](sim/dispersal.py) (stdlib, `python3 sim/dispersal.py`, about a minute) or [`sim/exact.py`](sim/exact.py) (CP-SAT and a search in numpy, `uv run --with ortools python3 sim/exact.py`, up to 14 min; 5 min in the oversight thread's orb). Finality uses q = 1/3, i.e. x = ⌊S/3⌋ + 1 subnets without a proof.
> - **Edited on integration** by the oversight thread, 2026-11-25. It reran both scripts, and re-derived the ceiling and the plane bound on its own and checked them against all 65,536 failure sets of the example, with a script of its own that is not in this repo. Four changes:
>   - **"Failures counted at one time" is new**, with section 8 of the script. The first version counted failures only over the whole scope and concluded that dispersal inside a slot buys almost nothing for a round. Counted as aggregators failed at the same moment, it keeps its whole gain. This part is the oversight thread's own and nobody has checked it.
>   - The ceiling uses that a loss is a whole number of subnets, which lowers it from 50 to 49 in the A = 64, k = 4 rows.
>   - "Fewer aggregators, or less replication" is rewritten with the load per aggregator, the number of proofs and the merge size stated. The first version said that halving k at the same 64 aggregators halves the aggregate bytes; the 64 proofs remain. The numbers are section 7 of the script, which the oversight thread added.
>   - A second proof of the example's 12 is noted, and the pointer to the worker's report is replaced by what the report said.
> - **Decided after this note** (Yann, 2026-11-25): the adversary is measured by the machines it attacks at any given time, simplified to per slot. So "Failures counted at one time" is the count that applies, and the property is now called DoS resilience in [`properties/aggregation-broadcast.md`](../../../properties/aggregation-broadcast.md#dos-resilience). The note's text is unchanged and still says "tolerance".
> - **Added after that decision** (oversight thread, 2026-11-25): "Against today's p2p stack", with section 9 of the script. Yann set today's p2p stack as the baseline: 64 subnets and 16 randomly chosen aggregators in a subnet of about 400. The section is the oversight thread's own modelling. It checked the script's figures with a second script, which is not in this repo, and nobody else has read either.
> - **Corrected by Yann the same day.** That section first measured a design in which every committee is cut into slices and an aggregator proves one slice of each. Yann rejected it, because it puts an aggregator in every subnet. He means that an aggregator takes a few whole subnets, for example 4, at random or round robin, and proves no more than an aggregator of the `pq` spec. The slice figures are removed. "Aggregators on a few whole subnets" replaces them, with section 10 of the script and parts 2 and 3 of `exact.py`. It is the oversight thread's own modelling, checked by the same second script, and nobody else has read it.
> - **Corrected by Yann again** (2026-11-25): his "subnet of about 400 nodes" is the nodes on a subnet's topic, not the committee of validators. "Against today's p2p stack" took it for the committee and compared machines with validators. It now keeps aggregators, nodes on a topic and machines apart, and takes machines from the hosting scenarios of aggregator selection's script. Yann also kept several choices open that day; they are marked "kept in the design space".
> - **And a third time** (Yann, 2026-11-25): validators are not spread evenly over machines, "they are spread according to kamil's deanonymization note". The row for 100 validators on each of 8,000 machines is removed. The figures in machines now come from that measured node list and from two kinds of approximation: the shape Heimbach et al. measured, and the shapes this repo's benchmarks run with. Section 10 gained the same count in machines for the 64 aggregators of a slot.
> - **The node list is not in this repo.** It was kept out on purpose, and Yann allowed aggregate figures from it on 2026-11-25. [`sim/measured.py`](sim/measured.py) computes them from the list (`python3 sim/measured.py <node list csv>`, about half a minute) and prints aggregates only. The oversight thread checked them with a second script in its orb, and nobody else has.

# Dispersed aggregator assignment

## Short answer

- **t(q) is a vertex-expansion number.** It is the fewest aggregators that touch some set of x subnets. Redundant assignment is the worst possible graph for it; dispersal is the search for a good expander (disperser) with the same degrees.
- **Bounds that hold for every assignment with replication k**, per instance:
  - floor: t ≥ k·x/d ≈ q·A. Redundant sits on it.
  - ceiling (new): t ≤ the least f with S·C(f, k) > (x − 1)·C(A, k), about **q^(1/k)·A**. A random set of f failures loses each subnet with probability C(f, k)/C(A, k) ≈ (f/A)^k, and some set of that size loses at least the average, in whole subnets. With subnets of unequal weight the same argument gives the least f with C(f, k) > q·C(A, k).
  - So at equal load the most dispersal can buy is a factor q^(1/k−1): **1.73× at k = 2, 2.28× at k = 4, 2.62× at k = 8** (q = 1/3).
- **How close real assignments get:**
  - Affine planes / Reed–Solomon nets (S = w² subnets, k parallel classes of lines, d = w, A = k·w): t ≥ k·q/(1 + (k−1)q)·A by Tanner's spectral bound, **0.667·A at k = 4** against 0.333·A redundant and 0.760·A ceiling.
  - Random balanced assignments approach the ceiling once each aggregator covers many subnets (d ≫ k), and stay well below it at d ≈ k.
- **Yann's example (S = A = 16, d = k = 4):** redundant 8, affine plane 12, ceiling 13. The plane's 12 is proved in Lean (formal topic). Whether 13 is reachable is **open**: annealing never got close and a SAT search (any 4 live aggregators cover ≥ 11 subnets) did not finish in 25 min. With the same 16 aggregators and the same load but 256 finer subnets (d = 64), random assignments reach 13.
- **Fewer aggregators, or less replication.** The baseline is redundant k = 4 with 64 aggregators: t(1/3) = 24, so finality breaks at 24 failures. With V votes, first-level proving is k·V signatures, each aggregator proves k·V/A of them, there are A proofs, and a full merge takes one disjoint cover of A/k of them. Planes, from section 7 of the script:

  | Assignment | t(1/3) | Load per aggregator | First-level proving | Proofs | Children of a full merge |
  |---|---:|---:|---:|---:|---:|
  | redundant, k = 4, A = 64 | 24 | baseline | baseline | baseline | 16 |
  | plane, k = 3, A = 48 | ≥ 29 (ceiling 34) | same | −25 % | −25 % | 16 |
  | plane, k = 2, A = 32 | ≥ 17 (ceiling 19) | same | −50 % | −50 % | 16 |
  | plane, k = 4, A = 32 | ≥ 22 (ceiling 25) | double | same | −50 % | 8 |
  | plane, k = 2, A = 64 | ≥ 33 (ceiling 38); random ≥ 30 | half | −50 % | same | 32 |

  - **At the same load per aggregator, three quarters of the aggregators are enough** (k = 3): t ≥ 29 against 24. Half of them (k = 2) are not: no assignment has t above 19.
  - **Half the aggregators match the baseline only if each proves twice as much** (k = 4, A = 32): t between 22 and 25, against 24.
  - **Halving k at the same 64 aggregators** raises t to at least 33 and halves the proving. The 64 proofs remain, each over half as many signatures, and a full merge takes 32 of them, which is two levels at m = 16.
  - **Bytes** follow the number of proofs where the load per aggregator is unchanged. Where it changes they also depend on how a proof's size moves with the signatures it covers, which is not measured here.
  - **The price of a smaller k is per-vote tolerance:** k floods silence a chosen subnet instead of 4.
- **In a round of per-slot assignments, how failures are counted decides how much of this is left.** [Aggregator selection](../../pq-gasper/aggregator-selection.md) states the flooding threat both ways: "~21 machines flooded at any moment, i.e. 684 floods of a few seconds per epoch". The example is that PQ Gasper epoch, 32 slots × 64 aggregators.
  - **Counted over the round, almost nothing is left.** Dispersal only spreads losses across the aggregators of one instance. An attacker able to fail all of a slot's aggregators at once takes whole slots, which costs one failure per aggregator under any assignment: 684 floods redundant, at most 704 for any per-slot dispersed assignment (+3 %). Against this count dispersal pays only if the scope is one instance: coverage sets that span the round, and failures that last it.
  - **Counted at one time, all of it is left** (added on integration). An attacker limited in how many aggregators it fails at the same moment breaks the round exactly when it can break one slot, so the single-instance numbers apply. Redundant: 24 at once. A plane over 256 subnets in every slot: no attack with fewer than 43 at once, and at least 1,203 floods per epoch for an attacker held to 48 at once.
- **Random failures and partial maps: no change in expectation.** p^k per subnet under any assignment. The plane only narrows the spread (P(break) 1.1 % vs 2.2 % at p = 0.5, equal at p = 0.7). The partial-map thresholds of [aggregator selection](../../pq-gasper/aggregator-selection.md) do not move.
- **Subnet count.** Dispersal wants **many subnets per aggregator**: S ≳ (A/k)² for a plane, d ≫ k for random. The subnet count is then decoupled from the merge fan-in, because a merge takes proofs (aggregators), not subnets. So 64 or more subnets are viable as long as A/k ≤ m; the 16 → 1 merge limit argues for few *aggregators per cover*, not few subnets.
- **Aggregators on a few whole subnets** (added 2026-11-25, [below](#aggregators-on-a-few-whole-subnets)). Yann's design keeps today's 64 subnets and gives an aggregator 4 of them, which is the load of one committee in the `pq` spec. With the spec's 64 aggregators, finality breaks at 37 machines per slot when each of the 4 layers regroups the subnets along another direction of a grid, and at 30 to 35 with a fresh shuffle per layer. It stays at the spec's 24 or 25 when the layers repeat or slide, and at 27 or below when aggregators draw on their own. 48 aggregators in three layers match the spec. Against today's p2p stack, which breaks at 352 with 1,024 known aggregators on one subnet each, 512 aggregators on 4 subnets are enough. One layer is the 16 children of a full merge; after failures the merger needs 16 to 21.

## The model

- One **instance**: S subnets, A aggregators, every subnet covered by exactly k aggregators, every aggregator covering exactly d subnets. Each aggregator proves its d·n votes; load per aggregator and in total (A·d·n = k·S·n proved signatures) is the same for every assignment with the same (S, d, k), so all comparisons below are at equal load.
- A subnet has no proof when all its k aggregators fail. No fallback, no late re-proving.
- **Duality** (also proved in the formal topic): t(q) = min over sets T of x subnets of |N(T)|, the aggregators touching T. Redundant groups make |N(T)| = k·⌈x/d⌉, the smallest possible.

## Results

### Yann's example: 16 subnets, 16 aggregators, d = k = 4

| | t(1/3) | fewest failures to lose ≥ j subnets, j = 1..8 |
|---|---:|---|
| floor (any assignment) | 6 | |
| redundant, 4 groups of 4 | 8 | 4 4 4 4 8 8 8 8 |
| 200 random biregular draws | 9 (9×), 10 (124×), 11 (67×) | |
| affine plane AG(2,4), 4 classes | **12** | 4 7 9 10 12 12 13 14 |
| ceiling (any assignment) | 13 | |

- Plane: any 4 live aggregators cover ≥ 10 subnets, any 5 cover ≥ 12, any 8 cover ≥ 14. Redundant: 4, 8, 8.
- Your scratch numbers all reproduce: 8, 12, the 10/12 coverage, and the random histogram exactly (same draw method, different seed).
- **Is 12 optimal?** The averaging ceiling says t ≤ 13. t = 13 would need every 4 aggregators to cover ≥ 11 subnets. Simulated annealing over k-regular assignments got stuck at a violation cost of 72–85 (the plane scores 48 and is not a local optimum of that walk either), and a CaDiCaL SAT encoding with the obvious symmetry breaking ran out of its 25-minute budget. Unresolved. A Glucose run was still going in the worker's orb when it reported, set to time out on its own; its outcome is not recorded here.
- **The plane's 12 has two proofs.** The survivor count in Lean ([formal topic](../formal/README.md), `affine_threshold`), and Tanner's bound below, which gives 11.3 for 6 subnets and so 12.

### Same 16 aggregators, same load, finer subnets

Each aggregator proves the same d·n = 4·n votes; the voter set is cut into S subnets of 64·n/S voters each.

| S | d | redundant | 5 random balanced draws (exact) | union bound, t ≥ (p > ½) | ceiling |
|---:|---:|---:|---|---:|---:|
| 16 | 4 | 8 | 10 ×5 | 9 | 13 |
| 32 | 8 | 8 | 11 ×5 | 10 | 13 |
| 64 | 16 | 8 | 12 ×5 | 11 | 13 |
| 128 | 32 | 8 | 12 ×5 | 12 | 13 |
| 256 | 64 | 8 | 13 ×5 | 12 | 13 |
| 1,820 (one subnet per 4-set) | 455 | 8 | 13 | | 13 |

So **the gain grows with subnets per aggregator**, and random assignment needs no algebra once d is large.

### Larger instances (q = 1/3)

| A | k | S | d | redundant (= floor) | random, t ≥ | plane, t ≥ | ceiling |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 32 | 4 | 32 | 4 | 12 | 18 (CP-SAT, exact) | RS net: 20 (exact) | 25 |
| 64 | 4 | 64 | 4 | 24 | 27 | | 49 |
| 64 | 4 | 256 | 16 | 24 | 39 | 43 | 49 |
| 64 | 4 | 4,096 | 256 | 24 | 47 | | 49 |
| 64 | 2 | 1,024 | 32 | 22 | 30 | 33 | 38 |
| 64 | 8 | 64 | 8 | 24 | 43 | 52 | 57 |
| 128 | 4 | 1,024 | 32 | 44 | 84 | 86 | 98 |

"random, t ≥" is a union bound: a uniformly random assignment has at least that tolerance with probability > ½ (real draws do better, as the 16-aggregator table shows). "plane" is the spectral guarantee, not the exact value. As shares of A for large instances:

| k | floor = redundant | plane k·q/(1+(k−1)q) | ceiling q^(1/k) | fixed d = 4, random (first-moment) |
|---:|---:|---:|---:|---:|
| 2 | 0.333 | 0.500 | 0.577 | 0.386 |
| 4 | 0.333 | 0.667 | 0.760 | 0.488 |
| 8 | 0.333 | 0.800 | 0.872 | 0.569 |

The last column is the regime "d fixed, scope grows": random assignments with small d stay far from the ceiling; structured ones (planes, d = A/k) do not.

### Scopes made of many instances

Failures are counted over the whole scope in this section, and at one time in the next.

- Fewest failures to lose a third of a scope of I copies of Yann's instance: redundant 44 vs plane 47 at I = 8 (128 aggregators), 172 vs 175 at I = 32. Reproduces your scratch numbers.
- Reason: losing a whole instance costs all of its aggregators under any assignment, and a threshold over many instances is reached by whole instances. Dispersal then only helps the one partial instance.
- **Per-slot dispersal in a 32-slot epoch:** 684 floods per epoch redundant; any per-slot assignment ≤ 10 whole slots + one = 704.
- **What a failure is in time decides whether coverage sets can span the round.** If the attacker floods a machine for the seconds in which it proves one slot, each (aggregator, slot) duty is its own failure unit, and an aggregator whose coverage set spans slots is just several independent duties: back to the many-instances case. Spanning helps only against failures that last for the round (machine down, operator withholding, a captured aggregator), or if each aggregator proves its whole coverage set at once at the end of the round, which is a latency and late-inclusion cost.

### Failures counted at one time

Added on integration by the oversight thread (section 8 of the script); not checked by anyone else.

- **The count.** The attacker fails at most c aggregators at the same moment. Each instance is on duty at a different time, so it fails at most c in each. Flooding capacity limits an attacker this way. A cost per target, such as finding a machine's address or corrupting its operator, limits the total over the round instead.
- **A scope of alike instances breaks exactly when one of them does:** c ≥ t(q) of one instance. The loss adds up over instances and each is limited separately, so the largest loss of the scope is I times the largest loss of one instance under c failures.
- **Scope of 32 copies of Yann's example**, fewest failures over the scope by c (exact; "none" means no attack):

  | c, most failures in one instance | 7 | 8 | 11 | 12 | 13 | 14 | 15 | 16 |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|
  | redundant | none | 172 | 172 | 172 | 172 | 172 | 172 | 172 |
  | plane | none | none | none | 345 | 321 | 266 | 219 | 175 |

  The whole-instance attack that brings the plane down to 175 needs all 16 aggregators of an instance failed at once. Held to 12 at once, the attacker pays twice the redundant total.
- **PQ Gasper epoch, 64 aggregators per slot, k = 4.**
  - Redundant, 16 subnets per slot: 24 at once, in the slots where 6 subnets go; the ~21 of aggregator selection is the average, 684 / 32. 684 floods per epoch.
  - A plane over 256 subnets in every slot: no attack with fewer than 43 at once, and 49 at once always suffice (the ceiling).
  - Floods per epoch against that plane, by the most at once: at least 1,365 at 43, 1,203 at 48, 948 at 56, and 697 to 704 at 64, which is whole slots. These are lower bounds from Tanner's bound, which is concave in the subnets lost in one slot; the exact profile of a 64-aggregator plane was not computed.
- **Which count applies is a question about the attacker,** not about the assignment. It is the open question this topic turns on.

### Against today's p2p stack

Added by the oversight thread on 2026-11-25, when Yann set today's p2p stack as the baseline to test against (section 9 of the script); not checked by anyone else. Figures are per slot. They count aggregators unless they say nodes or machines.

- **The baseline.** 64 subnets with one committee on each in every slot, and a private lottery that targets 16 aggregators per committee: a member aggregates if the hash of its slot signature is 0 mod (n // 16) (consensus-specs @ `d2021d2`, [`phase0/validator.md`](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/phase0/validator.md?plain=1#L733) lines 105 and 733, read 2026-11-25). At 800,000 validators a committee has 390 members, so each aggregates with probability 1/24. In this note's terms that is the redundant assignment with d = 1 and k = 16, about 1,024 aggregators per slot. Finality is lost in a slot once 22 of the 64 committees have no aggregate.
- **Nodes are not validators** (Yann, 2026-11-25). A subnet's topic has about 400 to 500 nodes today, with default nodes on 2 of the 64 subnets. A committee has 390 validators, which vote on the subnet without their nodes being on it, and one node can run many validators. So this section counts three things: aggregators, nodes on a topic, and machines that host validators.
- **Validators are not spread evenly over machines** (Yann, 2026-11-25). The figures in machines take 800,000 validators and three pictures of how they sit on machines:
  - **A measured node list** (Kamil Salakhiev's mapping of validators to the peers they were seen on, over 7 days). It has 13,613 peers, 10,902 of them with validators, and maps 374,983 validators. Peers with more than 10 validators hold 96.0 % of what is mapped, which is the 96 % that [aggregator selection](../../pq-gasper/aggregator-selection.md) has from the 27 Oct call. The list leaves two things open, and its figures are given for each reading:
    - **Repeats.** 37 % of the mapped validators are mapped to more than one peer, up to 20. Three readings: each validator on the largest peer that claims it, split evenly over the peers that claim it, or on the smallest.
    - **Coverage.** It maps fewer than half of 800,000 validators. Two readings: the measured machines host all of them in the measured proportions, or the rest sit on further machines of the same shape.
  - **After Heimbach et al.**, as [aggregator selection](../../pq-gasper/aggregator-selection.md)'s script builds it: 5,000 to 10,000 machines, of which 27 % host one validator and 11 % more than 100. One variant leaves the small machines about 4 % of the stake.
  - **As this repo's benchmarks run:** supernodes that share the validators evenly, next to home nodes of one to three. [devnet-0](../../../benchmarking/devnet-0/description.md) is "about 1/8 of mainnet" with 200 supernodes and 800 home nodes of a single validator; at mainnet scale that is 1,600 supernodes of 496 validators and 6,400 home nodes. [eth-slot-sim](../../../benchmarking/eth-slot-sim.md) is "1/2 the mainnet size" with cloud nodes of "100-1000 validators with a mean of 200" and home nodes of "2-3 validators"; at mainnet scale that is 4,000 cloud nodes and 4,000 home nodes, and here every cloud node gets the mean.
  - The last two are approximations. "In the past we approximated this differently though, both seem valid" (Yann).
- **What the baseline withstands.**

  | What the attacker knows | One committee | Finality, per slot |
  |---|---|---|
  | The nodes on a subnet, not who aggregates (Yann: 16 out of about 400) | 398 of the subnet's 400 nodes, or 497 of 500, for a 90 % chance | every node on 22 neighbouring subnets: 4,600 to 5,750 |
  | A map from validators to machines, not who aggregates | the machines of 388 of its 390 members: 205 to 301 measured, 254 to 370 in the approximations | the machines of the members of 22 committees: 1,236 to 2,713 measured, 1,101 to 3,631 in the approximations |
  | The aggregators, exactly 16 per subnet | 16 aggregators | 352 aggregators, on at most 153 to 238 machines measured, 201 to 314 in the approximations |
  | The aggregators, with the lottery's counts | 16.25 on average | 267 aggregators on average, 247 to 288 in 5 % to 95 % of slots |

  - **Secret, seen from the topic.** The 16 aggregators are among the nodes on the subnet, and the attacker cannot tell which. If it spares j of the N nodes, all 16 are silenced with probability C(N − j, 16) / C(N, 16), and a 90 % chance allows j = 2 at N = 400 and j = 3 at N = 500. A default node backs 2 neighbouring subnets (consensus-specs @ `d2021d2`, [`phase0/p2p-interface.md`](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/phase0/p2p-interface.md?plain=1#L1835) lines 306 and 1835), so a run of 22 subnets has the nodes of 23 starting points out of 64. Silencing them stops those subnets altogether, not only their aggregates.
  - **Secret, with a map.** The attacker floods the machines that host the committee's members, most-loaded first, and wins only if every aggregator is among them, which has probability (23/24)^j when it spares j members. A 90 % chance allows j = 2. This is the blind attacker of [aggregator selection](../../pq-gasper/aggregator-selection.md), which finds 500 to 1,410 machines for PQ Gasper's committees of 1,563.
  - **Known.** Where operators run many validators on a machine, the 352 aggregators of 22 subnets share machines. The figure takes the subnets greedily, fewest new machines first, so the attacker needs that many or fewer.
  - **Known, with the lottery's counts.** The count per subnet is Binomial(390, 1/24), and the attacker takes the 22 thinnest subnets of the slot.
  - **Which row describes today's stack** depends on what leaks. An aggregator that was not on its subnet has to join it and can be seen doing so (aggregator selection, "Watch").
- **Against silencing the voters themselves.** That takes the machines that hold a third of the validators. The measured rows give the three readings of the repeats: largest peer, split, smallest peer.

  | How validators sit on machines | A third of the validators | Secret, with a map: 22 committees | Known: the 352 aggregators |
  |---|---:|---:|---:|
  | Measured, on the measured machines | 22 / 41 / 47 | 1,236 / 1,659 / 1,942 | 153 / 189 / 201 |
  | Measured, the rest on further machines of the same shape | 48 / 87 / 102 | 1,741 / 2,340 / 2,713 | 198 / 229 / 238 |
  | After Heimbach et al., 5,000 machines | 112 | 1,101 | 201 |
  | After Heimbach et al., 8,000 machines | 206 | 1,768 | 251 |
  | After Heimbach et al., 10,000 machines | 286 | 2,209 | 272 |
  | 8,000 machines, small ones hold about 4 % of stake | 185 | 1,191 | 237 |
  | Benchmark shape of devnet-0: 1,600 supernodes of 496, 6,400 home nodes of 1 | 538 | 1,659 | 285 |
  | Benchmark shape of eth-slot-sim: 4,000 cloud nodes of 197 or 198, 4,000 home nodes of 2 or 3 | 1,347 | 3,631 | 314 |

  - **Measured, a third of the validators sit on 22 to 102 machines.** The largest machine holds 2.2 to 5.2 % of the validators and the ten largest 11 to 21 %. The approximations are less concentrated.
  - **Secret aggregators cost more than the voters under every picture:** 26 times or more measured, 2.7 times or more in the approximations. The attacker that sees only the topic, at 4,600 to 5,750, is above that again. The aggregators are then not the weak point.
  - **Known aggregators cost more than the voters measured,** 2.3 to 7 times. In the approximations it is 0.95 to 1.8 times after Heimbach et al., and a half or a quarter in the two benchmark shapes. The more concentrated the hosting, the lower the voters' level, and the better known aggregators compare with it.
  - **Machines are not alike.** The machines that hold a third of the validators are the largest ones. Flooding is "easy against home links and harder against data-center machines behind provider DDoS protection" ([aggregator selection](../../pq-gasper/aggregator-selection.md)), and whether large operators' machines can be flooded for a few seconds is that note's crux. The count treats all machines alike.
  - **A first version compared with 8,334,** a third of a slot's voters. That counts validators, not machines.
  - **At the `pq` spec's scale** a slot's 64 aggregators sit on 52 to 60 machines measured and on 59 to 64 in the approximations. The next section counts what that does to the attack.
- **A share of stake censoring or withholding.** The baseline's lottery leaves a committee without an aggregator outside a third of stake with probability 0.0017 %, and withholding alone halts finality from 33.3 % of stake.
- **The design measured against it** is the next section: 512 aggregators on 4 subnets each match the 352, and 1,024 break at 746 to 773.

### Aggregators on a few whole subnets

Added by the oversight thread on 2026-11-25, for the design as Yann corrected it that day:

- an aggregator takes a few whole subnets, at random or round robin;
- it proves no more than an aggregator of the [`pq` spec](../../../specs/README.md#pq-gasper);
- about 16 aggregates then cover the slot.

The figures are section 10 of the script, and parts 2 and 3 of `exact.py` where a row says exact or CP-SAT; not checked by anyone else. Machines are counted per slot, with one role per machine and the aggregators known. Finality is lost with 22 of the 64 subnets.

- **The example.** The baseline's 64 subnets, and d = 4 of them per aggregator. That is a 16th of the slot's voters, 1,562.5 signatures at 800,000 validators, which is exactly one of the `pq` spec's 16 committees. S/d = 16 proofs cover the slot, as one proof per committee does in the spec. Only S/d and the load d·n are taken from the spec; S and d stay parameters.
- **Layers.** A layer is one pass of a round robin: 16 aggregators that take 4 subnets each and together take every subnet once. k layers are 16·k aggregators and give every subnet k of them. The `pq` spec's 64 aggregators are 4 layers that deal the subnets the same way every time.
- **64 aggregators, by how the layers deal the subnets.**

  | Deal | Most subnets two aggregators share | Finality breaks at | How the figure is known |
  |---|---:|---:|---|
  | The same in every layer: the `pq` spec's layout | 4 | 24 | 6 groups of 4 aggregators |
  | Shifted by one subnet per layer: sliding windows on a ring | 3 | 25 | a run of 22 subnets touches 22 + 3 windows, and no set touches fewer |
  | No layers: every aggregator draws its 4 subnets on its own | 2 to 3 | at most 27, 26 and 27 in three draws | attacks found by annealing; no lower bound |
  | A fresh shuffle per layer | 2 to 3 | 30 to 35 | at least 30 for all but one shuffle in 10⁹; attacks found at 35, 34 and 35 in three draws |
  | Cube: the subnets on a 4 × 4 × 4 grid, each layer the 16 lines of another direction | 1 | **37** | exact; Tanner's bound gives 33 |
  | Any assignment of 64 aggregators on 4 subnets | | at most 49 | the ceiling |

  - **Round robin has to regroup.** Sliding windows keep neighbours together: an attacker takes a run of 22 subnets and pays 25, one machine more than under the spec's layout. The cube puts two subnets under a common aggregator at most once, as the plane does with d = 16.
  - **Random has to be dealt in layers.** Independent draws give a subnet anything from 0 to 8 aggregators. The attacker takes the thinnest 22, and with 64 aggregators some subnet has none at all in 66 % of draws, 1.03 subnets on average.
  - **What the `pq` layout needs to match:** 7 aggregators per committee, 112 in all, for the cube's 37, and 5 per committee, 80 in all, for the shuffled layers' guaranteed 30.
  - **The cube's 37 is exact.** The search cuts the grid into its four 4 × 4 sheets. It runs over which lines across the sheets are touched, in two directions, and solves the two directions inside the sheets one sheet at a time. `exact.py` checks it against the enumeration of all 2²⁷ sets on the 3 × 3 × 3 cube, against enumeration for up to 5 lost subnets, and against Tanner's bound at every loss. The exact value for shuffled layers is open between the two figures.
- **Three layers match the spec.** 48 aggregators in three cube layers break at 25, exact, against 24 for the spec's 64. That is a quarter fewer proofs, and one vote costs 3 machines instead of 4. By hand it is at least 24: with three layers a subnet is lost when its three lines failed, so a, b and c failed lines of the three directions lose at most √(a·b·c) subnets (Loomis–Whitney), and 22 lost subnets need a·b·c ≥ 484, which takes a + b + c ≥ 24. Three shuffled layers are guaranteed only 20, and one draw breaks at 24 or below.
- **Smaller steps.** The most subnets that f silenced aggregators leave without a proof, exact for the cube:

  | f | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 37 |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
  | `pq` layout | 4 | 8 | 12 | 16 | 20 | 24 | 28 | 32 | 36 | 36 |
  | Cube, 4 layers | 1 | 2 | 4 | 8 | 9 | 12 | 16 | 17 | 21 | 22 |

  The loss unit is one subnet, a 64th of the slot, instead of a committee of four subnets.
- **Counted in machines.** The network adversary silences machines, and a machine that hosts several of a slot's aggregators loses them together. Each draw gives the 64 roles to validators picked at random, so to machines by their share of the validators. The figures are medians over 30 draws, under the pictures of the [section above](#against-todays-p2p-stack); the measured rows give the three readings of the repeats.

  | How validators sit on machines | The 64 roles sit on | `pq` layout | Cube | Shuffled layers, one draw |
  |---|---:|---:|---:|---:|
  | Every role on a machine of its own | 64 | 24 | 37 | 30 to 35 |
  | Measured, on the measured machines | 52 / 55 / 57 | 18 / 19 / 19 | 29 / 30 / 32 | 27 / 29 / 30 |
  | Measured, the rest on further machines of the same shape | 58 / 60 / 60 | 20 / 21 / 21 | 32 / 34 / 34 | 31 / 33 / 34 |
  | After Heimbach et al., 5,000 machines | 59 | 20 | 33 | 32 |
  | After Heimbach et al., 8,000 machines | 62 | 22 | 35 | 34 |
  | After Heimbach et al., 10,000 machines | 62 | 22 | 36 | 35 |
  | 8,000 machines, small ones hold about 4 % of stake | 61 | 21 | 35 | 33 |
  | Benchmark shape of devnet-0 | 63 | 23 | 37 | 35 |
  | Benchmark shape of eth-slot-sim | 64 | 24 | 37 | 35 |

  - **The `pq` layout's figure is exact:** the fewest machines that host every aggregator of 6 committees. The other two are attacks found by a short annealing, so the true figure is that or lower. Where no machine is shared, that annealing finds 37 or 38 against the exact 37.
  - **The gain stays** at 1.5 to 1.7 times the `pq` layout under every picture.
  - **Against the voters' level, measured.** The `pq` layout's 18 to 21 machines are below the 22 to 102 that hold a third of the validators in every reading. The cube's 29 to 34 are above them in the most concentrated reading, 29 against 22, and below them in the other five.
- **More layers.** 16·k aggregators on 4 subnets each:

  | Layers k | Aggregators | `pq` layout | Shuffled layers, guaranteed | Attack found on one draw | Ceiling |
  |---:|---:|---:|---:|---:|---:|
  | 2 | 32 | 12 | 12 | 13 | 19 |
  | 3 | 48 | 18 | 20 | 24 | 34 |
  | 4 | 64 | 24 | 30 | 35 | 49 |
  | 6 | 96 | 36 | 50 | 57 | 79 |
  | 8 | 128 | 48 | 71 | 80 | 105 |
  | 16 | 256 | 96 | 162 | 174 | 210 |
  | 32 | 512 | 192 | 353 | 366 | 421 |
  | 64 | 1,024 | 384 | 746 | 773 | 843 |

  - **Guaranteed** is a first-moment bound: a draw breaks at no fewer, except with probability 10⁻⁹ over the shuffles. The gain over the `pq` layout grows with k, from nothing at 2 layers to 1.9 times at 64.
  - **The ceiling** is the lower of two averages. One is over random failure sets, about q^(1/k)·A as above. The other is over random sets of x subnets, which touch a share 1 − C(S − x, d) / C(S, d) of the aggregators. With d = 4 that is 0.82·A, however many layers there are.
- **Against today's p2p stack**, which has 1,024 aggregators on one subnet each and breaks at 352 ([above](#against-todays-p2p-stack)):
  - **Same resilience:** 512 aggregators in 32 shuffled layers are guaranteed 353. That is half the aggregators, each proving four subnets, so twice the proving.
  - **Same aggregators:** 1,024 in 64 layers break at 746 to 773. Today's layout would need 34 to 36 aggregators per subnet for that. The proving is four times today's.
  - **Same proving:** 256 aggregators in 16 layers prove every vote 16 times, as today, and break at 162 to 174, about half of 352. With one subnet per aggregator t = k·x, and an assignment with the same k and larger d has a d-th of the aggregators to silence.
  - **So the design is a better use of proofs, not of proving.** Under PQ every aggregator is a proof to carry and to merge: 209 KiB for 1,400 signatures in the leanVM benchmark ([sources](../../pq/README.md)), with a merge of 16. How a proof's size moves with fewer signatures is not measured here. At the `pq` spec's 64 proofs per slot and its load per proof, layers buy 25 to 54 % over the spec's layout.
- **What 16 aggregates cover.** Yann's expectation is that any 16 aggregates, or a bit more, cover the whole validator set with high probability.
  - **It holds for the 16 a merger picks, when nothing failed:** one layer is 16 disjoint proofs that cover all 64 subnets.
  - **It does not hold for 16 taken at random** from the 64: they cover 44.4 subnets on average, more than two thirds in about 80 % of cases, and never all 64 in 4,000 samples. 24 at random cover 54.8, 32 cover 60.4, and 48 cover all 64 in 83 % of cases.
  - **Independent draws need many more.** 16 aggregators that each draw 4 subnets cover 64 % of them on average. All 64 are covered with probability 34 % at 64 aggregators, 90 % at 100 and 98 % at 128.
- **The merge after failures at random.** f of the 64 aggregators fail. The first two rows are 400 failure sets each, from the script. The last two are 12 failure sets each, by CP-SAT.

  | f = 8 / 16 / 24 failed | `pq` layout | Cube | Shuffled layers, one draw |
  |---|---|---|---|
  | The survivors still cover all 64 subnets | 100 / 96 / 74 % | 100 / 84 / 29 % | 99 / 82 / 32 % |
  | 16 disjoint survivors cover all 64, a full merge of 16 | 100 / 96 / 74 % | 99 / 27 / 1 % | 32 / 2 / 0 % |
  | Fewest children for all that the survivors cover | 16 or fewer | 16 / 16 to 20 / 18 to 20 | 16 to 19 / 18 to 21 / 19 to 21 |
  | Subnets the best 16 children cover, on average | all that is left | 64 / at least 61.9 / at least 59.4 | at least 62.5 / 59.2 / 57.2 |

  - **The same expected loss, in another shape.** Under any assignment with k = 4, f failures at random leave 0.18 subnets without a proof on average at f = 16 and 1.07 at f = 24. The `pq` layout loses rarely and four subnets at a time. Layers lose more often and one subnet at a time.
  - **"16 or a bit more" holds for the merger, and the bit is up to 5.** With a quarter to three eighths of the aggregators gone it needs 16 to 20 children under the cube and 18 to 21 under shuffled layers. leanVM merges 16 today, so that is a second merge level, or 16 children that leave 2 to 7 of the 64 subnets out on average.
  - **The cube keeps a full merge of 16 longer than shuffled layers,** because lines of different directions also combine into disjoint covers, for example the rows of one sheet of the grid with the columns of another. Shuffled layers rarely do: 4 failures already rule a full merge of 16 out in 10 % of cases, which is how often they hit all four layers.
  - **What is proved.** The fewest children are proved optimal in every cube row, and in 6, 10 and 12 of the 12 cases for the shuffled draw; the others are upper bounds. "At least" marks coverage that CP-SAT found without proving it the best.
- **What it would change in the `pq` spec** (the oversight thread's reading of the spec at `4c29678`; nobody reviewed it).
  - Gossip rejects an aggregate unless "Exactly one committee is specified by the committee bits". An aggregate would name its d subnets.
  - Gossip ignores an aggregate when one aggregate already seen has a superset of its bits, and `should_broadcast_aggregate` keeps a later aggregator silent on the same condition. Under layers no single earlier aggregate covers a later aggregator's set, so both would have to compare with the union of what was seen. The spec's staggering then maps onto layers: the first layer publishes, and an aggregator of a later layer publishes only if some of its votes are still missing.
  - An aggregator subscribes to d subnets instead of one and receives as many votes. A node that only backs subnets carries less: with `SUBNETS_PER_NODE = 2` it holds 2 of 64 subnets instead of the spec's 2 of 16 ([design note](../../pq-gasper/design.md), "Backbone").
  - The assignment is public, as the spec's aggregation committees are.
- **Kept in the design space** (Yann, 2026-11-25).
  - **Secret and known aggregators.** Knowing the aggregators in advance reduces security: they can be targeted, and aggregators may be less protected than proposers (Yann). The figures of this section are for known aggregators, which is the only regime in which the assignment matters.
  - **Grid and shuffled layers.** Shuffling seems to induce more churn on the subnets, and is worth keeping if it gives higher resilience (Yann). In this example it does not: the cube breaks at 37 and shuffled layers at 30 to 35. What the shuffle has is that it exists for any S and d.
    - Per duty the two cost the same joins. An aggregator's node joins the subnets of its set that it does not already back: 4·(1 − 2/64) = 3.9 on average for a default node, against 1 − 2/16 = 0.9 for one subnet of 16 in the `pq` spec.
    - What differs is that the cube's sets are the same 64 lines in every slot, so a subscription can be kept from one duty to the next, or the nodes that back subnets can be arranged along lines. A fresh shuffle has new sets every time. How often a shuffle is redrawn is a free parameter, since its bound holds for any one draw. None of this is computed.
  - **Both ways out for a merger** that has no 16 disjoint proofs left: a second merge level, and 16 children that leave some subnets out.
  - **The last level as a public fallback.** Its merge could be run by a sample selected to aggregate, by dedicated machines, by the proposers of the last k slots ([builders note](../../../posts/pq-gasper-builders.md)), by volunteers, or by anyone (Yann). The properties file sets the last against Sybil resilience.
- **What the comparison leaves out.**
  - **A draw, not a lottery.** The figures take exactly k aggregators per subnet and stand against the baseline's 352 for exactly 16 per subnet. A lottery in place of the draw was not computed.
  - **Only the regime of known aggregators.** A blind attacker has to silence every node on a subnet whatever the assignment, so layers gain nothing against it; that is reasoning, not a computation. An aggregator that joins d subnets is also easier to see than one that joins its own, which is the oversight thread's inference from aggregator selection's "Watch" and not a measurement.
  - **Machines only for a slot's 64 aggregators.** The figures for 512 and 1,024 aggregators count aggregators and were not redone in machines, where many of them share one.
  - **Other S and d.** The cube is one construction, for 64 subnets and 4 per aggregator. Shuffled layers work for any S and d; structured layers for other sizes were not looked for.
  - **Censoring and withholding** depend on k, not on the assignment: a vote is kept out when all k aggregators of its subnet are adversarial.
  - **Who merges and when.** The merge counts take a merger that sees every surviving proof.

### Random failures and capture

- p^k per subnet under any assignment, so expected loss and the partial-map thresholds ("76 % of honest stake floodable halts finality" for 4 per subnet) are unchanged.
- P(≥ 6 of 16 subnets lost), each aggregator down w.p. p: redundant 0.38 / 2.2 / 8.4 / 24.5 % at p = 0.4 / 0.5 / 0.6 / 0.7; plane 0.11 / 1.1 / 6.7 / 25 %. Dispersal helps only in the tail, and not near the threshold.
- Capture of one subnet is β^k either way. A stake-holding attacker who captures several aggregators of one subnet group under redundant assignment gets d subnets at once; under dispersal it gets each subnet only if it holds all k of *its* aggregators. Same expectation, smaller loss unit.

## Costs

- **Per-vote tolerance stays k.** Dispersal buys threshold tolerance, not protection of a chosen validator. Using it to cut k (the table in the short answer) lowers per-vote tolerance to the new k.
- **Subscriptions.** An aggregator joins d subnets instead of 1 and receives d·n votes either way. A plane over 256 finer subnets needs 16 small topics per aggregator. Yann's constraint, set on 2026-11-25, is a few whole subnets: 4 of today's 64 in his example.
- **Merge.** One parallel class of a plane is A/k disjoint proofs that cover every subnet, so with no failures a full merge takes A/k children, as under redundant assignment (one proof per group). After failures the merger replaces a failed proof with proofs from other classes, each overlapping the rest; in a plane a failed line needs up to d replacements. leanVM merges overlapping children, at one guest slot per extra occurrence of a claim; that cost is unmeasured. Keeping A/k ≤ m (16) keeps one merge level. A random assignment is not built from disjoint covers; whether it contains one, and how many proofs its smallest cover takes, was not computed. For layers of 16 aggregators on 4 subnets it is, in ["Aggregators on a few whole subnets"](#aggregators-on-a-few-whole-subnets).
- **Assignment publicity.** The plane is public like today's draw; only which machine gets which line is random. Nothing here needs secrecy.
- **Machines, not aggregators.** A super node holding several aggregator seats fails them together. The assignment should not give one machine two seats of one instance; otherwise t counts machines, not aggregators.

## Merge level

The blob topic's coded-cell proposal makes mergers the failure point one level up. The model is the same with subnets → child proofs and aggregators → mergers: k′ mergers per proof, each taking d′ proofs, and the same floor, ceiling and plane results apply. Not computed further here.

## Suspicions checked

- 12 optimal for 16/16/4/4: **open**, see above. 13 is the hard upper limit for any assignment.
- Per-slot dispersal buys almost nothing for a round threshold: **confirmed when failures are counted over the round** (≤ +3 % for a Gasper epoch), with the time-of-failure caveat above. **Not when they are counted at one time** (added on integration): there it keeps its whole gain.
- Partial maps are the random-failure case: **confirmed** for expectation; the plane slightly thins the tail.
- Literature: the ceiling is a first-moment (averaging) argument; the plane bound is Tanner's bound for bipartite expanders; random assignments are lossless/unbalanced expanders (Capalbo–Reingold–Vadhan–Wigderson) and dispersers. Not checked against papers (web access was off).

## Open questions

- Is t = 13 reachable at S = A = 16, d = k = 4?
- Explicit families that approach q^(1/k)·A with small d (large d is easy with random assignment).
- Merge cost of overlapping children in leanVM, and how many replacements a merger needs under worst-case failures.
- ~~Which count describes the attacker of [aggregator selection](../../pq-gasper/aggregator-selection.md): machines flooded at once, or floods over the round.~~ Decided by Yann on 2026-11-25: machines per slot, under which dispersal inside a slot pays in full.
- The exact profile of a plane with 64 aggregators. The numbers for failures counted at one time are lower bounds.
- The exact tolerance of shuffled layers, which is between 30 and 35 with 64 aggregators on 4 of 64 subnets, and structured layers for other S and d than the 4 × 4 × 4 cube.
- A staggering rule and a gossip rule for layers: what an aggregator of a later layer publishes, and what replaces the superset rule, when no single earlier aggregate covers its set.
- What a merger does when no 16 disjoint proofs are left: a second merge level, or 16 children that leave a few subnets out.
