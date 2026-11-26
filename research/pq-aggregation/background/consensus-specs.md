---
title: Background — consensus-specs, for the broadcast properties
status: research notes
date: 2026-11-25
provenance: agent
---

> **Provenance: agent.** Written 2026-11-25 by a research subagent of the oversight thread of the [PQ aggregation strategy](../README.md) workstream, at Yann's request for background from consensus-specs, ethresear.ch and the Eth R&D Discord. Source: `ethereum/consensus-specs` (spec text, commit messages, issues, pull requests), plus `fradamt/consensus-specs`, branch `simplex-healing`. Yann has not reviewed it.
> - **Checked by the oversight thread:** 44 quoted fragments from 24 of the entries, against a clone for spec text and commit messages and through the GitHub API for issues and pull requests. All were found where cited. The rest is the subagent's reading, unchecked.
> - **"Bears on" is the subagent's judgement** of what a source means for our properties. Where the oversight thread reads it differently, the note below says so; [`README.md`](README.md) says what went into the properties.
> - **Note on entry 10** (nodes per subnet). The 400 to 500 nodes that the properties have from Yann match a 2025 statement in the Discord archive: 13,000 nodes on 2 of 64 subnets, plus aggregators and observers ([discord F19](eth-rnd-discord.md)). The 2023 measurement quoted here was taken with 4,200 nodes.

# Background from consensus-specs

**Revisions read**

| What | Revision |
|---|---|
| `ethereum/consensus-specs` `master` | `d2021d2719235f0df4726a1d330502cb15aa8ea3` |
| branch `pq` | `4c296784bb6ff54cbdcf72ebdda2a1057cce8893` (2026-11-21) |
| branch `decoupled-consensus` (EIP-8453) | `0f4fa3ffdd26ec083ff4dba65645d81433178413` (2026-11-02) |
| branch `pq-dc` | `bde2349e1e86763aed845e8a064cb22805628e0c` (2026-11-17) |
| PR 5856 head (EIP-8453 incentives) | `2455170c968a0f47e54263e334254997ee9007ec` |
| `fradamt/consensus-specs` `simplex-healing` | `5750e57bd5350468e65342a4657201b95cf321f2` (2026-07-27) |

**How to read this file**

- Every quote was read in the source at the link given. Spelling inside quotes is the source's.
- A sentence that starts with "Inference" is mine and is not in the source.
- "Bears on" names a property of [`aggregation-broadcast.md`](../../../properties/aggregation-broadcast.md) or [`attestation-broadcast.md`](../../../properties/attestation-broadcast.md).
- Links to spec files use `?plain=1` so that line anchors work.

