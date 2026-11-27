---
title: PQ Gasper — interleaved aggregation: 64 subnets with aggregators that span four
status: wip
date: 2026-11-27
provenance: agent
---

> **Provenance: agent.** Written 2026-11-26 and 27 by an agent, on Yann's proposal: keep 64 subnets with a committee of about 400 on each and 4 subnets per node, keep the spec's 64 aggregators per slot, and let each prove 4 subnets, assigned so that every committee has 4 aggregators. Yann has not reviewed it line by line.
> - This is one of two ideas under [multi-subnet aggregation](multi-subnet-aggregation.md), and the note takes it on its own. The other is [voluntary aggregation](voluntary-aggregation.md). Yann chose the names, and on 2026-11-27 he wrote: "aligned vs. interleaved sounds nice".
> - The same idea is studied for PQ-DC as [dispersed aggregator assignment](https://github.com/yannvon/dc-networking/blob/546d9a55e668a863d1d514992b373ca22e31d447/research/pq-aggregation/README.md#1-dispersed-aggregator-assignment) (2026-11-25). On 2026-11-27 that note is in `yannvon/dc-networking`, read at `546d9a5`, and not in `ethereum/dc-networking`, so the links go there. Its section [Aggregators on a few whole subnets](https://github.com/yannvon/dc-networking/blob/546d9a55e668a863d1d514992b373ca22e31d447/research/pq-aggregation/dispersed-assignment/README.md#aggregators-on-a-few-whole-subnets) has this note's layouts under other names: its `pq` layout is the aligned spans, its layers are the cuts, and its shuffled layers are the interleaved spans. The two were computed separately and agree: 24 for the spec, 25 for spans of consecutive subnets, and about 35 for cuts drawn at random, where its attacks are at 34 and 35. Its proven figures are quoted under "DoS resilience" and "Fewer aggregators?". It keeps 2 backbone subnets per node and has an aggregator join its 4 subnets for the duty. Here the 4 are the backbone.
> - Numbers are from [`sim/interleaved_aggregation.py`](sim/interleaved_aggregation.py) (stdlib; run it with `python3`), at V = 800,000 as in [the avenues post](../../posts/pq-gasper-avenues.md). The model is one slot: a subnet's votes get in if one aggregator that proves it is honest and reachable.
> - The attacker, and the spec's flood counts, are those of [aggregator-selection.md](aggregator-selection.md). Its [mitigation 1](aggregator-selection.md#mitigations) is the fallback named under "DoS resilience".
> - Flood counts for interleaved spans are the best attack a search finds, not proven minimums. Forty times more search lowers the floods by 2 % and raises the votes lost by less than one point. For cuts drawn at random, the dispersed assignment note guarantees at least 30, except for one draw in a billion.
> - How the backbone becomes the span (items 2 to 4 of the last section) is this note's reading of the proposal.
> - Spec references are to the consensus-specs `pq` branch @ `b73c695` (2026-11-26, still its head on 2026-11-27). [design.md](design.md) describes it at `ee867e9` and `4c29678`, and the attestation path has not changed since. Proving times are leanVM's benchmarks @ `be190e90a`. Anton's simulations are read at `e7b69b8` (2026-11-17).

# Interleaved Aggregation: 64 Subnets with Aggregators that Span Four

**Context.** The `pq` spec has [16 attestation subnets](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/p2p-interface.md#L48-L52) instead of 64. Each carries one committee of V/512 validators, and [4 aggregators](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/beacon-chain.md#L391-L395) prove that committee. That is 64 aggregators per slot and 4 proofs per vote.

**Main idea.** Keep 64 subnets, with a committee of about 400 on each, and keep the 64 aggregators. An aggregator proves 4 subnets instead of 1: the 4 that its node holds as backbone, assigned so that every committee is proven by 4 aggregators. The spans can be *aligned*, so that a committee's 4 aggregators prove the same 4 subnets, or *interleaved*, so that they prove it together with different subnets.

**Equal footing.** Both sides have 64 aggregators per slot, 1,563 signatures per proof and 4 proofs per vote, and a node relays 1/16 of all votes: 1 of 16 subnets, or 4 of 64. Only the layout differs.

**Verdict.** The merit is in interleaving the spans. Aligned spans are the spec on smaller topics, with the spec's numbers. Interleaved spans keep its tolerance per vote and lose fewer votes to an attacker that picks its targets, as long as it cannot take down all 64 aggregators of a slot. They cost aggregates that overlap.

| Per slot, at 800,000 validators | `pq` spec | Aligned spans | Interleaved spans |
|---|---:|---:|---:|
| Subnets, and votes on each | 16 × 1,563 | 64 × 391 | 64 × 391 |
| A node's subnets, and its share of all votes | 1 of 16 = 1/16 | 4 of 64 = 1/16 | 4 of 64 = 1/16 |
| Aggregators, and signatures per proof | 64 × 1,563 | 64 × 1,563 | 64 × 1,563 |
| Aggregators that prove a given vote | 4 | 4 | 4 |
| Faulty aggregators that can never lose a vote | any 3 | any 3 | any 3 |
| A vote has no honest aggregator, if a third are faulty | 1 in 81 | 1 in 81 | 1 in 81 |
| A slot loses 1/16 of its votes or more, if a third are faulty | 18 % of slots | 18 % | 2 % |
| Votes of a slot lost to 4 targeted faults | 1/16 | 1/16 | 1/64 |
| Votes of a slot lost to 16 targeted faults | 25 % | 25 % | 12 % |
| Aggregators to flood at once to halt finality | 24 | 24 | about 35 |
| Floods per epoch to halt finality, with 64 at once | 684 | 684 | 683 to 704 |
| Proofs sent when nothing fails | 16 | 16 | 16 |
| Proofs sent if a third are faulty | 16 | 16 | 24 |

The spec column takes 1 subnet per node, to compare at equal load. Its config has [2](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/configs/mainnet.yaml#L203-L204), which is 1/8 of all votes. A flood takes one aggregator's machine offline for the aggregation window.

## Merits

1. **Targeted faults lose less (interleaved).** 4 of them lose 1/64 of a slot's votes instead of 1/16, and 16 lose 12 % instead of 25 %. Halting finality takes about 35 aggregators down at once instead of 24.
2. **Losses come in smaller pieces (interleaved).** At a third faulty, a slot loses 1/16 of its votes or more in 2 % of slots instead of 18 %. The average loss is the same.
3. **Topics a quarter the size, for the same 64 proofs.** A subnet carries 391 votes per slot, as on mainnet today, where the spec's carry 1,563. Dedicated aggregators would take 256 proofs for that. Load then comes in steps of 1/64 of all votes: a node without validators could hold 2 of 64.
4. **No aggregator joins a subnet for its duty.** Its span is its backbone, so it collects over meshes it is always in. In the spec an aggregator joins its committee's subnet for 7 duties of 8, and needs a mesh there in time.
5. **A finer step for voluntary aggregation.** An aggregator that adds to its span adds a subnet of 391 votes at a time, where the spec's step is a committee of 1,563.

## Limits

1. **Nothing for random faults.** A vote is in 4 proofs, as in the spec, and no layout of 64 such proofs does better.
2. **Nothing against whole slots.** An attacker that takes down all 64 aggregators of a slot halts finality with about 700 floods per epoch, in every layout.
3. **Nothing if aligned.** Merits 1 and 2 need interleaved spans.

## Costs

1. **Aggregates overlap (interleaved).** Gossip has to compare an aggregate with all it has seen together, and a block needs a merge by union or several `Attestation`s for one slot.
2. **More proofs when aggregators fail (interleaved).** 19 instead of 16 if one of the first 16 fails, and 24 at a third faulty.
3. **Spans are assigned to validators.** Aggregators are then drawn per span, and a node's subscriptions show which spans its validators have.
4. **No simulation yet.** Nothing shows that an aggregator on 4 subnets of 64 has its votes by its cutoff.

## Counting

- **Proofs per vote = aggregators × subnets per proof ÷ subnets.** That is 64 × 1 ÷ 16 = 4 in the spec and 64 × 4 ÷ 64 = 4 here. A span adds no redundancy. It lets 64 aggregators serve 64 subnets.
- **The 4 subnets have to be assigned.** If each aggregator proved 4 subnets of its own choosing, 1.6 % of subnets would have no aggregator and 7 % a single one.
- **Aligned.** The 64 subnets form 16 fixed groups of 4, and each group has 4 aggregators. A group is one of the spec's committees, on 4 topics.
- **Interleaved.** The subnets are cut into 16 groups of 4 in four different ways, with one aggregator per group of each cut. A subnet has one aggregator from each cut, and they prove it together with different subnets.

## Honesty assumption

- **What has to hold.** One of the 4 aggregators that prove a vote is honest and online. That is the spec's assumption, in both layouts.
- **With what probability.** Aggregators are drawn by balance, so each is faulty with probability β, the faulty share of stake. A vote has no honest aggregator with probability β⁴: 1 in 10,000 at 10 % faulty, 1 in 625 at 20 %, and 1 in 81 at a third.
- **Read the other way.** For a vote to get in with probability 99 %, up to 31.6 % of aggregators may be faulty, which leaves about 44 honest of 64. For 99.99 % it is 10 %, or 58 of 64.
- **No layout does better.** With 4 proofs per vote on average, the fewest votes are lost when every vote has exactly 4, because β^r is convex in r. More tolerance to random faults takes more proving, not another layout.
- **What fails together.** At a third faulty, the spec and aligned spans lose 1/16 of a slot's votes in 18 % of slots. Interleaved spans lose votes in about half of the slots, one or two subnets of 1/64 each. The average is 1.2 % of the votes in all three.
- **Finality.** Stake that withholds its votes and its aggregates halts finality at 32.6 % in all three.

## DoS resilience

The attacker knows which machine runs each aggregator and floods the ones it picks for the aggregation window. Aggregators are public 32–64 slots ahead in the spec and here. The same counts hold for aggregators it corrupts.

- **Spec and aligned.** A committee's 4 aggregators prove the same votes, so 4 floods lose 1/16 of a slot.
- **Interleaved.** 4 floods still silence a subnet, but only that one: the other subnets that its aggregators prove keep 2 or 3 of their own. Losing 1/16 of a slot takes about 10 floods.

  | Aggregators flooded, of a slot's 64 | 4 | 16 | 32 | 48 | 64 |
  |---|---:|---:|---:|---:|---:|
  | Votes lost, spec and aligned | 6 % | 25 % | 50 % | 75 % | all |
  | Votes lost, interleaved | 1.6 % | 12 % | 30 % | 55 % | all |

- **Halting finality** takes a third of an epoch's votes, and the attacker has two ways to get them.
  - *Spread over all slots.* The spec falls to 24 floods at once (21 on average) and 684 per epoch. Interleaved spans take about 35 at once and about 1,100 per epoch.
  - *Whole slots.* Flooding all 64 aggregators of a slot silences it in any layout, and 11 silent slots of 32 halt finality: 704 floods per epoch. No layout with 4 proofs per vote falls to fewer than 683.
  - So interleaving raises what an attacker has to reach at once, from 24 aggregators to 35. It does not raise the number of floods for one that reaches 64. Only provers outside the slot's 64 would, such as a fallback open to every node on a subnet.
- **Never below the spec.** A flood takes an aggregator away from 4 subnets, and m subnets have 4m aggregator seats, so f floods empty at most f subnets. The spec's layout is on that bound at every fourth flood.
- **How the spans interleave matters.** If aggregator i proves subnets i to i + 3, emptying m subnets takes m + 3 floods, and halting finality 25 at once. The 35 is for cuts drawn at random. It is the best attack found, and such cuts take at least 30, except for one draw in a billion. Cuts along four directions of a 4 × 4 × 4 grid of subnets take exactly 37, and no two aggregators then share more than one subnet. The last two results are from the note on [dispersed aggregator assignment](https://github.com/yannvon/dc-networking/blob/546d9a55e668a863d1d514992b373ca22e31d447/research/pq-aggregation/dispersed-assignment/README.md#aggregators-on-a-few-whole-subnets), which studies these layouts for PQ-DC.
- **Floods at random.** If the attacker can flood only the aggregators it happens to find, the layouts are equal again. It has to hit 76 % of them to lose a third of the votes.

## Fewer aggregators?

- **Against a flooder with limited reach, yes.** 48 interleaved aggregators, 3 per vote, take 24 or 25 floods at once to halt finality. The spec's 64 take 24. With cuts along three directions of the grid, 48 take exactly 25, by the note on dispersed aggregator assignment.
- **Against one that silences whole slots, no.** A slot costs as many floods as it has aggregators: 48 instead of 64, and 528 per epoch instead of 704.
- **Against random faults, no.** 3 per vote lose 1 vote in 27 at a third faulty, not 1 in 81. Redundancy is proving work: to keep 4 per vote, 32 aggregators would each prove 8 subnets. That is 3,125 signatures and 1.6–2.8 s on leanVM's benchmark machines, against the 2.4 s the spec allows.

## What it assumes of PQ Gasper

1. **64 committees per slot, one per subnet.** [`MAX_COMMITTEES_PER_SLOT_PQ`](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/beacon-chain.md#L447-L451) goes back from 16 to 64, and `ATTESTATION_SUBNET_COUNT_PQ` goes. Committees are drawn as on mainnet today.
2. **A validator's backbone is its span.** Its node holds 4 assigned subnets for a long period, so `SUBNETS_PER_NODE` is 4. The subnets follow from the validator's index, where today they follow from the [node id](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/p2p-interface.md#L210-L227). A node holds the spans of all its validators. From about 54 validators (aligned) or 73 (interleaved) that is every subnet, as for the pool nodes in [Anton's simulations](https://github.com/Nashatyrev/jvm-libp2p/blob/e7b69b840addf76b19b361988744754ea919588c/pq-gasper.md).
3. **Aggregators are drawn per span, not per committee.** [`compute_aggregation_committee`](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/beacon-chain.md#L1067-L1096) samples a committee's members by balance. It would sample the validators that hold a span: 4 per group and slot if aligned, 1 per group of each cut if interleaved. An aggregator need not attest in the slot it aggregates. It signs at the slot's [aggregate leaf](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/beacon-chain.md#L1050-L1065), which every validator has. A validator aggregates every 391 epochs, as in the spec.
4. **The price of a fixed span is privacy.** A node's subscriptions show which spans its validators have. That narrows the search for a validator's node to the nodes on its span.
5. **An aggregate covers 4 committees.** Gossip [rejects](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/p2p-interface.md#L367-L370) anything but exactly one today. With aligned spans, the superset rule, the proposer's one aggregate per committee and its merge of 16 proofs then work per group.
6. **Interleaved spans need aggregates that overlap.**
   - The first cut's 16 aggregates tile the slot, so nothing overlaps while nothing fails. When one is missing, up to 4 aggregators of the next cut fill in: 19 proofs travel instead of 16, and 24 if a third are faulty.
   - An aggregator [stays silent](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/validator.md#L619-L650) if one received aggregate holds all its attesters. It would have to compare with all of them together.
   - A block has to hold aggregates that share committees. They can go into separate `Attestation`s, of which it [holds 16](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/beacon-chain.md#L469-L473). Or the merge proves a union, which leanVM [can do](https://github.com/leanEthereum/leanVM/blob/3d84ffc3c866d66f4c632848f8fc6f30a3350f76/doc/leanvm/body/10-ethereum.tex#L10) and [`stark_merge_proofs`](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/beacon-chain.md#L949-L957) does not ask for.
7. **Aggregators have the votes in time.** Anton's simulations have 16 subnets, and their aggregates come from pool nodes on every subnet. A run with 64 subnets and aggregators on 4 of them has to show it.
