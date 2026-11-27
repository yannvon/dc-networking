---
title: PQ Gasper — voluntary aggregation: aggregators may prove more than their committee
status: wip
date: 2026-11-27
provenance: agent
---

> **Provenance: agent.** Written 2026-11-27 by an agent, on Yann's idea that an aggregator may add as many subnets to its duty as it wants. Yann has not reviewed it line by line.
> - This is one of two ideas under [multi-subnet aggregation](multi-subnet-aggregation.md), and the note takes it on its own, on the `pq` spec's layout. The other is [interleaved aggregation](interleaved-aggregation.md). Yann chose the names.
> - Numbers are from [`sim/voluntary_aggregation.py`](sim/voluntary_aggregation.py) (stdlib; run it with `python3`), at V = 800,000 as in [the avenues post](../../posts/pq-gasper-avenues.md). The model is one slot: a committee's votes get in if one aggregator that proved them is honest and reachable.
> - What an aggregator adds is its own choice. The note looks at three cases: one other committee, the committees on the node's 2 backbone subnets, and the whole slot.
> - The attacker, and the spec's flood counts, are those of [aggregator-selection.md](aggregator-selection.md).
> - Spec references are to the consensus-specs `pq` branch @ `b73c695` (2026-11-26, still its head on 2026-11-27), which [design.md](design.md) describes. Proving times are leanVM's benchmarks @ `be190e90a`, taken as linear in signatures. Anton's measurements are read at `e7b69b8` (2026-11-17), and EIP-8292 at `6889815`.

# Voluntary Aggregation: Aggregators May Prove More than Their Committee

