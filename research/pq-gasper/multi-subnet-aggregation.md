---
title: PQ Gasper — multi-subnet aggregation
status: wip
date: 2026-11-27
provenance: agent
---

> **Provenance: agent.** Written 2026-11-27 by an agent as the front page of two notes on Yann's ideas, [interleaved-aggregation.md](interleaved-aggregation.md) and [voluntary-aggregation.md](voluntary-aggregation.md). Yann chose the names and has not reviewed the text line by line.
> - Every number is from those two notes and their scripts, at V = 800,000. The verdict is the agent's wording. Yann, 2026-11-27: "happy to have both on the same level".
> - Interleaved aggregation is the [dispersed aggregator assignment](https://github.com/yannvon/dc-networking/blob/546d9a55e668a863d1d514992b373ca22e31d447/research/pq-aggregation/README.md#1-dispersed-aggregator-assignment) of the PQ aggregation workstream, taken here for PQ Gasper alone. On 2026-11-27 that workstream is in `yannvon/dc-networking`, read at `546d9a5`, and not in `ethereum/dc-networking`, so the link goes there. The grid figure under the table is from its note.
> - Spec references are to the consensus-specs `pq` branch @ `b73c695` (2026-11-26, still its head on 2026-11-27).

# Multi-Subnet Aggregation

**Context.** In the `pq` spec an aggregate covers exactly one subnet. There are [16 subnets](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/p2p-interface.md#L48-L52) with one committee on each, [4 aggregators](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/beacon-chain.md#L391-L395) prove a committee, and gossip [rejects](https://github.com/ethereum/consensus-specs/blob/b73c6956b086e06b45158553f571106ef6c47eba/specs/_features/pq/p2p-interface.md#L367-L370) an aggregate that names any other number of committees. So a vote is in 4 proofs, and 4 faulty aggregators can lose 1/16 of a slot's votes.

**Main idea.** Let an aggregate cover more than one subnet. Two ideas follow from that, and neither needs the other.

- **Interleaved aggregation** keeps today's 64 subnets and the spec's 64 aggregators. Each aggregator proves 4 assigned subnets, and the 4 aggregators of a subnet prove it together with different subnets.
- **Voluntary aggregation** keeps the spec as it is and makes the assigned subnet a floor. An aggregator may add any other subnets of the slot whose votes its node holds. Nothing relies on it.

**Verdict.** The two do different things, and neither replaces the other.

- **Interleaved aggregation** changes the layout and adds no proving. Targeted faults lose less: 4 of them lose 1/64 of a slot's votes instead of 1/16. A vote still has no honest aggregator 1 time in 81 at a third faulty. It changes the subnets, the backbone and how aggregators are drawn.
- **Voluntary aggregation** keeps the layout and adds proving. If every aggregator adds one subnet, that 1 in 81 becomes 1 in 1,240, and the proving time doubles. It changes only what gossip and blocks accept.

Neither helps against an attacker that takes down all 64 aggregators of a slot.

| Per slot, at 800,000 validators | `pq` spec | Interleaved | Voluntary, all add one |
|---|---:|---:|---:|
| Subnets | 16 | 64 | 16 |
| What an aggregate covers | its subnet | 4 assigned subnets | its subnet and one more |
| Signatures per proof | 1,563 | 1,563 | 3,125 |
| Aggregators that prove a given vote | 4 | 4 | 8 on average |
| A vote has no honest aggregator, if a third are faulty | 1 in 81 | 1 in 81 | 1 in 1,240 |
| Floods to lose 1/16 of a slot's votes | 4 | about 10 | 5 |
| Aggregators to flood at once to halt finality | 24 | about 35 | 30 to 52 |
| Floods per epoch to halt finality, with 64 at once | about 700 | about 700 | about 700 |
| Aggregates sent, if a third are faulty | 16 | 24 | 15 |

A flood takes one aggregator's machine offline for the aggregation window. In the interleaved column, about 10 and about 35 are the best attacks found on spans cut at random. Spans cut along a grid take exactly 37 to halt finality. In the last column, 5 and 30 are for an attacker that knows what every aggregator adds, and 52 for one that cannot predict it.

## Where each one helps

- **Random faults.** Only voluntary aggregation. Interleaving moves the 4 proofs of a vote around, and 4 per vote is already the best that 64 proofs of this size can do.
- **Targeted faults.** Both. Interleaving does it by layout: 4 targeted faults lose 1/64 of a slot's votes instead of 1/16, whatever the aggregators do. Voluntary aggregation does it only as far as aggregators add.
- **Speed when aggregators fail.** Voluntary aggregation: at a third faulty, the first turn of aggregates proves 83 % of the votes instead of 67 %. Interleaving sends more proofs then, 24 where the spec sends 16.
- **Load.** Interleaving: topics a quarter the size for the same 64 proofs. Voluntary aggregation costs proving time, twice the duty for one added subnet.

## What both need

- **Aggregates that cover several committees.** Gossip rejects them today.
- **Aggregates that overlap.** Gossip has to compare them committee by committee, and a block needs a merge by union, which leanVM [can prove](https://github.com/leanEthereum/leanVM/blob/3d84ffc3c866d66f4c632848f8fc6f30a3350f76/doc/leanvm/body/10-ethereum.tex#L10).
- **Something else against whole slots.** With all 64 aggregators of a slot down, the slot is silent in both, and 11 silent slots of 32 halt finality.

## Together

- On 64 subnets a voluntary addition is a quarter of one of the spec's committees. If every aggregator adds 1 subnet, it proves 25 % more signatures and a vote is lost 1 in 160 times at a third faulty.
- With interleaved aggregation a node holds the spans of all its validators, so nodes with several validators have more to add.
