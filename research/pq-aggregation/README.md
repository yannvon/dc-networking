---
title: PQ aggregation strategy
status: wip
date: 2026-11-25
provenance: agent
---

> **Provenance: agent.** Set up 2026-11-25 by an agent at Yann's request, as the index of a new workstream. The three topics are Yann's. Their framing here is the agent's, and Yann has not reviewed it line by line.
> - Each topic has a note written by a worker thread and reviewed the same day by the oversight thread, which reran the scripts of the dispersed and blob notes, re-derived the dispersed note's two bounds, rechecked the blob note's cited figures, and rebuilt the Lean project from a clean copy.
> - Two results in section 1 are the oversight thread's own. Counting failures at one time was added during that review, and its script is checked against brute force on small cases. The comparison against today's p2p stack was added afterwards, when Yann set that baseline, and redone the same day for aggregators on a few whole subnets, after Yann rejected a first version built on slices of committees. Its figures are checked by a second script of the same thread. Nobody else has read either.
> - Yann answered four open questions on 2026-11-25. The nodes on a subnet are not its validators, which corrects the baseline. And three choices stay open: secret or known aggregators, grid or shuffled layers, and what a merger does after failures. They are in "Design space" below. He also corrected that validators are not spread evenly over machines. The figures in machines now come from a measured node list, which is not in this repo and of which only aggregates are published, and from two approximations: the shape Heimbach et al. measured and the shapes of this repo's benchmarks.
> - Background from public sources was added the same day, at Yann's request: three research subagents read consensus-specs, ethresear.ch and the Eth R&D Discord archive, and the oversight thread checked their notes and worked them into the properties as items tagged `external`. The notes and how they were checked are in [`background/`](background/README.md). The rows marked `external` under "Design space" come from there, and Yann has not seen them.
> - On 2026-11-26 Yann answered three open points, and the oversight thread worked them in the same day. The reference spec is "the one francesco (fradamt) worked on this week", which an agent took to be the `pq-dc` branch of `ethlabs-org/consensus-specs` ([`specs/`](../../specs/README.md)). Asked whether that is the one, Yann answered "I think perhaps, but check also /ethereum/consensus specs"; upstream was read the same day, and [`specs/`](../../specs/README.md#where-upstream-differs) says where it differs. The five properties from public sources "sound good for now" and stay. And blobs are "a specific type of transaction", which is the first of the three readings in the blob note, with blob streaming as what may come. Nothing in sections 1 to 3 was recomputed for the reference spec.

# PQ aggregation strategy

**What this is.** How finality votes get from the subnets onto the chain under PQ-DC: who proves which votes, how the proofs are merged, and how they travel. It continues [Q21](../open_questions.md), the aggregation tree.

**How it is judged.** By the properties in [`properties/aggregation-broadcast.md`](../../properties/aggregation-broadcast.md): safety, liveness against each type of adversary with DoS resilience first, and performance, each tested against today's p2p stack as the baseline. Yann set that frame on 2026-11-25, after the three notes below were written, so they still say "fault tolerance" and "tolerance" for what the file now calls DoS resilience. That file defines the terms and symbols used here: scope, instance, S, n, k, d, A, m, t(q).

**What others have said.** [`background/`](background/README.md) holds what consensus-specs, ethresear.ch and the Eth R&D Discord say about these properties: 116 entries with quotes, the properties they state that ours lacked, and where they contradict ours. No source read has a dispersed assignment of aggregators, or aggregates carried in blobs.

**Which spec** (Yann, 2026-11-26). Francesco's `pq-dc` branch, read at `1e9307b` ([`specs/`](../../specs/README.md)), which is an agent's reading of "the one francesco (fradamt) worked on this week". It leaves this workstream's whole subject open, as upstream's `pq-dc` does: aggregator selection, the aggregate messages and their deadlines are TODOs. What it fixes around it:

- **The shape.** A slot has 256 committees of about 390 validators, 16 on each of 16 subnets, and an aggregate may cover any of them. Per subnet and slot that is the shape of Yann's example in section 1: 16 units, of which an aggregator at the `pq` spec's load proves 4.
- **Where a vote counts.** An FG vote reaches fork choice only through a block. So its aggregate has to reach proposers, and other nodes get it in the block.
- **How often a vote is sent.** Once per height. A vote that no proof picked up is not sent again, and it can be included while its target is the chain's current or previous one. That window is Francesco's. Upstream has [another](../../specs/README.md#where-upstream-differs).
- **Not recomputed.** The figures of sections 1 and 2 are for the `pq` spec's 16 committees per slot and for 64 subnets. Redoing them on this shape is under "Other components".

**Kept general.** The number of subnets is an output of the strategy, not an input. Notes in this folder state results in those symbols and use concrete numbers only as examples.

## Topics

| | Topic | Question | Note |
|---|---|---|---|
| [Q26](../open_questions.md) | Dispersed aggregator assignment | Does giving each aggregator a different set of subnets buy fault tolerance at the same load, and how much? | [`dispersed-assignment/`](dispersed-assignment/README.md), reviewed |
| [Q27](../open_questions.md) | Blobs for aggregate propagation | Can aggregates travel as blobs, instead of through a large-message broadcast such as SEACAST? | [`blob-propagation/`](blob-propagation/README.md), reviewed |
| [Q28](../open_questions.md) | Formal framework | Exact definitions of the aggregation properties, so that strategies can be compared on them | [`formal/`](formal/README.md), reviewed, builds |

## 1. Dispersed aggregator assignment

**The idea** (Yann, in a chat shared on 2026-11-25). Today the k aggregators of a subnet all prove the same votes. Instead, cut the votes into more, smaller subnets and give each aggregator a different set of them. Every subnet still has k aggregators and every aggregator still proves as many signatures, but no two aggregators do the same work. Yann calls it error correction for aggregation.

**His example.**

- Baseline: 4 subnets with 4 aggregators each, so 16 aggregators. Finality breaks once 2 subnets are lost, which takes 8 failed aggregators.
- Dispersed: 16 subnets, and each of the 16 aggregators covers 4 of them. Every subnet is still covered 4 times.
- The claim to test: higher fault tolerance with the same 16 aggregators, or the same tolerance with fewer.

**Findings** (2026-11-25, [note](dispersed-assignment/README.md), [`sim/dispersal.py`](dispersed-assignment/sim/dispersal.py) and [`sim/exact.py`](dispersed-assignment/sim/exact.py); exact for the example, bounds beyond it; reviewed).

- **For one instance the claim holds.** In the example finality breaks at 8 failed aggregators under the redundant assignment and at 12 under an affine plane, at the same load. No assignment can exceed 13.
- **How much in general.** The failures an attacker needs, as a share of the A aggregators of an instance, at q = 1/3:

  | | Formula | k = 2 | k = 4 | k = 8 |
  |---|---|---:|---:|---:|
  | Floor: the least under any assignment, and where the redundant one sits | q | 0.33 | 0.33 | 0.33 |
  | Affine plane, guaranteed | k·q / (1 + (k − 1)·q) | 0.50 | 0.67 | 0.80 |
  | Ceiling: the most under any assignment | q^(1/k) | 0.58 | 0.76 | 0.87 |

  - **Ceiling.** A random set of f failures loses each subnet with probability C(f, k) / C(A, k), and some set loses at least the average. So dispersal buys at most a factor of 1.73, 2.28 and 2.62 at k = 2, 4 and 8.
  - **Plane.** S = w² subnets on a grid. The aggregators are k classes of w parallel lines, so d = w and A = k·w. The guarantee is Tanner's bound for expander graphs.
  - **Random assignments** get near the ceiling only when each aggregator covers many more subnets than k. With the example's 16 aggregators at the same load, five random draws all break at 10 with 16 subnets, at 12 with 64 and at 13 with 256.
- **It can be spent on fewer aggregators or less replication.** Against the redundant assignment with k = 4 and 64 aggregators, which breaks at 24 failures:

  | Plane | Breaks at | Load per aggregator | Proofs | Per-vote tolerance |
  |---|---|---|---|---|
  | k = 3, 48 aggregators | at least 29 | same | a quarter fewer | 3 |
  | k = 4, 32 aggregators | 22 to 25 | double | half | 4 |
  | k = 2, 64 aggregators | at least 33 | half | same, and a full merge takes 32 | 2 |
  | k = 2, 32 aggregators | 17 to 19 | same | half | 2 |

  So "the same tolerance with fewer aggregators" holds with three quarters of them at the same load. With half of them the tolerance is about the same only if each proves twice as much; at the same load it falls to 17 to 19.
- **In a round of per-slot assignments the gain depends on how failures are counted, and Yann chose the count per slot** (2026-11-25: the adversary is measured by the machines it attacks at any given time, simplified to per slot). So the second count below is the one that applies, and dispersal inside a slot keeps its gain. [Aggregator selection](../pq-gasper/aggregator-selection.md) states today's threat both ways: "~21 machines flooded at any moment, i.e. 684 floods of a few seconds per epoch". For that epoch of 32 slots × 64 aggregators:
  - **Counted over the round, almost nothing is left.** An attacker able to fail all of a slot's aggregators takes whole slots, at one failure per aggregator under any assignment: 684 floods redundant, at most 704 for any assignment that stays inside a slot. Under this count the gain needs coverage sets that span the round, and failures that last it.
  - **Counted at one time, all of it is left.** If the attacker is limited in how many aggregators it fails at the same moment, a round of alike slots breaks exactly when one slot does. Redundant: 24 at once. A plane over 256 subnets in every slot: nothing below 43 at once, and at least 1,203 floods per epoch for an attacker held to 48 at once. With all 64 at once it is 697 to 704 again.
  - The second count is the oversight thread's addition: section 8 of the script, not in Lean.
- **The merge limit bounds aggregators per cover, not subnets.** A plane is k layers that each cut the subnets into A/k disjoint coverage sets, so one layer is a full cover, as one proof per group is under the redundant assignment. A/k ≤ m keeps one merge level whatever S is. After failures a merger fills in with proofs of other layers, which overlap; what that costs in leanVM is not measured.
- **What it costs.** An aggregator joins d subnets instead of one, 16 in a plane of 64 aggregators with k = 4, for the same d·n signatures. A slot then has 256 subnets instead of 16, each a sixteenth of the size. Per-vote tolerance stays k, and so does the redundant proving. Yann's constraint, set on 2026-11-25, is a few whole subnets per aggregator, which rules that plane out; the next point is the design within it.
- **Aggregators on 4 whole subnets** (Yann's design as he corrected it on 2026-11-25; [note](dispersed-assignment/README.md#aggregators-on-a-few-whole-subnets), section 10 of the script and `exact.py`, not in Lean). Today's 64 subnets stay, and an aggregator takes 4 of them, at random or round robin. That is a 16th of the slot's voters, the load of one committee in the `pq` spec. A layer is one pass of the round robin: 16 aggregators that together take every subnet once.
  - **Against the `pq` spec, with its 64 aggregators.** Finality breaks at 24 machines per slot when all 4 layers deal the subnets the same way, which is the spec's layout, and at 25 when each layer shifts the deal by one subnet. It breaks at 30 to 35 with a fresh shuffle per layer, and at 37, exact, when each layer follows another direction of a 4 × 4 × 4 grid. The spec's layout needs 7 aggregators per committee, 112 in all, for 37.
  - **Random only works within layers.** When every aggregator draws its 4 subnets on its own, finality breaks at 27 or below in three draws, and some subnet has no aggregator at all in two draws of three.
  - **The same resilience with fewer.** Three grid layers, 48 aggregators, break at 25, against the spec's 24 with 64.
  - **Smaller steps.** 16 silenced machines leave at most 8 of the 64 subnets without a proof, against 16 under the spec's layout, and 24 leave 12 against 24.
  - **Against today's p2p stack** (Yann's baseline: 64 subnets, 16 randomly chosen aggregators per subnet, and about 400 to 500 nodes on a subnet's topic; [note](dispersed-assignment/README.md#against-todays-p2p-stack), section 9). Today, with the aggregators known: one committee costs its 16 aggregators, and finality breaks at 352 aggregators per slot, or 267 on average with the lottery's uneven counts. 512 aggregators on 4 subnets each, in shuffled layers, match the 352, and 1,024 break at 746 to 773.
  - **It is a better use of proofs, not of proving.** At the same proving as today, 256 aggregators on 4 subnets break at 162 to 174, half of today's 352. Many small aggregators are more machines to silence, and under PQ four times as many proofs to carry and merge.
  - **Today, aggregators secret:** the 16 aggregators hide among the nodes on the subnet's topic, so a blind attacker silences 398 of 400 nodes for a 90 % chance, and every node on 22 neighbouring subnets, 4,600 to 5,750, to stop finality. That stops the subnets themselves. It holds only while subnet joins do not give the aggregators away.
  - **Nodes, validators and machines are three counts** (Yann's correction of a first version, which took the 400 nodes for the committee). Validators are not spread evenly over machines (Yann), and how they are spread decides the comparison. Under a measured node list a third of the validators sit on 22 to 102 machines, and the 352 known aggregators on at most 153 to 238. So today's stack costs 2.3 to 7 times what silencing the voters does with known aggregators, and 26 times or more with secret ones. The node list is not in this repo; only aggregates from it are, as ranges over what it leaves open.
  - **Two approximations are less concentrated.** In shapes after Heimbach et al. a third of the validators sit on 112 to 286 machines, and in the shapes this repo's benchmarks run with on 538 or 1,347; the 352 known aggregators sit on at most 201 to 314. There today's stack with known aggregators costs between a quarter of and 1.8 times what silencing the voters does.
  - **Counted in machines** a slot's 64 aggregators sit on 52 to 60 machines measured. Finality then breaks at 18 to 21 machines under the `pq` spec's layout, exact, and at 29 to 34 under the grid layers, an attack found; in the approximations it is 20 to 24 and 33 to 37. The gain stays at 1.5 to 1.7 times. The spec's layout is below the voters' level in every reading, and the grid layers pass it in the most concentrated one only.
  - **Machines are not alike.** The machines that hold a third of the validators are the largest ones, which are harder to flood than home nodes ([aggregator selection](../pq-gasper/aggregator-selection.md)). The count treats them alike.
  - **16 aggregates cover the slot when the merger picks them:** one layer. 16 taken at random from the 64 cover 44 subnets on average. After 16 of the 64 failed at random, 16 that cover everything still exist in 27 % of cases under the grid layers and 2 % under shuffled ones, against 96 % under the spec's layout.
  - **Not computed:** the exact value for shuffled layers, a lottery in place of an exact draw, and layers for other S and d than this example.

**Proved in Lean** ([formal project](formal/README.md)).

- **A share q of the aggregators is the least any assignment tolerates.** Each subnet left without a proof has k failed aggregators, and a failed aggregator accounts for at most d subnets, so t(q) ≥ k · (⌊q·S⌋ + 1) / d ≈ q·A. The redundant assignment sits at that floor, up to rounding to whole groups. Dispersal can only raise it. (Lean: `floor_bound`, `redundant_bound`.)
- **Random failures cost the same under every assignment.** If each aggregator fails with probability p, independently, a subnet loses all its aggregators with probability p^k, and the expected loss is the same for every assignment with replication k. Dispersal changes which losses come together, and what an attacker who picks its targets can reach. (Lean: `prob_lost`, `expected_loss_uniform`.) In the example, the chance that finality breaks at p = 0.5 is 1.1 % under the plane against 2.2 %, and the two are equal at p = 0.7 (the note's script).
- **t(q) is a property of the coverage graph.** It is the least number of aggregators that touch a set of subnets holding more than a share q of the votes (Lean: `tolerance_eq_min_nbhd`). An assignment is good when every large set of subnets touches many aggregators.
- **Overlap bound.** If two subnets share at most λ aggregators, losing ℓ subnets takes at least k·ℓ − λ·C(ℓ, 2) failures (Lean: `pairwise_bound`). The bound peaks near ℓ = k/λ, so it speaks only about small losses.
- **Yann's example, proved.** 16 subnets, 16 aggregators, d = k = 4. Finality breaks once 6 subnets have no proof.

  | Assignment | Failed aggregators that break finality | Loss unit |
  |---|---|---|
  | Redundant: 4 groups of 4 subnets, 4 aggregators each | 8 (Lean: `redundant_threshold`) | 4 subnets |
  | Affine plane over GF(4): the aggregators are the lines of 4 parallel classes on a 4 × 4 grid | 12 (Lean: `affine_threshold`; also all 65,536 failure sets, enumerated by two independent scripts) | 1 subnet |
  | Random with the same d and k, 200 draws | 9 in 9 draws, 10 in 124, 11 in 67 (the note's script) | not measured |

  The affine plane is at least as good at every number of failures. With 4, 8, 12 and 15 failed aggregators it loses at most 1, 2, 6 and 12 subnets, against 4, 8, 12 and 12 ([`formal/scripts/check_example.py`](formal/scripts/check_example.py)).
- **Why 12, without enumeration** (Lean: `affine_lost_le_five`). Count the survivors. Two lines of one class share no subnet and two lines of different classes share one. Among any 5 aggregators two are of the same class, so at most 9 pairs share a subnet, and the 5 cover at least 5·4 − 9 = 11 subnets. After 11 failures 5 aggregators survive, so at most 5 subnets are lost. The same count gives at most 6, 7, 9 and 12 lost after 12, 13, 14 and 15 failures, which is what the enumeration finds; those four are not in Lean.
  - In general, nothing a surviving aggregator covers is lost, and g survivors cover at least d·g − μ·X subnets, where two aggregators share at most μ subnets and X of the pairs among them share any. Lean has it without the uniform d and μ: the sizes of the survivors' coverage sets, minus the subnets that pairs of them share (`lost_card_add_le_of_survivors`).
  - Layers that each cut the subnets into disjoint coverage sets keep X small, because two aggregators of one layer share nothing. The bound says something only when few aggregators survive, so it settles small examples and not large scopes.
- **A round of per-slot assignments is one assignment over all its slots** (formal note, point 7), so Lean's t(q) counts failures over the round. For rounds of 8 and 32 slots of the example, redundant against plane is 44 against 47 of 128 aggregators, and 172 against 175 of 512 (the note's script). A limit on the failures in each slot is a condition on which failure sets are allowed. That is not in Lean.

**Open.**

- **What limits the attacker** is decided: machines attacked per slot (Yann, 2026-11-25; [DoS resilience](../../properties/aggregation-broadcast.md#dos-resilience)). The test is today's p2p stack in the same regime, secret or known aggregators (Yann, same day). The voters' level stays the ideal. In machines it is 22 to 102 under a measured node list, and 112 to 1,347 in two approximations. No assignment of A known aggregators gets beyond about q^(1/k) · A, which is 49 for the `pq` spec's 64 per slot.
- What an aggregator that listens to d subnets gives away to someone watching subnet joins, and whether a private draw is available at all with PQ signatures. Dispersal pays only where the aggregators are known anyway.
- Whether 12 is the best possible in the example. 13 is the most any assignment could reach; annealing and a 25-minute SAT search in the worker's orb settled nothing.
- Constructions that get near the ceiling with few subnets per aggregator, and the exact tolerance of a plane with 64 aggregators. Its figures above are bounds.
- What merging overlapping children costs in leanVM, and how many replacements a merger needs after failures.
- A staggering and a gossip rule for layers. The `pq` spec lets a later aggregator stay silent, and gossip ignore an aggregate, when one aggregate already seen covers its attesters. Under layers only several earlier aggregates together do.
- What the merger does after failures, when no 16 disjoint proofs are left: a second merge level, or a proof that leaves a few subnets out.
- How a draw produces a good assignment, public or private, and what grinding the seed gains. The plane itself can be public; only which machine gets which line is drawn.
- The literature was not checked, because web access was off in the worker's orb. The note names the bounds without a citation: a first-moment argument for the ceiling, Tanner's bound for the plane, lossless expanders for random assignments.

## 2. Blobs for aggregate propagation

**The idea** (Yann, 2026-11-25). Use blobs as part of how aggregates propagate, instead of a dedicated large-message broadcast such as SEACAST.

**Which blobs** (Yann, 2026-11-26). "blobs are a specific type of transaction", and "they are stored for say 2 weeks only". So he means blob transactions, the first reading below, with blob streaming as what may come.

**Why it is a question.**

- **Aggregates are large.** A leanVM proof over 1,400 signatures is 204 KiB, and the recursion benchmark's is 280 KiB (leanVM [`benchmarks.json`](https://github.com/leanEthereum/leanVM/blob/20a75c102288b6016b5ff8057f8c51c80a222f77/doc/site/benchmarks.json), measured at `be190e9`, read 2026-11-25). That is two to three blobs of 128 KiB.
- **Gossip is slow for objects of that size.** [SEACAST](https://notes.ethereum.org/@cskiraly/seacast) (Csaba Kiraly; version 2, 2026-11-17) sends an object as coded chunks that nodes forward on arrival, push to a few peers and announce to the rest. It reports a 1 MiB payload at 99 % of 500 home nodes after 0.64 s, against 4.5 s with gossipsub. It names consensus blocks with post-quantum signatures among the objects it is meant for.
- **The data-availability layer already moves coded objects.** Blobs travel as cells on column topics, and any half of a blob's cells rebuild it.
- **leanVM proves both.** One guest program checks signatures, checks the encoding of up to 32 blobs, or verifies child proofs of either kind ([`10-ethereum.tex`](https://github.com/leanEthereum/leanVM/blob/20a75c102288b6016b5ff8057f8c51c80a222f77/doc/leanvm/body/10-ethereum.tex) @ `20a75c1`).

**Findings** (2026-11-25, [note](blob-propagation/README.md) and [`arith.py`](blob-propagation/arith.py); arithmetic on downlink floors, not simulation; reviewed).

- **The question becomes who receives a whole proof.** A node that verifies a proof needs every byte of it. The block's proof goes to every node whole. An intermediate proof is verified only by whoever merges it.
- **Three ways to move intermediate proofs.** Examples at 204 KiB per proof, 64 proofs per slot, 3 to 4.5 copies received:

  | Mode | Bytes per node per slot | Who holds a proof |
  |---|---|---|
  | Global whole delivery, today's `pq` spec | 38 to 57 MiB, growing with the number of proofs | every node, whole |
  | Merger topics: proofs whole on per-subnet topics that mergers and the subnet's backers join ([`../pq/README.md`](../pq/README.md)) | 4.8 to 7.2 MiB for a node on 2 subnets of 4 aggregators, whatever the number of proofs; nothing for other nodes | the topic's members, whole |
  | Sampled diffusion: each proof coded into cells, every node custodies 8 of 128 columns, only mergers rebuild | 5.3 MiB at 3 copies, growing with the number of proofs | every node, a share of 1/8 |

- **So far: sampled diffusion if aggregators cover several subnets, merger topics otherwise.** Sampled diffusion beats global delivery by 7× on bytes but not merger topics; at equal copies the two break even at 16 subnets, and merger topics are cheaper above that. What sampled diffusion adds is that a proof keyed by (slot, aggregator) fits any coverage set, and that every node holds part of every proof for late inclusion and builders.
- **What topic 1 changes.** A dispersed assignment gives each aggregator several subnets: 4 in the design Yann means, 16 in a plane of 64 aggregators. If it is taken up, per-subnet merger topics no longer fit a proof, and the choice is between sampled diffusion and merger topics keyed by merger, which are not worked out. What limits the attacker is decided, machines per slot, and under that count dispersal keeps its gain (section 1).
- **It is a use of SEACAST, not a rival.** SEACAST has this mode (interest derived from custody), and the block's proof still goes to every node whole, where SEACAST is the candidate.
- **Latency does not separate the modes,** because the merger receives its children whole in all of them. From the vote deadline: 1.61 to 3.14 s through one merge of up to 16 proofs, 2.35 to 4.62 s through two levels over 64. One level fits Q17's 4 s on all four benchmark machines, two levels only on the faster ones.
- **Today's blobs do not fit.** KZG is not post-quantum, and a leaf proof fills two blobs: 64 proofs need 128 blobs, against 21 per block. The sparse blobpool ([EIP-8070](https://github.com/ethereum/EIPs/blob/e3e214423e3dcbbcfaf1186211ad02971eff98a8/EIPS/eip-8070.md)) is the existing precedent for sampled diffusion before a block.
- **Blob streaming would change one of the three objections** (added 2026-11-26, [note, section 5](blob-propagation/README.md#5-blob-transactions-and-blob-streaming); a reading of the draft, nothing computed). [EIP-8256](https://github.com/ethereum/EIPs/blob/bdc1d099649eefb8790b76f912e25487757f5f4e/EIPS/eip-8256.md), a draft, lets blob data travel ahead of its block on the consensus layer, for senders that bought a ticket on chain for that slot.
  - **Gone:** that sampled blob data arrives only with its block.
  - **Stay:** KZG, the price, and a capacity that the draft leaves open.
  - **New:** an admission rule for an open set of senders, which is payment in advance. It is a third answer to who may publish a proof, next to stake and assignment, and it fits the third level of delivery: a place where anyone who paid can leave a proof for a proposer.
  - **Limits:** a ticket is for one exact slot and is bought a lookahead before it, so it suits duties known in advance. And the path is not post-quantum, so it is for later, not for the first PQ-DC fork.
- **A LeanDA proof is not needed for intermediate proofs,** because their merger rebuilds and verifies them. It may shorten the block: one proof for the votes and the blob encoding instead of two, 290 KiB less if the merged proof is the size of a recursion proof. That is not benchmarked.

**Open.**

- Which blobs Yann meant: answered on 2026-11-26, blob transactions. Open instead: the caps on blobs sent ahead of time, who pays for a ticket, and a post-quantum blob layer.
- The "asynchronous blobs write-up" Yann named is the ethresear.ch post on blob streaming, which section 5 of the note reads. He described it on 2026-11-26: "it might now be called something like blob streaming, it should also mention blob tickets". The earlier texts on blobpool tickets that the post points to are not worked in.
- Merger topics keyed by merger instead of by subnet, which would also fit coverage sets of several subnets. Not worked out.
- How spam is bounded when the nodes that forward cells cannot check the proof. Today the bound is the sender set: one object per (slot, aggregator).
- Mergers become the only nodes that rebuild, and so the ones to flood.
- Any simulation with many proofs from many sources at once. The copies per node at 200 to 300 KiB are read off SEACAST's size figure, not measured.

## 3. Formal framework

**The idea** (Yann, 2026-11-25). State the aggregation properties formally. The aim is exact definitions that make designs comparable and point to more robust ones, not a verified implementation.

- **Where.** A project of its own first. Its likely long-term home is [EthLib](https://github.com/ethereum/EthLib), which has no PQ-DC spec yet.
- **Neighbour.** [verified-consensus](https://github.com/ethlabs-org/verified-consensus), which was `eth-consensus-lean` until a rename that Yann reported on 2026-11-26, proves a protocol with an available chain and a finality gadget correct against a network model that gives finality-gadget attestations a delay bound. Aggregation broadcast is the layer that would have to deliver such a bound.

**Findings** (2026-11-25, [note](formal/README.md) and a Lake project in `formal/`, on Lean v4.36.0 and Mathlib v4.36.0, EthLib's pins; reviewed).

- **It builds from clean sources.** The oversight thread ran `lake exe cache get && lake build` on a fresh copy: 2,076 jobs pass in about 20 s once the Mathlib cache is downloaded. The sources contain no `sorry` and no `native_decide`, and `#print axioms` on 42 of its theorems shows only `propext`, `Classical.choice` and `Quot.sound`.
- **The model.** An assignment gives each aggregator a coverage set. A failure is a set of aggregators that publish nothing, which covers crashing, flooding, withholding and capture. A subnet is lost when all its aggregators fail. Votes are weights per subnet. The numbers of subnets, aggregators and votes stay parameters.
- **Proved for all parameters.** A·d = S·k, per-vote tolerance, the floor, the redundant bound, the overlap bound and its twin on the survivors' side, p^k and the expected loss, the equivalence of t(q) and the coverage profile, that a fallback never lowers a tolerance, that a vote costs as many machines as own its roles, and that h merge levels of fan-in m over proofs of c votes cover at most m^h · c votes.
- **One notion of tolerance.** The fewest failures whose lost set meets a loss criterion. Per-vote tolerance, t(q) and the threshold of a scope with several instances differ only in the criterion.
- **True by how the model is set up, not results.** "Complete in good conditions", "gated acceptance recovers nothing" and soundness hold by definition in the model. Time, bytes, verification work, spam and selection are not modelled.
- **The example.** Redundant t(1/3) = 8 and affine t(1/3) = 12 are both checked by Lean's kernel. The 12 comes from the survivor count of section 1, with no enumeration of failure sets: the kernel checks only the 256 pairs of aggregators. The overlap bound alone gives 9, or 10 when applied at 5 lost subnets. Only the coverage profile at other numbers of failures is still evaluated outside Lean.
- **What topic 1 found that Lean does not have.** The ceiling, the plane's guarantee beyond the example, and failures counted at one time. The first two are short counting and spectral arguments. The third limits which failure sets are allowed, which the model's notion of tolerance can take as it stands.
- **What changed in the prose.** [`properties/aggregation-broadcast.md`](../../properties/aggregation-broadcast.md) now has overlap λ, weights in t(q), redundant work as a consequence of replication under any assignment, roles against machines, and gated acceptance.
- **The interface to verified-consensus is weaker than its network model.** `Delivers.fgAtts` (`ConsensusLean/Spec/Problem/Network.lean` at `c1bf08b`) delivers every finality-gadget attestation of an honest validator within ΔFG. No aggregation design meets that once all k aggregators of a subnet fail. What fits is threshold delivery: for an admissible failure set F, votes outside the lost set arrive within ΔFG, and the lost set holds at most a share q. Liveness in the healthy regime would have to be re-proved from that; accountable safety does not depend on delivery.
- **Towards EthLib.** In EthLib's terms it is a model, next to `EthLib/Consensus/Proofs/Models/Ffg`. Its weights are EthLib's `stake`, and thresholds would become natural-number fractions as in the FFG model. EthLib keeps no examples (its CONTRIBUTING.md, "No examples", at `56d23b9`), so `Examples.lean` stays with this project and the general lemmas are what would move.

## Design space

Choices that Yann kept open on 2026-11-25. Each stays in until something decides it. "For" and "against" hold what this repo has on each option; an empty cell means it was not examined. Rows and cells marked `external` were added from the [background research](background/README.md) and are not choices Yann made.

| Choice | Option | For | Against |
|---|---|---|---|
| Who knows the aggregators | Secret, by a private lottery as today | A blind attacker has to silence nearly every node on a subnet, 398 of 400, to stop its aggregate. `external` The reference spec runs such a lottery for the head vote committee, on a hash tree of per-slot secrets; upstream's `pq-dc` does not ([DoS resilience](../../properties/aggregation-broadcast.md#dos-resilience)) | Needs a PQ VRF. Leaks when an aggregator joins a subnet it was not on. The assignment changes nothing |
| | Known, by a public draw as in the `pq` spec | Simple. The assignment can be structured, which is where dispersal pays: 24 to 37 | The aggregators can be targeted, and they may be less protected than proposers (Yann) |
| | `external` Mixed: a few known, more by a private lottery | No committee is left without an aggregator, which a lottery alone allows, and the rest stay unknown until they publish ([discord F23](background/eth-rnd-discord.md)) | The precedent is a known proposer with secret backups. It names two problems: backups that publish eagerly, and a backup that gains from an attack on the primary ([ethresear.ch 33](background/ethresearch.md)) |
| How aggregators get their subnets | Grid layers | 37 with 64 aggregators, exact. The same 64 sets in every slot. A full merge of 16 survives more failures | One construction, for 64 subnets and 4 per aggregator |
| | Shuffled layers | Exist for any number of subnets | 30 to 35 with 64 aggregators. More churn on the subnets (Yann). Fewer full merges of 16 after failures |
| What a merger does when no 16 disjoint proofs are left | A second merge level | Covers all that is left | Two levels fit Q17's 4 s only on the faster benchmark machines (section 2) |
| | 16 children that leave some subnets out | One level | At most 2 to 7 of the 64 subnets left out on average, after 16 to 24 failures at random |
| Who runs the last merge level, as a public fallback (Yann) | A sample selected to aggregate | `external` About ten sampled per slot were thought to be enough ([discord F30](background/eth-rnd-discord.md)) | |
| | Dedicated machines | | |
| | The proposers of the last k slots ([builders note](../../posts/pq-gasper-builders.md)) | A small, staked sender set | |
| | Volunteers | | `external` "it should still be a selected aggregator, not a volunteer, otherwise it's gonna be a DoS vector" ([discord F30](background/eth-rnd-discord.md)) |
| | Anyone | | Whoever may publish a proof may also flood the topic ([Sybil resilience](../../properties/aggregation-broadcast.md#safety)) |
| | `external` Staked builders | Any proposer can get a bid for the best aggregate (the point on aggregation builders in the [list of properties](../../properties/README.md)) | "I could easily Sybil the builder registry", unless the stake asked for is high ([discord F30](background/eth-rnd-discord.md)) |
| | `external` The proposer alone | It is today's fallback with BLS ([specs 17](background/consensus-specs.md)), and how Gloas aggregates its payload attestations ([specs 22](background/consensus-specs.md)) | It needs the raw votes of every subnet and a prover: "the proposer would need to be on all subnets and smaller stakers may be swamped" ([discord F15](background/eth-rnd-discord.md)) |
| | `external` Anyone who holds a ticket (blob streaming) | An open set of senders that is still bounded: a ticket is paid in advance and not refunded ([blob note](blob-propagation/README.md#5-blob-transactions-and-blob-streaming)) | A draft. Not post-quantum. A ticket is for one slot and is bought a lookahead before it. Somebody pays the blob fee |
| `external` Who aggregates at all | Assigned aggregators, as in the model | | |
| | Nobody assigned: every node folds what it holds on each tick | Nobody to silence (an agent's inference). A node's cost is one proof per tick and peer, and "does not increase as the number of objects that users send in grows" ([ethresear.ch 9](background/ethresearch.md)) | That cost is there whatever the load, 2 MB/s in the post's example of 8 peers and ticks of 500 ms, and every node proves ([ethresear.ch 9](background/ethresearch.md)) |
| | At the source: an operator proves its own validators' votes before gossip | Takes raw signatures off the subnets ([ethresear.ch 22](background/ethresearch.md)) | The [incentives proposal](../../design/incentives.md) is written to discourage it |
| | A role that is opt-in, opt-out or registered | Home stakers can stay out of a duty their machines cannot carry ([discord F31](background/eth-rnd-discord.md)). EIP-8292 specifies the opt-in form for lean consensus, with no stake threshold ([Model](../../properties/aggregation-broadcast.md#aggregators)) | Who is in the set becomes an assumption of its own: it has to be "decentralized enough to guarantee one honest validator per committee in each slot" ([discord F31](background/eth-rnd-discord.md)) |

- **Out of the space:** slices of committees, which put an aggregator in every subnet (Yann). Sliding windows and independent draws gain almost nothing ([section 1](#1-dispersed-aggregator-assignment)).
- **Grid against shuffle on churn.** Per duty both cost an aggregator's node the same joins, 3.9 on average against 0.9 for one subnet of 16 in the `pq` spec. The grid's sets repeat from slot to slot and a fresh shuffle's do not, which is what would let subscriptions be kept. Not computed ([note](dispersed-assignment/README.md#aggregators-on-a-few-whole-subnets)).

## Other components (not started)

- The numbers of sections 1 and 2 on the reference spec's shape: 256 committees on 16 subnets per slot, with aggregates that may span committees and subnets. Whether an aggregator's committees should stay on one subnet, which costs it no extra topic, or spread over several is the first thing to compute ([`specs/`](../../specs/README.md), Yann's choice of spec on 2026-11-26).
- Shape of the aggregation tree and the hardware it assumes ([Q21](../open_questions.md)).
- Aggregator selection without BLS, public draw or private lottery ([Q24](../open_questions.md), [aggregator selection](../pq-gasper/aggregator-selection.md)).
- Proofs for the available chain's head votes, a TODO on the `pq-dc` branch ([design note](../pq-gasper/design.md)).
- Fallback and late inclusion ([aggregator selection](../pq-gasper/aggregator-selection.md), mitigation 1).
- Builders as aggregators ([builders note](../../posts/pq-gasper-builders.md)).