**Contents:** [1. Why today's design looks the way it does](#1-why-todays-design-looks-the-way-it-does) · [2. What the protocol pays for, and by when](#2-what-the-protocol-pays-for-and-by-when) · [3. Later changes](#3-later-changes) · [4. The `pq` branch](#4-the-pq-branch-what-the-design-note-lacks) · [5. Decoupled-consensus specs](#5-decoupled-consensus-specs) · [6. Three lists](#6-three-lists)

---

## 1. Why today's design looks the way it does

### 1. The target of 16 aggregators was not derived from a fault bound

- **Source.** [Issue 2226](https://github.com/ethereum/consensus-specs/issues/2226), djrtwo, 2021-03-11, and his [closing comment](https://github.com/ethereum/consensus-specs/issues/2226#issuecomment-952312732), 2021-10-26.
- **Quote.** "`TARGET_AGGREGATORS_PER_COMMITTEE` was chosen to be 16 for phase 0 without too much thought. I'd like to at least consider reducing this to 8 in Altair to reduce the load on the global channel". Closing: "`16` was shown to be a safe choice in the context of sync committee aggregations ... The logic applies to this type of aggregation as well. Keeping `16`!"
- **Bears on.** Baseline; DoS resilience; Byzantine tolerance. **Sharpens.** The baseline's k = 16 is not a resilience target of its authors. Its one stated purpose is entry 2. The figures "352 aggregators per slot" and "0.002 %" are by-products of that choice.
- **Numbers.** 16 kept; 8 considered, to cut load on the aggregate topic.

### 2. The stated criterion for the target is the chance that a committee draws no aggregator

- **Source.** [Issue 1542](https://github.com/ethereum/consensus-specs/issues/1542#issuecomment-567542140), hwwhww, 2019-12-19. [PR 2514](https://github.com/ethereum/consensus-specs/pull/2514), djrtwo, 2021-07-12.
- **Quote.** "the probability of no aggregator with `TARGET_AGGREGATORS_PER_COMMITTEE=16` and `committee_size = 150` is about `2.12E-08`". PR 2514: "the current configuration of `TARGET_AGGREGATORS_PER_SYNC_SUBCOMMITTEE` as `4` had an unacceptably high probability of sync committee subnets not having aggregators ... the choice of `16` is the right tradeoff to generally have a high chance of having at least one aggregator per slot, even on a daily basis."
- **Bears on.** Baseline; the "missing aggregators" failure. **Sharpens.** A draw of exactly k removes this reason for a large k. The `pq` commit says so (already in the design note).
- **Numbers.** 2.12e-8 at n = 150. Raising the sync target from 4 to 16 "increases global messages for ~6%". Inference, my arithmetic from `is_aggregator`: at n = 390 the modulo is 24 and (23/24)^390 ≈ 6e-8; a sync subcommittee of 128 at target 4 gives (31/32)^128 ≈ 1.7 % per slot, and at target 16 gives (7/8)^128 ≈ 4e-8.

### 3. The selection proof exists to stop spam on the global topic; hiding the aggregator is not a stated purpose

- **Source.** [`phase0/p2p-interface.md` L2204–L2214](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/phase0/p2p-interface.md?plain=1#L2204-L2214). Added by [PR 1440](https://github.com/ethereum/consensus-specs/pull/1440), djrtwo, merged 2019-10-28.
- **Quote.** "The dominant strategy for an individual validator is to always broadcast an aggregate containing their own attestation to the global channel to ensure that proposers see their attestation for inclusion. Using a private selection criteria and providing this proof of selection alongside the gossiped aggregate ensures that this dominant strategy will not flood the global channel." And: "without some sort of proof of selection as an aggregator, the global channel can trivially be spammed."
- **Bears on.** Sybil resilience: **supports** (the senders must be few and provable). Incentive compatibility: **names a deviation our list lacks**, a validator that pushes its own vote onto the topic every proposer reads. DoS resilience, aggregators secret: **sharpens**. I found no statement, in the spec or the threads read, that the selection is private in order to protect aggregators. The secret regime is a side effect.

### 4. Aggregates are signed because an unsigned per-sender cap lets a neighbour displace the good aggregate

- **Source.** [Issue 1570](https://github.com/ethereum/consensus-specs/issues/1570), hwwhww, 2020-01-13. [Issue 1595](https://github.com/ethereum/consensus-specs/issues/1595), djrtwo, 2020-01-24. Fixed by [PR 1615](https://github.com/ethereum/consensus-specs/pull/1615), merged 2020-02-12. Spec: [`phase0/validator.md` L784–L786](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/phase0/validator.md?plain=1#L784-L786).
- **Quote.** Option 1: "we can just allow one `aggregate_and_proof` per aggregator per slot ..., but an attacker could forge the message with a much less optimal aggregate and try to block the original good aggregate from making it far in the gossip." Option 2: "only propagate an `aggregate_and_proo`f if it is _better_ (includes more validators) than any before seen for that aggregator at this slot ... still leaves open the aggregator themselves for semi DoS'ing by sending many aggregates sequentially from small to large". Chosen ([djrtwo, 2020-01-28](https://github.com/ethereum/consensus-specs/issues/1595#issuecomment-579481474)): "we don't enforce that the aggregator won't sign multiple via a slashing condition, but the condition (1) prevents the gossip channel from being DoS-able by the aggregator even if they sign multiple."
- **Also.** hwwhww's own fix, an aggregator that keeps its vote off the subnet, was rejected by [djrtwo](https://github.com/ethereum/consensus-specs/issues/1570#issuecomment-578343471): it "creates up to num_aggregator non-aggregatable messages per committee which would take up more attestation positions in each block ... and reduce the optionality in a block proposer including missing attestations from previous slots."
- **Bears on.** No displacement: **supports**, and is its first recorded instance. Sybil resilience: **sharpens**. The cap has to be per authenticated sender over the whole message, and "forward only if better" was rejected because one sender can send a ladder. Inference: the `pq` branch's balance rule (`2c5edd4`) was option 2 keyed by committee, and it was withdrawn a day later (`98814e4`).
- **Numbers.** Cost named: "an additional signature verification per message".

### 5. "One aggregate per aggregator and epoch" is per epoch only to shrink a cache

- **Source.** [PR 1706](https://github.com/ethereum/consensus-specs/pull/1706#issuecomment-609820527), djrtwo, 2020-04-06. [PR 1710](https://github.com/ethereum/consensus-specs/pull/1710), paulhauner, 2020-04-07. [Issue 1860](https://github.com/ethereum/consensus-specs/issues/1860#issuecomment-637662439), djrtwo, 2020-06-02. [PR 3257](https://github.com/ethereum/consensus-specs/pull/3257), arnetheduck, 2023-02-17. Rule today: [`phase0/p2p-interface.md` L731–L736](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/phase0/p2p-interface.md?plain=1#L731-L736).
- **Quote.** "we can expand this to be "per epoch" instead of "per slot" to safely reduce the size of the map from `V*32` bits to `V` bits." PR 1710: "don't allow a validator to aggregate twice in the same epoch." Issue 1860: "once a validator goes rogue, they can make an infinite number of valid-looking message for "free". To mitigate this DoS issue, there are validation conditions on the wire". PR 3257: "for those, we hope that validators are honest in signing only one but should they choose to sign more than one, they cannot be used to DoS the network."
- **Bears on.** Sybil resilience: **supports**, and states what the cap defends against: a signer who equivocates on messages that carry no slashing. **Contradicts a design in our space.** A validator that aggregates more than once per epoch (several slots, several layers, a merger role) is dropped by this key. The `pq` spec keeps the key.
- **Numbers.** V bits per epoch, 2V with the previous epoch kept. The rule was per slot in v0.11.0 and per epoch from v0.11.2.

### 6. The superset rule drops only what one seen aggregate covers, and names its own exception

- **Source.** [PR 2847](https://github.com/ethereum/consensus-specs/pull/2847), arnetheduck, 2022-03-03, merged 2022-05-17; [djrtwo's review](https://github.com/ethereum/consensus-specs/pull/2847#issuecomment-1062998935), 2022-03-09. Rule: [`phase0/p2p-interface.md` L724–L729](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/phase0/p2p-interface.md?plain=1#L724-L729).
- **Quote.** "it does not mandate dropping aggregates where a union of previous aggregates would cause it to become a subset". Premise: "any aggregate that has already been seen by a peer will also have been seen by its neighbours - a subset aggregate (strict or not) brings no new value to the aggregation algorithm, except in the extreme edge case where you could combine several such sparse aggregates into a single, more dense "combined" aggregate and thus use less block space." Cause of sparse aggregates: "an aggregator has not been able to include itself in the mesh and therefore publishes an aggregate with only its own attestations." djrtwo: "essentially dropping the message from gossip (which has amplificaiton factor) in favor of disseminating the unnecessary message through slower IWANT/IHAVE direct comms."
- **Bears on.** No displacement: **supports** (no vote is dropped that a seen aggregate lacks). Merge: **sharpens**. The "extreme edge case" of BLS, combining sparse aggregates to save block room, is the normal case under PQ, where a proposer takes one proof per committee or merges.
- **Numbers.** Teku after the change: "a small reduction in CPU usage" and "a slight decrease in outgoing bandwidth". The same rule was added for sync contributions.

### 7. Half of the aggregate topic was duplicates; deduplication worked "by accident" and nodes on the topic do not hold the same aggregates

- **Source.** [Issue 2155](https://github.com/ethereum/consensus-specs/issues/2155), blacktemplar, 2020-12-17. [Issue 2183](https://github.com/ethereum/consensus-specs/issues/2183), AgeManning, 2021-01-14 and [2021-11-29](https://github.com/ethereum/consensus-specs/issues/2183#issuecomment-981232838). [PR 2225](https://github.com/ethereum/consensus-specs/pull/2225), merged 2021-03-15.
- **Quote.** "over `50%` of the messages in the `beacon_aggregate_and_proof` topic get ignored because of that rule." A message ID taken from the aggregate alone fails because "an invalid message (invalid `aggregator_index` or invalid `selection_proof`) may have the same id as a valid message". AgeManning: "If the aggregates are identical, then we have about a 15x message redundancy." After PR 2225 removed the rule, clients "now fully propagate the redundant messages which appear to increase bandwidth and also increase CPU-time". [djrtwo](https://github.com/ethereum/consensus-specs/issues/2183#issuecomment-982135224): "the original mechanism did *not* work as we intended (strictly dropping dupes) and was short-circuited by IWANT/IHAVE. So it kind of worked in practice but by accident." [AgeManning](https://github.com/ethereum/consensus-specs/issues/2183#issuecomment-982173943): "some nodes on the network can receive different messages than others even though they are subscribed to the same topic. It turns out this doesn't seem to harm anything and costs us less resources."
- **Bears on.** Redundant work: **supports**, with a mainnet measurement. Fair to proposers: **sharpens**. "Every node is on the aggregate topic" does not mean every proposer holds the same aggregates. No displacement: today an aggregate that IGNORE stopped still arrives by IHAVE/IWANT. Inference: with proofs of about 200 KiB that second path is one pull per proof.
- **Numbers.** More than 50 % ignored; about 15×. I did not locate the pull request that restored the rule; the current text has it as the superset rule.

### 8. Staggering aggregators was raised in 2021 and judged too tight for BLS timing

- **Source.** [Issue 2183](https://github.com/ethereum/consensus-specs/issues/2183#issuecomment-981232838), AgeManning, 2021-11-29; [nisdas](https://github.com/ethereum/consensus-specs/issues/2183#issuecomment-981542380), same day.
- **Quote.** Option: "Set validators to not publish an aggregate if they have already seen an identical aggregate (may help a little, maybe even somehow order/randomize aggregator publishing time)". nisdas: "assuming all validators in the network are synced within 500ms of each other, packing in the aggregates and broadcasting them would take potentially 500ms - 1000ms. Relying on a node to receive an aggregate before broadcasting its own would have a limited impact on duplicates being propagated."
- **Bears on.** Redundant work; latency. **Sharpens.** The `pq` spec staggers by 600 ms. Inference: that step is inside the 500 to 1,000 ms nisdas gives for packing and broadcast alone, before a 200 KiB proof is received and verified, so how often a later aggregator can stay silent is open.

### 9. 64 subnets equal the committee count; more subnets cost more aggregates and need more nodes

- **Source.** [`phase0/p2p-interface.md` L2179–L2187](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/phase0/p2p-interface.md?plain=1#L2179-L2187). [Issue 3460](https://github.com/ethereum/consensus-specs/issues/3460), djrtwo, 2023-07-19.
- **Quote.** "The value is currently set to be equal to `MAX_COMMITTEES_PER_SLOT` if/until network tests indicate otherwise." Issue 3460, on splitting each committee over two subnets: "you'd still need to assign the same number of target aggregators per subnet (rather than per committee), so the total load on the global aggregate attestation subnet would be 2x. Given that attnets load increases linearly with size of validator set while aggregate subnet has remained stable, the trade-off to put more load on the aggregate subnet is likely acceptable." And: "without sufficient nodes on the network, you might either reduce the number of nodes per subnet to dangerous levels *or* you need to increase the attnets backbone subscription count ... If we had 10x the number of nodes on the network, I think such a strategy would be a no-brainer."
- **Bears on.** Model ("the number of subnets is not fixed"): **supports**. Attestation broadcast, "at a fixed N, a node's vote load does not depend on the subnet count": **supports**, the spec author states the same trade. **Lacks:** a floor on nodes per subnet. Inference: "2x on the aggregate topic" is acceptable for BLS and is the scarce resource under PQ.
- **Numbers.** 64 to 128 in the example; aggregate load 2×.

### 10. Nodes per subnet were measured at about 500 before nodes moved to 2 of 64; the same source expects under 200 after

- **Source.** [Issue 2749](https://github.com/ethereum/consensus-specs/issues/2749), djrtwo, 2021-11-29. [PR 3312](https://github.com/ethereum/consensus-specs/pull/3312), AgeManning, 2023-03-30, merged 2023-05-10. Spec: [`phase0/p2p-interface.md` L1807–L1848](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/phase0/p2p-interface.md?plain=1#L1807-L1848).
- **Quote.** Issue 2749, requirements of a backbone: "Subnets are relatively stable, slot-to-slot and epoch-to-epoch ... Subnets entry points can be found in a relatively short time (< 1 minute) ... (Nice to have) A method to discern whether a node is "honestly" performing the expected backbone duty". And: "This relies on an unenforcable "honesty" of validator nodes when the rational behavior is to turn your attnets down to 1 or even 0." PR 3312: "I measured 4.2k nodes on mainnet ... There are currently around 500 nodes per subnet ... This change (with `SUBNETS_PER_NODE` ==2 ) would reduce the density just under 200 nodes per subnet ... If we were to go with `SUBNETS_PER_NODE` ==1 there would be just under 100 nodes per subnet. I've opted for 2 just to be conservative."
- **Bears on.** Model, "nodes on a subnet ... today about 400 to 500 with default nodes on 2 of the 64 subnets": **contradicts on provenance**. In the source 500 is the count under the old rule (random subnets per attached validator, up to 64 per node), and the author expects under 200 under the new one. The baseline's secret-regime figures (398 of 400; 4,600 to 5,750 machines) scale with this number. **Lacks:** backing a subnet is unpaid, and was unenforceable.
- **Numbers.** 4.2k nodes; 45 % on no long-lived subnet; 7 % on all 64. Inference: P·j/S at P = 4,200 gives 131, so "just under 200" counts something more, and 400 to 500 at j = 2 needs 12,800 to 16,000 nodes.

### 11. The node-ID backbone has known costs: a public map, and node IDs ground to sit on one subnet

- **Source.** [PR 3312](https://github.com/ethereum/consensus-specs/pull/3312), body. [Issue 2749](https://github.com/ethereum/consensus-specs/issues/2749#issuecomment-982640288), Nashatyrev, 2021-11-30; [djrtwo's reply](https://github.com/ethereum/consensus-specs/issues/2749#issuecomment-982748680).
- **Quote.** "It is known in advance which node-ids will be subscribing to which subnets, which could lead to some additional forms of DOS vectors." "There could be sybil attacks by setting node-ids to specific values to hijack subnets". Nashatyrev: "An attack on a single subnet would require just 1/64 of malicious nodes than attacking the whole network." djrtwo: "the damage of eclipsing a small set of nodes wrt an attsetation subnet is likely limited -- a few validators might no get their individual attestations included. A targeted DOS could do the same thing with likely even fewer resources."
- **Bears on.** Network adversary: **names an adversary our model lacks**, one that joins a subnet with many nodes, holds no stake and silences nobody. Attestation broadcast, "Reliable". DoS resilience, aggregators secret: the nodes on a topic are computable from node IDs. Inference: the authors accepted the risk because the loss is "a few validators"; with fewer, larger subnets and 4 public aggregators the loss per subnet is larger.
- **Numbers.** 1/64 of the nodes. Downscoring nodes off their assigned subnets was left out of the merge.

### 12. Subnets show who validates; the aggregator is the attester that must subscribe

- **Source.** [`phase0/validator.md` L353–L359](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/phase0/validator.md?plain=1#L353-L359). [PR 1685](https://github.com/ethereum/consensus-specs/pull/1685), djrtwo, 2020-03-25, with [his reply to mkalinin](https://github.com/ethereum/consensus-specs/pull/1685#issuecomment-604547702). Issue 2749: [Nashatyrev](https://github.com/ethereum/consensus-specs/issues/2749#issuecomment-982723837), [djrtwo](https://github.com/ethereum/consensus-specs/issues/2749#issuecomment-982748680), [ajsutton](https://github.com/ethereum/consensus-specs/issues/2749#issuecomment-992013216).
- **Quote.** Spec: "If the validator is assigned to be an aggregator for the slot (see `is_aggregator()`), then subscribe to the topic." PR 1685: "Non-aggregators -- Only find sufficient peers on the attestation subnet (rather than subscribe) ... Reduces bandwidth requirement on the node, and keeps attnets small for quick propagation." mkalinin: "doesn't it increase a surface for eclipse attack?" djrtwo: "the mesh consists of the persistent committee _plus_ the aggregators for a range of slots (something like 5 to 20 slots worth of aggregators, assuming aggregators join some amount of slots in advance to prepare)". Nashatyrev: "currently it is even easy to estimate the number of validators per node with discovery `attSubnets` and `syncSubnets` attributes". djrtwo: "right! an incredible amount of information is leaked today." ajsutton: "if you're running 2048 validators or more then you're probably subscribed to every subnet to support your aggregation duties anyway".
- **Bears on.** DoS resilience, aggregators secret ("as long as nothing leaks"): **supports and sharpens**. A duty subscription is by design the mark of an aggregator, and aggregators are expected to join 5 to 20 slots early. Operators with 2,048 or more validators sit on every subnet, so joining shows nothing for them. "Anonymity enhancing": **supports**.
- **Numbers.** 5 to 20 slots; 2,048 validators.

### 13. Attest at 1/3 and aggregate at 2/3 arrived with the first aggregation design, without a derivation; the margins were measured later

- **Source.** [PR 1440](https://github.com/ethereum/consensus-specs/pull/1440), merge commit [`60a469b`](https://github.com/ethereum/consensus-specs/commit/60a469b9c71ec43a66270325aa35b695691d4ab0), 2019-10-28. [PR 3433](https://github.com/ethereum/consensus-specs/pull/3433), arnetheduck, 2023-06-15 (closed); [potuz](https://github.com/ethereum/consensus-specs/pull/3433#issuecomment-1593671399). [PR 3472](https://github.com/ethereum/consensus-specs/pull/3472), haxxpop, 2023-08-04; [arnetheduck](https://github.com/ethereum/consensus-specs/pull/3472#issuecomment-1666495519).
- **Quote.** The diff of PR 1440 changes "halfway through the `slot`" to "one-third of the way through the `slot`" and adds the aggregate "two-thirds of the way through the `slot`". PR 3433: "~95% of attestations are submitted within 2s of the broadcast cutoff and >99% of aggregates." potuz: "The way we handle aggregation requires us currently to have by default all attestations arriving 1.5 seconds before the aggregation". PR 3472: "Prysm aggregators currently aggregate only the attestations that arrive before 6.5 seconds in the slot rather than 8 seconds as specified in the spec". arnetheduck: "aggregating 512 attestations into a single aggregate takes <1ms ... validation takes ~1ms" and "we produce 20:ish mostly-the-same aggregates per committee and only one of them is actually needed to construct a block, iff it's good". [potuz](https://github.com/ethereum/consensus-specs/pull/3472#issuecomment-1666447218): "it's more important to broadcast early than to gather attestations longer".
- **Bears on.** Timely vote: **sharpens**. The cutoff is a client's choice ahead of the publishing time, 1.5 s in one client with BLS. Latency; the baseline row "making an aggregate takes no proof".
- **Numbers.** One Nimbus node's histogram: 327.9 M of 348.9 M attestations received by 6 s (94 %); 23.32 M of 23.48 M aggregates by 10 s (99.3 %), 72,015 by 8 s. "a validator assigned to aggregation duties must today aggregate ~350". Gloas moves the deadlines to 25 % and 50 % of the slot.

### 14. Two failure modes that are neither random nor adversarial: voters who vote late, and aggregators that share a client

- **Source.** [PR 3433](https://github.com/ethereum/consensus-specs/pull/3433#issuecomment-1831732129), casparschwa, 2023-11-29. [Issue 2226](https://github.com/ethereum/consensus-specs/issues/2226#issuecomment-796418161), potuz, 2021-03-11.
- **Quote.** casparschwa: "An attestor wants to get their head vote correct ... They can achieve this by delaying their attestation slightly (while making sure they propagate it in time for aggregation - timing games all over)." potuz: "Currently some clients drop attestations that are received before the block to which they are attesting ... If all the aggregators in the committee are from these clients, the attestation is likely to be missing."
- **Bears on.** Incentive compatibility and "Fair vote timing": **names a rational deviation by voters**, not aggregators. Inference: a public, staggered cutoff tells a voter how late it can be. "Failures at random are the mild case": **sharpens**. Failures correlate by client software; the model has machines and not clients.

---

## 2. What the protocol pays for, and by when

### 15. Nothing pays for aggregating; the proposer is paid, and only for flags not yet set

- **Source.** [`altair/beacon-chain.md` L139–L146](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/altair/beacon-chain.md?plain=1#L139-L146) and [L593–L607](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/altair/beacon-chain.md?plain=1#L593-L607). [`phase0/validator.md` L530–L537](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/phase0/validator.md?plain=1#L530-L537).
- **Quote.** `if flag_index in participation_flag_indices and not has_flag(epoch_participation[index], flag_index): ... proposer_reward_numerator += get_base_reward(state, index) * weight`. Validator guide: "To maximize profit, the validator should attempt to gather aggregate attestations that include singular attestations from the largest number of validators whose signatures from the same epoch have not previously been added on chain."
- **Bears on.** Incentive compatibility: **supports** the baseline row, and **sharpens** it. The party paid for coverage is the proposer, and a vote already on chain pays nothing again, so uncovered votes are worth the most to the next proposer.
- **Numbers.** Weights of 64: source 14, target 26, head 14, sync 2, proposer 8.

### 16. Payment deadlines differ by part of the vote: head one slot, source 5 slots, target until the end of the next epoch

- **Source.** [`altair/beacon-chain.md` L446–L451](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/altair/beacon-chain.md?plain=1#L446-L451). [`deneb/beacon-chain.md` L350–L356](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/deneb/beacon-chain.md?plain=1#L350-L356). [PR 2140](https://github.com/ethereum/consensus-specs/pull/2140), vbuterin, 2020-11-28. [PR 3360](https://github.com/ethereum/consensus-specs/pull/3360#issuecomment-1593014581) (EIP-7045), djrtwo, 2023-06-15.
- **Quote.** vbuterin: "the "coarsening" of the inclusion delay reward from the original 1/n rule to a "very timely / timely / not timely" triad". djrtwo: "We want validators to be rewarded for correct FFG vote no matter when it makes it on chain -- so anytime in the maximum range. Source correctness reward "splits the difference" between the timeliness of head and the timeliness of target".
- **Bears on.** Delivered, level 1: **sharpens** the Gasper baseline. 14/64 of a vote's reward needs the next block, 14/64 needs 5 slots, 26/64 has up to two epochs. Recoverable: **supports**. The finality part was made deadline-free on purpose.
- **Numbers.** `inclusion_delay == 1`; `<= integer_squareroot(SLOTS_PER_EPOCH)` = 5; target 32 slots in Altair, any slot of epochs N and N+1 from Deneb.

### 17. Today's stack has a fallback: proposers are "the aggregators of last resort"; there are no late aggregators

- **Source.** [PR 3360](https://github.com/ethereum/consensus-specs/pull/3360#issuecomment-1593172503), arnetheduck, 2023-06-15; [djrtwo](https://github.com/ethereum/consensus-specs/pull/3360#issuecomment-1596206970), 2023-06-18. [PR 3552](https://github.com/ethereum/consensus-specs/pull/3552#discussion_r1402925514), etan-status, 2023-11-23.
- **Quote.** arnetheduck: "are there designated aggregators listening on the right subnet that can pick up these attestations when they come late?" djrtwo: "Proposers are already and would continue to be the aggregators of last resort for late or non-previously-picked-up attestations. This is clearly imperfect due to a given stretch of proposers not having perfect coverage off attestation subnets, but 7045 is a *strict* improvement by giving both more time and more potential proposers to pick up missing attestations." etan-status: "The block proposer is not necessarily subscribed to all individual attestation subnets."
- **Bears on.** Recoverable, fallback: **contradicts the baseline table by omission**. The table has no fallback row, and its DoS and censorship rows count only the 16 aggregators. With BLS any proposer aggregates the raw votes its node holds, for free. Its reach is the subnets that proposer's node is on. Under PQ the same fallback needs the raw signatures and a proof.

### 18. A longer inclusion window brought replayed aggregates

- **Source.** [PR 3627](https://github.com/ethereum/consensus-specs/pull/3627), arnetheduck, 2024-03-19, merged 2024-03-29.
- **Quote.** EIP-7045 "effectively extends the valid lifetime of an attestation/aggregate to 2 epochs ... peers are allowed to republish old aggregates and attestations and libp2p will not stop the spread with the settings we recommend ... Significant amounts of this kind of spam have been observed on the aggregate channel in particular leading to a 5x increase in aggregate traffic as some clients republish these old messages in spite of the "attestation cover rule"".
- **Bears on.** Recoverable, "it pulls against Sybil resilience": **supports**, with an observed case. **Lacks:** the deduplication caches have to live as long as a vote stays includable.
- **Numbers.** 5× aggregate traffic; `seen_ttl` raised to two epochs.

---

## 3. Later changes

### 19. EIP-7549 took the committee index out of the signed data; aggregates on the wire still cover exactly one committee

- **Source.** [PR 3559](https://github.com/ethereum/consensus-specs/pull/3559), dapplion, 2023-12-05; [hwwhww](https://github.com/ethereum/consensus-specs/pull/3559#issuecomment-1842262460). [`electra/validator.md` L114–L119](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/electra/validator.md?plain=1#L114-L119). [`electra/p2p-interface.md` L253–L256](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/electra/p2p-interface.md?plain=1#L253-L256).
- **Quote.** "Signing over the 3rd item causes tuples of equal votes to produce different signing roots. If the committee index is moved outside of the Attestation message the minimum number of attestations to verify to reach a 2/3 threshold is reduced to ceil(32 * 2/3) = 22 (a factor of 62)." hwwhww: "it was a flawed design in phase0." Spec: aggregates "with disjoint `committee_bits` sets and equal `AttestationData` SHOULD be consolidated into a single `Attestation` object." Gossip: "[REJECT] Exactly one committee is specified by the committee bits".
- **Bears on.** "Encoding independent of the topology": **supports**, with the precedent and its reason. Merge: today's last merge is the proposer's and is free. **Contradicts a design in our space under current rules:** an aggregate over several committees is rejected on this topic, in Electra and in the `pq` spec.
- **Numbers.** 1,366 to 22 aggregates for a 2/3 quorum; `MAX_ATTESTATIONS` 128 to 8.

### 20. `SingleAttestation`: the check that ties a message to a staked signer comes before any costly work

- **Source.** [PR 3900](https://github.com/ethereum/consensus-specs/pull/3900), arnetheduck, 2024-08-26; his comments of [2024-08-28](https://github.com/ethereum/consensus-specs/pull/3900#issuecomment-2314336922) and [2024-10-18](https://github.com/ethereum/consensus-specs/pull/3900#issuecomment-2421977222); [dapplion](https://github.com/ethereum/consensus-specs/pull/3900#issuecomment-2433764523), 2024-10-23.
- **Quote.** "placing the validator index directly in the attestation allows verifying the signature without computing a shuffling - this closes a loophole where clients either must drop attestations or risk being overwhelmed by shuffling computations". "with this change we can do so _after_ signature verification meaning that only validators can create new shufflings." "The aggregate topic uses an envelope that is already signed by a validator - it does not offer the opportunity of DoS by a non-validator as the attestation topic does". dapplion: "So we'll have attributability in case of an attack."
- **Bears on.** Sybil resilience and "Bounded spam": **sharpens** "cheap checks before the proof check" into an order: authenticate the signer first, then do work that depends on state, then the proof. **Lacks:** attributability.

### 21. Sync committee contributions: why aggregate at all, why a global topic, and a loss unit

- **Source.** [PR 2201](https://github.com/ethereum/consensus-specs/pull/2201#issuecomment-781641172), ralexstokes, 2021-02-18; djrtwo's review comments of [2021-03-03](https://github.com/ethereum/consensus-specs/pull/2201#discussion_r586714535) and [2021-03-04](https://github.com/ethereum/consensus-specs/pull/2201#discussion_r586926086). [`altair/validator.md` L463–L464](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/altair/validator.md?plain=1#L463-L464).
- **Quote.** "the unaggregated version introduces an extra ~100kB per slot for _all_ validators (as any individual validator would need to be listening to this channel all the time given the minimal amount of lookahead on the proposer shuffling)". djrtwo: "you do get redundancy because there are sub-committees so if even 2 fail, you still get 75% of the committee through aggregates". djrtwo: "By default, all *potential* proposers (thus all validators today) should just listen to this channel. It's a bit wasteful on bandwidth and verification". Spec: "The set of aggregators generally changes every slot; however, the assignments can be computed ahead of time as soon as the committee is known."
- **Bears on.** Fair to proposers: **sharpens**. The stated reason every node joins the aggregate topic is that the next proposers are not known early enough. Inference: with proposers known ahead, a topic that only the next proposers join becomes possible. Loss unit: **supports**. DoS, aggregators secret: the holder of a "private" role knows it early.
- **Numbers.** About 100 kB per slot; 4 subnets of 128; target 16 per subcommittee; one contribution per (slot, aggregator, subcommittee).

### 22. Gloas payload attestations: a 512-member vote with no aggregators, aggregated by the proposer

- **Source.** [`gloas/validator.md` L232–L246](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/gloas/validator.md?plain=1#L232-L246). [`gloas/p2p-interface.md` L927–L990](https://github.com/ethereum/consensus-specs/blob/d2021d2719235f0df4726a1d330502cb15aa8ea3/specs/gloas/p2p-interface.md?plain=1#L927-L990).
- **Quote.** "Listen to the `payload_attestation_message` gossip global topic." "The proposer MUST aggregate all payload attestations with the same data into a given `PayloadAttestation` object." Gossip: "[IGNORE] This is the first valid payload attestation from this validator index" and "[REJECT] The validator is a member of the payload timeliness committee".
- **Bears on.** Recoverable, "the last level as a public fallback": a precedent in the spec where the proposer is the only aggregator and the sender set is the committee itself.
- **Numbers.** `PTC_SIZE` 512; `MAX_PAYLOAD_ATTESTATIONS` 4; deadline 75 % of the slot.

---

## 4. The `pq` branch: what the design note lacks

Checked against [`research/pq-gasper/design.md`](../../../research/pq-gasper/design.md). Only reasons, notes and commit rationale that it does not have.

### 23. Why the aggregators are staggered, and why a covered aggregator stays silent

- **Source.** Commit [`4595f0f`](https://github.com/ethereum/consensus-specs/commit/4595f0fc9be7e3611f0187a2ff5fee00e120f751), Justin Traglia, 2026-11-19. Table: [`pq/validator.md` L579–L602](https://github.com/ethereum/consensus-specs/blob/4c296784bb6ff54cbdcf72ebdda2a1057cce8893/specs/_features/pq/validator.md?plain=1#L579-L602).
- **Quote.** "This gives every aggregator the same time to build its proof and lets later aggregators include late attestations." "Aggregates are large and costly to verify, so this avoids sending ones that would not be propagated anyway."
- **Bears on.** Redundant work: **supports**, and gives the author's reason (verification cost and size, not bandwidth alone). Timely vote: **sharpens**. There are four cutoffs per subnet, not one.
- **Numbers.** Per position 0 to 3: collects for 1.8, 2.4, 3.0, 3.6 s; proves for 2.4 s each; "Until proposal" 16.8, 16.2, 15.6, 15.0 s.

### 24. A later aggregator compares against each received aggregate on its own, never against their union

- **Source.** [`pq/validator.md` L648–L650](https://github.com/ethereum/consensus-specs/blob/4c296784bb6ff54cbdcf72ebdda2a1057cce8893/specs/_features/pq/validator.md?plain=1#L648-L650).
- **Quote.** "Each received aggregate is compared on its own, not together with the others. A proposer can include only one aggregate per committee, so two aggregates that together cover the aggregator's attesters do not make its aggregate redundant."
- **Bears on.** No displacement: **supports**. Redundant work: **contradicts** one sentence of ours, that under a dispersed assignment a later aggregator "can stay silent only when several earlier proofs together" cover its set. The spec's stated reason forbids exactly that, as long as the proposer cannot union overlapping proofs.

### 25. The two-slot inclusion delay is there to give the proposer a slot for receiving and merging

- **Source.** Commit [`ec4e216`](https://github.com/ethereum/consensus-specs/commit/ec4e21652fa20d50808bf264a8f09d1447d2f13e), 2026-11-18. Commit [`2f42da8`](https://github.com/ethereum/consensus-specs/commit/2f42da884bb2e8c08d5a1b188ee1799ee2030517), same day.
- **Quote.** "gives the proposer an extra slot to receive aggregates and merge their proofs into the block's proof. Aggregators keep the same deadline, so fork choice sees votes as early as before. The timely head flag now requires an inclusion delay of exactly two slots, so a timely attestation no longer always votes for the parent block." And: "With a two-slot inclusion delay, full participation only justifies on the last slot of a minimal epoch".
- **Bears on.** Latency; Delivered, levels 1 and 2. **Sharpens.** The author separates the two levels: nodes get the aggregate at the old deadline for fork choice, and the proposer gets one more slot. The cost is later justification.
- **Numbers.** `MIN_ATTESTATION_INCLUSION_DELAY_PQ = 2`; the proposer has until 24 s after the start of the votes' slot.

### 26. With several provers per committee, aggregates "overlap heavily but rarely cover one another"

- **Source.** Commit [`2c5edd4`](https://github.com/ethereum/consensus-specs/commit/2c5edd4ae4983de4d2ea474e035aece5d7e3bb9f), 2026-11-17. Commit [`98814e4`](https://github.com/ethereum/consensus-specs/commit/98814e4beefd2578de7e95ac1fed355e69df43a2), 2026-11-18.
- **Quote.** "Each committee now has several aggregators building from the same subnet, so their aggregates overlap heavily but rarely cover one another, and nearly all of them reached every node." "Attesting balance rather than attester count is used because fork choice weight and rewards scale with effective balance." The withdrawal: "so every aggregate that adds a vote is still propagated."
- **Bears on.** Redundant work: **sharpens**. The superset rule saves bytes only when aggregates are equal or nested. [nisdas](https://github.com/ethereum/consensus-specs/issues/2749#issuecomment-983212092) asked the same in 2021: "would this change lead to more disjoint aggregates, and along with that a higher CPU load for the entire network as now more individual aggregates have to be verified?" No displacement: **supports**. The author gave up the saving to keep it.

### 27. An open issue says the proofs do not bind the leaf index that the spec's statement names

- **Source.** [Issue 5829](https://github.com/ethereum/consensus-specs/issues/5829), rahulbarmann, 2026-11-14 (title only read). [Issue 5840](https://github.com/ethereum/consensus-specs/issues/5840), ethDreamer, 2026-11-18, both open.
- **Quote.** "leanVM ... currently produces proofs that attest only `(pubkey, message)` pairs." "Aggregate proofs are the only verification of attestation signatures in: `process_stark` over `body.proof` at block import; `beacon_aggregate_and_proof` gossip validation; `is_valid_indexed_attestation`". "The attacker, acting as an aggregator for that committee or as a block proposer (or colluding with one), includes the forged signature in an aggregate proof."
- **Bears on.** Integrity ("it rests on the signature scheme and the proof system"): **names a precondition**. The proof's statement has to bind the leaf, or one reused leaf of a key breaks integrity through an aggregator. The issue's author has "not assessed how practical the forgery" is.

### 28. Smaller points, and one absence

- **Source.** Commits [`e26cc6f`](https://github.com/ethereum/consensus-specs/commit/e26cc6fe90416184d3f4369cbc49e13ebe9ad411), [`af898d0`](https://github.com/ethereum/consensus-specs/commit/af898d07b6a2a4d56e7ae896c171225a622813a4), [`bde2349`](https://github.com/ethereum/consensus-specs/commit/bde2349e1e86763aed845e8a064cb22805628e0c) (`pq-dc`).
- **Quote.** `e26cc6f`: the window is cached "so the selection does not change when effective balances are updated at an epoch boundary", and "aggregate gossip validation advances a head state that is more than one epoch behind so that the aggregators are in its window." `af898d0`: "Testing aggregation with large committees otherwise needs a devnet large enough to fill them." `bde2349`: attestations "carry an unsigned `round` in place of `epoch`, since a validator attests once per round and each attestation needs its own XMSS leaf."
- **Bears on.** CPU load: checking who may send can cost a state advance. Bounded spam under PQ: one vote per round is also one leaf per round.
- **Absence.** The `pq` files at `4c29678` have no note or TODO on denial of service against the public aggregators, on censoring or withholding aggregators, or on privacy. I searched `validator.md`, `p2p-interface.md` and `fork-choice.md` for those words.

---

## 5. Decoupled-consensus specs

### 29. `ethereum/consensus-specs` has an EIP-8453 networking spec; aggregator selection and both aggregate topics are TODOs

[`specs/README.md`](../../../specs/README.md) says "The DC networking spec itself is still to come". This branch has a first one since 2026-10-26.

- **Source.** Branch `decoupled-consensus`: [`eip8453/p2p-interface.md` L259–L274](https://github.com/ethereum/consensus-specs/blob/0f4fa3ffdd26ec083ff4dba65645d81433178413/specs/_features/eip8453/p2p-interface.md?plain=1#L259-L274) and [L461–L482](https://github.com/ethereum/consensus-specs/blob/0f4fa3ffdd26ec083ff4dba65645d81433178413/specs/_features/eip8453/p2p-interface.md?plain=1#L461-L482); [`eip8453/validator.md` L465–L477](https://github.com/ethereum/consensus-specs/blob/0f4fa3ffdd26ec083ff4dba65645d81433178413/specs/_features/eip8453/validator.md?plain=1#L465-L477) and [L578–L589](https://github.com/ethereum/consensus-specs/blob/0f4fa3ffdd26ec083ff4dba65645d81433178413/specs/_features/eip8453/validator.md?plain=1#L578-L589). Authors of the commits: Justin Traglia, terence, Mikhail Kalinin.
- **Quote.** "the `beacon_aggregate_and_proof` and `beacon_attestation_{subnet_id}` topics are deprecated, and the `head_vote` and `attestation_{subnet_id}` topics are new". "FG attestations carry neither a slot nor a block root. Each validator may propagate one attestation per round, in the slot of its attestation committee." "*TODO*: Specify aggregator selection for head votes and FG attestations. The legacy aggregation helpers require adaptation to EIP-8453 committees." "*TODO*: Specify aggregate gossip messages, selection-proof wrappers and broadcast deadlines. Gossip deduplication must use the data and signers, since the epoch is not signed."
- **Bears on.** The whole aggregation stage is unspecified there, so nothing in our list is contradicted by it yet. **States one requirement our list lacks:** deduplication keyed by data and signers. Delivered, level 2: **supports** "these attestations do not play into fork choice" for this spec, since FG votes carry no block root. Entry 33 differs.

### 30. EIP-8453 parameters: 256 committees per slot on 64 subnets, and aggregates that span committees

- **Source.** [`eip8453/beacon-chain.md` L148–L155](https://github.com/ethereum/consensus-specs/blob/0f4fa3ffdd26ec083ff4dba65645d81433178413/specs/_features/eip8453/beacon-chain.md?plain=1#L148-L155), [L400–L404](https://github.com/ethereum/consensus-specs/blob/0f4fa3ffdd26ec083ff4dba65645d81433178413/specs/_features/eip8453/beacon-chain.md?plain=1#L400-L404), [L1700–L1701](https://github.com/ethereum/consensus-specs/blob/0f4fa3ffdd26ec083ff4dba65645d81433178413/specs/_features/eip8453/beacon-chain.md?plain=1#L1700-L1701). [`eip8453/validator.md` L205–L215](https://github.com/ethereum/consensus-specs/blob/0f4fa3ffdd26ec083ff4dba65645d81433178413/specs/_features/eip8453/validator.md?plain=1#L205-L215) and [L510–L514](https://github.com/ethereum/consensus-specs/blob/0f4fa3ffdd26ec083ff4dba65645d81433178413/specs/_features/eip8453/validator.md?plain=1#L510-L514).
- **Quote.** "Aggregates combine the attestations of several committees." "Attestations cast in different rounds of the same epoch can be aggregated together." "A proposer should prefer aggregates that add target, progress or pending-finality participation." Inclusion: `assert attestation.epoch <= get_current_epoch(state)` and `assert attestation.epoch >= compute_epoch_at_slot(state.finalized_slot)`.
- **Bears on.** Model, coverage set d: **supports** an aggregator that covers several committees, as the spec's stated direction. "Uses the whole round" and late inclusion: **extends**. An FG vote stays includable from the finalized epoch to the current one, which is longer than a round.
- **Numbers.** `SLOTS_PER_ROUND` 8; `ATTESTATION_COMMITTEES_PER_ROUND` 2,048, so 256 per slot; `MAX_VALIDATORS_PER_AGGREGATE` 131,072, counted over all members of the committees an aggregate names; `HEAD_VOTE_COMMITTEE_SIZE` 1,024; `MAX_HEAD_VOTES` 8; subnet = `committee_index % ATTESTATION_SUBNET_COUNT`. Inference: at 800,000 validators that is about 390 per committee, 100,000 voters per slot and 1,560 per subnet per slot.

### 31. Proposed EIP-8453 incentives: full pay for inclusion in the next slot, zero after 16 slots, and the first proposer is penalised too

- **Source.** [PR 5856](https://github.com/ethereum/consensus-specs/pull/5856), anderselowsson, opened 2026-11-23, open, base `decoupled-consensus`. Text read in the diff at head `2455170`.
- **Quote.** "An attester can earn up to `FG_ATTESTER_WEIGHT / WEIGHT_DENOMINATOR` of its base reward per duty when its attestation is included promptly, in the slot after its voting slot." "The payments to the attester and the including proposer decay with each slot of delay and reach zero after `FG_REWARD_WINDOW` slots. At the end of the first inclusion slot, the attester and the proposer assigned to that slot each pay a fixed penalty per duty." "A later proposer can still include the vote for payment even if the height advances or the checkpoint finalizes." On gossip: "If an omitted vote is held as a `SingleAttestation`, it can be relayed here in a one-signer aggregate using the original committee epoch."
- **Bears on.** Delivered, level 1: **contradicts** "until the round ends" as the only deadline. Under this proposal the deadline that pays is one slot, and the window is 16 slots, two rounds. Incentive compatibility: **extends**. Still no pay for aggregating, and the first proposer bears the aggregators' failure. Recoverable: **supports**, with a relay path for single late votes. It also differs from [`design/incentives.md`](../../../design/incentives.md) as our file summarises it.
- **Numbers.** `FG_ATTESTER_WEIGHT` 24, `FG_PROPOSER_WEIGHT` 3, `HEAD_VOTE_WEIGHT` 4, of 64; `FG_REWARD_WINDOW` 16. At d slots late the attester keeps (7/8)·(23/24)^(d−1), tapered. The pull request is open and may change.

### 32. Equivocation evidence has to travel: gossip must forward a second, different vote from the same validator

- **Source.** [PR 5863](https://github.com/ethereum/consensus-specs/pull/5863), spiral-ladder, opened 2026-11-24, open. Simplex: [`simplex/p2p-interface.md` L100–L106](https://github.com/fradamt/consensus-specs/blob/5750e57bd5350468e65342a4657201b95cf321f2/specs/_features/simplex/p2p-interface.md?plain=1#L100-L106) and [L741–L746](https://github.com/fradamt/consensus-specs/blob/5750e57bd5350468e65342a4657201b95cf321f2/specs/_features/simplex/p2p-interface.md?plain=1#L741-L746), fradamt.
- **Quote.** PR 5863: "dropping the second vote on gossip prevented nodes from detecting head-vote equivocations over P2P." Simplex: "The first distinct valid message for a validator in a round is forwarded. One second distinct message is also forwarded and marks the validator as a known round equivocator; this is necessary to exclude that signer from TSQ support and SG grades. Further distinct copies add no synchronization information."
- **Bears on.** Attestation broadcast, "Bounded spam ... one per target epoch and validator": **contradicts** it for decoupled consensus. The bound these specs want is two per validator and round. **Lacks:** delivery of equivocation evidence as a property.
- **Numbers.** 2 per (slot, validator) for head votes; 2 per (round, validator) for finality attestations in Simplex.

### 33. In the Simplex pyspec, finality attestations feed fork choice on receipt, with a freeze at the end of each round

- **Source.** [`simplex/p2p-interface.md` L42–L46](https://github.com/fradamt/consensus-specs/blob/5750e57bd5350468e65342a4657201b95cf321f2/specs/_features/simplex/p2p-interface.md?plain=1#L42-L46), [L49–L56](https://github.com/fradamt/consensus-specs/blob/5750e57bd5350468e65342a4657201b95cf321f2/specs/_features/simplex/p2p-interface.md?plain=1#L49-L56), [L84–L88](https://github.com/fradamt/consensus-specs/blob/5750e57bd5350468e65342a4657201b95cf321f2/specs/_features/simplex/p2p-interface.md?plain=1#L84-L88), [L402–L408](https://github.com/fradamt/consensus-specs/blob/5750e57bd5350468e65342a4657201b95cf321f2/specs/_features/simplex/p2p-interface.md?plain=1#L402-L408). [`simplex/validator.md` L88–L92](https://github.com/fradamt/consensus-specs/blob/5750e57bd5350468e65342a4657201b95cf321f2/specs/_features/simplex/validator.md?plain=1#L88-L92).
- **Quote.** "Simplex finality attestations are one-per-round duties, use slot checkpoints, and immediately update the per-validator latest-head view as soon as a valid wire message is received." "At `VIEW_FREEZE_DUE_BPS` in the final slot of round `R`, process every valid round-`R` finality attestation delivered at or before the boundary ... A missed freeze or selection is not reconstructed later". "This gives the single validator's vote the same fork-choice delivery path as a validated aggregate without waiting for aggregation or block inclusion." Validator guide: "so head fields — the SG and TSQ inputs — keep flowing at all heights."
- **Bears on.** Delivered, level 2, "more relaxed in DC than in Gasper, because these attestations do not play into fork choice": **contradicts** it for this spec, which [`specs/README.md`](../../../specs/README.md) names as our reference. Here a finality vote carries a head field, each vote must reach nodes on the wire, and there is a hard boundary per round. Entry 29 shows the EIP-8453 branch chose otherwise.

### 34. Simplex bounds aggregate gossip by content: an aggregate is forwarded if it adds a signer, whoever sent it

- **Source.** [`simplex/p2p-interface.md` L601–L616](https://github.com/fradamt/consensus-specs/blob/5750e57bd5350468e65342a4657201b95cf321f2/specs/_features/simplex/p2p-interface.md?plain=1#L601-L616). [`simplex/validator.md` L1076–L1079](https://github.com/fradamt/consensus-specs/blob/5750e57bd5350468e65342a4657201b95cf321f2/specs/_features/simplex/validator.md?plain=1#L1076-L1079).
- **Quote.** "ignore every aggregate that adds none, even when it uses a previously unseen aggregator." Aggregation itself is inherited: "Aggregation follows the same pattern as the base spec (aggregation selection via `is_aggregator`, aggregate construction, timed broadcast at the aggregate deadline".
- **Bears on.** Sybil resilience: **extends**. This is a bound on what is forwarded per signer, in place of a bound per sender. No displacement: **supports**. Inference from reading the function: `seen.aggregator_rounds` is written at L615 and never read, so the "first aggregate per aggregator" rule is gone in this pseudocode.

### 35. On the available-committee topic any node may aggregate; publishing a vote must not wait for aggregation

- **Source.** [`simplex/validator.md` L1338–L1364](https://github.com/fradamt/consensus-specs/blob/5750e57bd5350468e65342a4657201b95cf321f2/specs/_features/simplex/validator.md?plain=1#L1338-L1364).
- **Quote.** "Aggregation MUST NOT delay this initial publication." "There is no selection-proof wrapper for this topic. Any node MAY combine contributions with identical complete data ... then publish the resulting `AvailableAttestation`." "Gossip superset rules suppress redundant aggregates, while proposers may continue collecting valid contributions for block inclusion".
- **Bears on.** Sybil resilience, "a set that anyone can join does not work": **contradicts** it for a 512-member BLS committee, where the sender set is open and the bound is on content. Inference: it carries over to PQ only if "adds a signer" can be checked from the bitfield before the proof. Recoverable, public fallback: **supports**.
- **Numbers.** 512 members; publish by 25 % of the slot; receivers cut off at 50 %.

### 36. Simplex asks nodes to keep and re-gossip the signed wire messages, and separates "valid on gossip" from "includable"

- **Source.** [`simplex/p2p-interface.md` L121–L142](https://github.com/fradamt/consensus-specs/blob/5750e57bd5350468e65342a4657201b95cf321f2/specs/_features/simplex/p2p-interface.md?plain=1#L121-L142). [`simplex/validator.md` L1174–L1189](https://github.com/fradamt/consensus-specs/blob/5750e57bd5350468e65342a4657201b95cf321f2/specs/_features/simplex/validator.md?plain=1#L1174-L1189).
- **Quote.** "TSQ relay additionally requires the ordinary attestation pool to retain the concrete validated signed messages ... The proposer first publishes any missing named blocks and ancestry and re-gossips every retained support-round message". "For a block-carried aggregate ... the aggregator wrapper and its signature are still absent from the block and must come from the retained gossip message." "The proposer ... MUST NOT treat a well-gossiped aggregate as includable. Gossip validity has never implied includability here". "it SHOULD select previous-epoch aggregates first because they expire first, then aggregates covering the greatest not-yet-included effective balance".
- **Bears on.** Delivered: **sharpens** the definition. A node can hold a valid proof for a vote that the proposer's chain cannot include. **Lacks:** retention and re-gossip of wire aggregates after inclusion. Inference: under PQ that is about 200 KiB per retained aggregate.

---

## 6. Three lists

### Requirements or properties stated in the source that our list lacks

1. **Equivocation evidence is delivered.** Gossip forwards a second, different vote per validator and round (entry 32).
2. **A floor on nodes per subnet,** and a backbone that is stable, found in under a minute and enforceable (entries 9, 10).
3. **Resistance to an adversary that joins a subnet** with ground node IDs, holding no stake and silencing nobody (entry 11).
4. **Deduplication caches live as long as the inclusion window** (entry 18).
5. **Signer first, costly work second,** and attributability of whoever triggers the work (entry 20).
6. **Deduplication keyed by data and signers,** not by the unsigned fields (entry 29).
7. **Publishing a vote does not wait for aggregation** (entry 35).
8. **Wire aggregates are kept and re-gossiped after inclusion** (entry 36).
9. **Valid on gossip is not the same as includable;** the proposer re-validates against its own chain (entry 36).
10. **The proof's statement binds the signature's leaf index** (entry 27).
11. **Voters' rational timing,** and **failures correlated by client software** (entry 14).
12. **Who bears an aggregator's failure:** the proposed EIP-8453 rewards penalise the first proposer (entry 31).

### Places where the source contradicts our list

1. **Nodes per subnet "400 to 500 with nodes on 2 of 64".** The source's 500 predates that rule, and it expects under 200 after (entry 10).
2. **The baseline has no fallback row.** Proposers are "the aggregators of last resort" today (entry 17).
3. **"One vote per epoch and validator" as the spam bound.** Decoupled-consensus specs want two (entry 32).
4. **"These attestations do not play into fork choice."** False in the Simplex pyspec, true in the EIP-8453 branch (entries 33, 29).
5. **"A set that anyone can join does not work."** Simplex opens aggregation to any node on one topic and bounds content (entries 34, 35).
6. **"Until the round ends" as the deadline of level 1.** The proposed rewards pay in full for one slot and reach zero after 16 (entry 31).
7. **A later aggregator silent when earlier proofs together cover it.** The `pq` spec rules that out, with a reason (entry 24).
8. **Aggregators on several whole subnets.** Rejected by the "exactly one committee" rule in Electra and `pq`; favoured by one sentence of the EIP-8453 branch (entries 19, 30).
9. **k = 16 read as the baseline's resilience.** Its authors chose it "without too much thought" and kept it for one reason, entry 2 (entry 1).

### Where I looked and found nothing

- **A derivation of 16,** beyond entries 1 and 2. **A derivation of 1/3 and 2/3:** PR 1440 gives none.
- **Any statement that the selection is private in order to protect aggregators from attack.** Searched the spec text and issues for "aggregator DoS secret", "aggregator privacy", "aggregator subscribe subnet leak".
- **Lazy, censoring or withholding aggregators, or pay for aggregating.** Searches for "lazy aggregator", "censoring aggregator", "aggregator incentive", "aggregator reward" returned nothing relevant.
- **Denial of service, censorship or privacy of public aggregators in the `pq` files** at `4c29678` (entry 28).
- **Aggregator selection, aggregate topics or deadlines in the EIP-8453 branch:** all TODO (entry 29). Simplex adds no new aggregator selection.
- **Not read, or only skimmed:** issues 1777, 2692, 4031 and 5829 (body); PRs 3545, 3623, 4015; branches `dc-lock-updates` and `dc-optimistic-confirmation`; documents linked from the threads (HackMD notes, spreadsheets, client issues). `git log -S` over the full history was too slow on the blobless clone, so history was traced through pull request numbers and release tags.