**Context.** In the `pq` spec an aggregator proves exactly its committee. Gossip [rejects](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/p2p-interface.md#L367-L370) an aggregate that names any other number of committees, and takes [one aggregate](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/p2p-interface.md#L381-L386) per aggregator and epoch. A slot has 16 committees with [4 aggregators](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/beacon-chain.md#L391-L395) each, so a vote is in 4 proofs.

**Main idea.** The assigned committee becomes a floor. In the same aggregate, an aggregator may also prove any other committee of the slot whose votes its node holds. Nothing in the protocol relies on these additions.

**Baseline.** The `pq` spec as it is. Committees, subnets, the 64 aggregators per slot and the one aggregate each do not change.

**Verdict.** Worth having on its own. If every aggregator adds one committee, a vote is lost 1 in 1,240 times at a third faulty instead of 1 in 81, and the first turn of aggregates proves 83 % of the votes instead of 67 %. No message is added. It costs proving time, which doubles with one added committee, and aggregates that overlap, which need a merge by union. It leaves one thing as it is: with all 64 aggregators of a slot down, the slot is silent.

| Per slot, at 800,000 validators | `pq` spec | Half add one committee | All add one | All add their backbone |
|---|---:|---:|---:|---:|
| Signatures per proof | 1,563 | 1,563 or 3,125 | 3,125 | up to 4,688 |
| Proving time, of the 2.4 s the spec allows | 0.8–1.4 s | 0.8–2.8 s | 1.6–2.8 s | 2.3–4.2 s |
| Aggregators that prove a given vote, on average | 4 | 6 | 8 | 11.5 |
| A vote has no honest aggregator, if a third are faulty | 1 in 81 | 1 in 310 | 1 in 1,240 | 1 in 15,000 |
| Faulty share up to which 99.99 % of votes get in | 10 % | 15 % | 22 % | 35 % |
| Votes proven by the first turn, if a third are faulty | 67 % | 76 % | 83 % | 91 % |
| Floods to silence a committee, if the attacker knows the additions | 4 | 4 | 5 | 7 |
| Aggregators to flood at once to halt finality, if it knows them | 24 | 25 | 30 | 36 |
| The same, if it cannot predict them | 24 | 44 | 52 | — |
| Aggregates sent, if a third are faulty | 16 | 15 | 15 | 13 |
| Aggregates per slot, at most | 64 | 64 | 64 | 64 |

Proving times are for leanVM's four benchmark machines. A backbone is [2 subnets](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/configs/mainnet.yaml#L203-L204) and public, so the last column has no unpredictable case. A flood takes one aggregator's machine offline for the aggregation window.

## Merits

1. **A weaker honesty assumption, for the same messages.** If every aggregator adds one committee, a vote has 8 aggregators on average and is lost 1 in 1,240 times at a third faulty, instead of 1 in 81. With half of them it is 1 in 310.
2. **Votes are proven sooner when aggregators fail.** At a third faulty, the first turn of aggregates proves 83 % of the votes instead of 67 %, and the second 97 % instead of 89 %.
3. **Floods have to reach further.** Halting finality takes 24 aggregators down at once in the spec. With one added committee each it takes 30 if the attacker knows every addition, and 52 if it cannot predict them.
4. **Nothing is added to the network.** A slot still has at most 64 aggregates, and slightly fewer are sent when aggregators fail. A proof grows by 4 to 8 % when its signatures double, and a merged proof of 4,000 signatures verifies in 10 ms, as one of 2,000 does ([Anton's measurements](https://github.com/Nashatyrev/jvm-libp2p/blob/e7b69b840addf76b19b361988744754ea919588c/pq-gasper.md)). The votes an aggregator adds are votes its node receives anyway.
5. **A small change, on any layout.** An on-chain [`Attestation`](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/beacon-chain.md#L524-L531) already covers several committees, and proofs are [stated per committee](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/beacon-chain.md#L1425-L1457). Committees, subnets and the selection of aggregators stay. It works on the spec's 16 subnets as on 64.
6. **Those who can add have a reason to.** A large operator's node holds many subnets, and it has validators in every committee whose votes it wants on chain.

## Limits

1. **Proving time is the budget.** An added committee costs as much as the duty. One fits the spec's 2.4 s on three of leanVM's four benchmark machines, and two on one of them.
2. **An aggregator can add only what its node holds.** That is its 2 backbone subnets, 1.9 other committees on average. A node on every subnet can add any committee. The whole slot takes 12–23 s on one machine, or 1.4–2.7 s with 16 provers and a merge.
3. **It is not a guarantee.** The floor stays 1 honest aggregator of 4. Nothing may count on additions, so they are no reason to draw fewer aggregators.
4. **Nothing against whole slots.** Additions come from the slot's own 64 aggregators. An attacker that takes all of them down halts finality with about 700 floods per epoch, as in the spec.
5. **Public additions help less.** A backbone is public, so the attacker also floods whoever would add the committees it wants. That is 36 at once if all add their backbone.

## Costs

1. **Aggregates overlap.** Gossip has to compare aggregates committee by committee, and a block needs a merge by union. Without one, a slot's votes take as many `Attestation`s as the proposer picks aggregates that overlap, and a block holds 16.
2. **The floor can slip.** An aggregator sends one aggregate. If an addition makes its proof late, its own committee is late with it. It can prove its committee first and merge the addition if that is ready: a merge of two proofs takes 0.2–0.3 s in Anton's measurements. Or additions get an aggregate of their own, at one of the slot's three [unused leaves](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/beacon-chain.md#L414-L422).
3. **Memory.** It grows with the signatures: 8.7 GiB for 2,000 and 17.5 GiB for 4,000 in Anton's measurements.
4. **More of the chain's proofs come from large nodes.** They can add the most. A wide aggregate cannot push out a narrower one that holds a vote it lacks, as long as gossip and the proposer keep both.

## Honesty assumption

- **What has to hold.** One of a committee's 4 aggregators is honest and online, or one honest aggregator added the committee. The first is the spec's assumption and stays the guarantee.
- **With what probability.** Each aggregator is faulty with probability β, the faulty share of stake. Say a share s of the aggregators add, and an aggregator that adds proves a given other committee with probability r. A vote then has no honest aggregator with probability β⁴ · (1 − s · r · (1 − β))⁶⁰, since the other committees have 60 aggregators. r is 1/15 for one committee picked at random, 1/8 for a backbone and 1 for the whole slot.

  | Faulty share β | 10 % | 20 % | 1/3 | 1/2 |
  |---|---:|---:|---:|---:|
  | `pq` spec | 1 in 10,000 | 1 in 625 | 1 in 81 | 1 in 16 |
  | Half add one committee | 1 in 62,000 | 1 in 3,200 | 1 in 310 | 1 in 44 |
  | All add one | 1 in 410,000 | 1 in 17,000 | 1 in 1,240 | 1 in 122 |
  | All add their backbone | 1 in 13 million | 1 in 350,000 | 1 in 15,000 | 1 in 770 |
  | A quarter prove the whole slot | 1 in 44 billion | 1 in 410 million | 1 in 4.6 million | 1 in 48,000 |

- **Read the other way.** 99.99 % of votes get in with up to 10 % faulty aggregators in the spec, 22 % if all add one committee and 35 % if all add their backbone.
- **Sooner, too.** A committee's aggregators [take turns](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/validator.md#L595-L600) 0.6 s apart, and one stays silent if earlier turns prove all it has. At a third faulty:

  | Votes proven after the turn at | 7.2 s | 7.8 s | 8.4 s | 9.0 s |
  |---|---:|---:|---:|---:|
  | `pq` spec | 67 % | 89 % | 96.3 % | 98.8 % |
  | All add one committee | 83 % | 97 % | 99.5 % | 99.9 % |

## DoS resilience

The attacker knows which machine runs each aggregator and floods the ones it picks for the aggregation window.

- **Spec.** 4 floods silence a committee. Halting finality takes 171 of an epoch's 512 committees: 24 floods at once and 684 per epoch.
- **Additions it cannot predict.** It floods whole committees and hopes that nobody left standing adds them. If every aggregator adds one committee, the 4 floods that silence a committee in the spec do so 1 time in 60. To halt finality it has to flood 52 of a slot's 64 at once before too few are left to fill in, and 44 if half of them add one.
- **Additions it knows.** It also floods every aggregator that would prove a committee it wants. Silencing a committee then takes 5 floods if all add one committee and 7 if all add their backbone. Halting finality takes 30 at once, and 36.
- **Whole slots.** Flooding all 64 aggregators of a slot silences it whatever they add, and 11 silent slots of 32 halt finality: 704 floods per epoch. Only provers outside the slot's 64 would cost the attacker more.

## With interleaved aggregation

The two ideas do not need each other. Together, an addition is one of 64 subnets, a quarter of one of the spec's committees:

- If every aggregator adds 1 subnet, it proves 25 % more signatures and a vote is lost 1 in 160 times at a third faulty. With 2 subnets it is 1 in 310, and with 4, the size of a committee, 1 in 1,240.
- A node holds the spans of all its validators, so nodes with several validators have more to add.

## What it assumes of PQ Gasper

1. **An aggregate may cover several committees.** Gossip rejects anything but exactly one today. The aggregator's own committee has to be among them, and the [aggregator check](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/p2p-interface.md#L435-L438) stays on that one.
2. **One aggregate per aggregator, as today.** That rule and the leaf it signs at stay, so a slot has at most 64 aggregates.
3. **Aggregates are compared committee by committee.** The [superset rule](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/p2p-interface.md#L373-L379) and the [broadcast rule](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/validator.md#L619-L650) compare whole aggregates of one committee. They would ask, for each committee of an aggregate, whether the aggregates seen so far hold its attesters.
4. **Blocks merge by union.** The proposer [takes one aggregate per committee](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/validator.md#L322-L352), and [`stark_merge_proofs`](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/beacon-chain.md#L949-L957) proves the concatenation of its inputs' statements. Aggregates that overlap need the union, which leanVM [can prove](https://github.com/leanEthereum/leanVM/blob/3d84ffc3c866d66f4c632848f8fc6f30a3350f76/doc/leanvm/body/10-ethereum.tex#L10). Until then they go into separate `Attestation`s, of which a block [holds 16](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/beacon-chain.md#L469-L473).
5. **The floor is protected.** Either of the two ways under cost 2.
6. **Related.** The super-aggregator of [EIP-8292](https://github.com/ethereum/EIPs/blob/68898156500eea7389cf65d746b64c7dd27e4bc1/EIPS/eip-8292.md) is the whole-slot case without a floor.
