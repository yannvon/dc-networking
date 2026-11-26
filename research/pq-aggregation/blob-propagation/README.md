---
title: Blobs for aggregate propagation
status: wip
date: 2026-11-25
provenance: agent
---

> **Provenance: agent.** Written 2026-11-25 by an agent for topic Q27 of the [PQ aggregation strategy](../README.md) workstream, and revised the same day after the oversight thread's review. Yann's prompt was one sentence: "using blobs as part of the aggregate propagation strategy, instead of SEACAST for example". Which blobs he means is not known yet, so this note works out three readings and picks one. Yann has not reviewed it.
> - Sources: SEACAST [post](https://notes.ethereum.org/@cskiraly/seacast) version 2 (2026-11-17) and its [specification](https://github.com/cskiraly/informed-diffusion-spec) at `ca0bbb0` (v0.12.0 draft, 2026-11-22); leanVM at [`20a75c1`](https://github.com/leanEthereum/leanVM/tree/20a75c102288b6016b5ff8057f8c51c80a222f77) (`doc/leanvm/body/10-ethereum.tex`, `README.md`, `doc/site/benchmarks.json` measured at `be190e9`); consensus-specs `master` at `d2021d2` for blob parameters.
> - Every computed number below is printed by [`arith.py`](arith.py) (stdlib; `python3 arith.py`). Measurements quoted from a source (SEACAST's times, leanVM's verification times) are cited where they appear. It is arithmetic, not simulation: times are downlink floors, bytes received divided by link rate, on a link that carries nothing else. Real delivery is slower; SEACAST measures 2.6–3.2× its own lower bound.
> - Symbols follow [`properties/aggregation-broadcast.md`](../../../properties/aggregation-broadcast.md). P is the number of intermediate proofs published per slot, s their size, m the merge fan-in, j the subnets a node backs, c its custody count out of C = 128 columns. Concrete values are examples only: s = 204 KiB (leanVM leaf, 1,400 signatures), 280 KiB (recursion), P ∈ {16, 64, 128}, j = 2, k = 4, N = 8,000 nodes.
> - **Edited on integration** by the oversight thread, 2026-11-25, after it reran `arith.py` and rechecked the cited leanVM, SEACAST and consensus-specs figures. Three changes: the latency table counts the children of a merge, not P (the first review had conflated the two); reading 1 names the sparse blobpool, [EIP-8070](https://github.com/ethereum/EIPs/blob/e3e214423e3dcbbcfaf1186211ad02971eff98a8/EIPS/eip-8070.md); and "Open" gains merger topics keyed by merger.
> - **Yann's answer, 2026-11-26,** worked in by the oversight thread the same day. Which blobs he means: "blobs are a specific type of transaction", with "they are stored for say 2 weeks only" and a pointer to a HackMD note and to an "asynchronous blobs write-up" for "future improvements possible". That is reading 1. The HackMD note is the draft of [EIP-8256](https://github.com/ethereum/EIPs/blob/bdc1d099649eefb8790b76f912e25487757f5f4e/EIPS/eip-8256.md), Blob Streaming. Section 5 is new and reads it against reading 1; the short version and section 6 say what changed. Its quotes from the EIP, read at `bdc1d09`, and from the [ethresear.ch post](https://ethresear.ch/t/24202) on the same proposal were matched by script against the downloaded texts. No text named "asynchronous blobs" was found. Asked again that day, Yann said of the write-up that "it might now be called something like blob streaming, it should also mention blob tickets". The post is called that and has a section on blob tickets, so it is taken to be the write-up. Nothing in section 5 is computed.

# Blobs for aggregate propagation

## Short version

- **The question is not blobs against SEACAST. It is who receives a whole proof.** A node that verifies a proof needs every byte of it, so sampling only helps the nodes that do not verify. Only mergers (next-tier aggregators, proposers, builders) verify intermediate proofs, yet today's `pq` spec sends every aggregate whole to every node.
- **Three ways to move intermediate proofs**, compared here:
  - *global whole delivery*, today's `beacon_aggregate_and_proof`;
  - *merger topics*, the baseline [`../../pq/README.md`](../../pq/README.md) already assumes: leaf proofs go whole on per-subnet topics that only their mergers and opt-in nodes join;
  - *sampled diffusion* (reading 3): each proof is coded into cells, every node custodies a few columns of every proof, and only mergers rebuild.
- **Against global delivery, sampled diffusion wins on bytes by 7× at P = 64** (5.3 MiB per node per slot against 38 MiB with SEACAST-like copies). **Against merger topics it does not win on bytes.** A node on 2 subnets receives 4.8 MiB at the same copies, 7.2 MiB at gossipsub's, and does not grow with P. A node on no subnet receives nothing. At equal copies the two break even at S = j·C/(2c) = 16 subnets for c = 8, and above that merger topics are cheaper.
- **What sampled diffusion buys over merger topics:**
  - A proof is keyed by (slot, aggregator), not by subnet. It fits any coverage set, so it still works if [dispersed assignment](../README.md) gives each aggregator several subnets, where per-subnet topics no longer fit a proof.
  - Every node holds part of every proof, so a late merger, proposer or builder can fetch any proof. Under merger topics only N·j/S nodes hold a given proof: 1,000 at S = 16, 250 at S = 64.
  - A merger asks for exactly the children it merges, one per subnet: 9.7–10.8 MiB at 3 copies. On merger topics it receives every aggregator's proof: 38 MiB at k = 4, or 9.6 MiB if the later aggregators stay silent, as the `pq` spec's staggering at `4c29678` intends.
  - Forwarding nodes verify no STARK.
- **What it costs:** every node pays about 5 MiB per slot instead of nodes off the topics paying nothing. Custodians cannot check a proof before forwarding it. An aggregator that publishes fewer than half its cells is lost. It needs a new object type.
- **Recommendation, conditional:** use sampled diffusion when proofs do not map one-to-one onto subnets, or when every node should hold part of every proof for late inclusion and builder access. If neither holds, merger topics are as cheap, simpler, and can verify before forwarding. Either way, sampled diffusion is a use of SEACAST (its *derived* interest) or of PeerDAS-style column topics, not a rival to SEACAST.
- **Latency does not separate the options.** A merger receives its children whole in every mode. Vote deadline to merged proof is 1.61–3.14 s for one merge level and 2.35–4.62 s for two (64 children with m = 16). Including aggregator uploads it is 1.68–3.28 s and 2.51–4.94 s. One level fits Q17's 4 s; two levels fit it only on the faster machines. The children of a full merge are one proof per subnet, not all P = S·k of them, so one level covers up to 16 subnets.
- **The block's proof** must reach every node whole. That hop stays a broadcast, and SEACAST is the candidate there.
- **Today's blobs (reading 1) do not fit,** on KZG and on capacity. This is the reading Yann means (2026-11-26). Blob streaming, a draft, would remove a third objection, that sampled blob data arrives only with its block, and it brings an admission rule for an open set of senders. KZG, capacity and the price stay ([section 5](#5-blob-transactions-and-blob-streaming)). **LeanDA (reading 2)** is not needed for aggregates but may let a block carry one merged proof instead of a DA proof and a vote proof.

## 1. Two hops, two different needs

| Hop | From → to | Who verifies | Needs the whole object |
|---|---|---|---|
| Intermediate | aggregator → its mergers (next-tier aggregator, proposer, builder) | the merger | the merger only |
| Final | proposer → every node, in or beside the block | every node, on import (`process_stark`) | every node |

Today's `pq` spec puts the intermediate hop on a global topic: every node receives every `SignedAggregateAndProof` (~212 KiB) and checks its STARK before forwarding ([design note](../../pq-gasper/design.md)). That is broadcast used where only delivery to a few mergers is needed. The [builders note](../../../posts/pq-gasper-builders.md) adds a second reason for broadcast: in PQ Gasper, slot N's head votes must reach every node before block N+1, so a full-slot aggregate goes to everyone. Under PQ-DC finality votes are off the head's critical path, so that reason applies to the available chain's head votes, not to finality aggregates.

## 2. Three readings

### Reading 1: today's blobs carry aggregate bytes

An aggregator posts its proof as blob data: a type-3 transaction, KZG commitments, data-column sidecars.

- **Not post-quantum.** KZG commitments and cell proofs rest on pairings. A PQ fork must replace them anyway.
- **Two paths, neither useful.** Blob transactions are announced and fetched in the execution layer's blobpool before inclusion (EIP-4844's network wrapper), so the bytes could reach a merger before the block. That path delivers whole blobs to every EL node that fetches them, which is global whole delivery under another name. The consensus-layer path with custody and sampling is what would help, and it carries blob data only with a block, a slot too late for the merger.
- **The sparse blobpool is the precedent for reading 3.** [EIP-8070](https://github.com/ethereum/EIPs/blob/e3e214423e3dcbbcfaf1186211ad02971eff98a8/EIPS/eip-8070.md) (`eth/72`, status Last Call at `e3e2144`, read 2026-11-25) changes the first path. An EL node fetches a blob transaction's whole payload with probability 0.15, and otherwise only the cells of its consensus-layer custody set. That is sampled diffusion before the block, with a minority of nodes holding the whole object, already specified for blob transactions. It keeps KZG and the blob limits, so this reading still fails.
- **Too small.** A 204 KiB proof fills 2 blobs of 126,976 usable bytes (82 %), a 280 KiB one 3. P = 16 leaf proofs take 32 blobs, P = 64 take 128, against `MAX_BLOBS_PER_BLOCK` = 21 on mainnet since January 2026. Aggregates would also compete with rollups in the blob fee market.
- **Custody does not deliver.** A node custodies 4 to 8 of 128 columns (`CUSTODY_REQUIREMENT`, `VALIDATOR_CUSTODY_REQUIREMENT`); only supernodes rebuild whole blobs.

The reading fails on KZG and on capacity. Nothing in it is worth keeping beyond the dissemination idea, which reading 3 takes on its own.

### Reading 2: a post-quantum DA layer (LeanDA) carries them

LeanDA ([`10-ethereum.tex`](https://github.com/leanEthereum/leanVM/blob/20a75c102288b6016b5ff8057f8c51c80a222f77/doc/leanvm/body/10-ethereum.tex) @ `20a75c1`): a row is 128 KiB of payload coded to 256 KiB in 128 cells of 2 KiB, any 64 rebuild it, 1–32 rows under one root, a cell authenticated by 12 hash siblings. A leanVM proof proves every row is a codeword. The same guest program checks signatures, a blob matrix, or child proofs, and a node "may pass on one child's root".

- **For aggregates, the encoding proof is not needed.** Sampling security needs it because samplers never see the whole row. A merger does see it: it rebuilds from 64 cells, re-encodes, compares the root (SEACAST's decode-and-compare), and then verifies the STARK. A wrong encoding or a wrong proof fails one of those checks. A Merkle root over coded cells, as in SEACAST Lite §1, is enough.
- **It cannot be self-referential.** An aggregate proof cannot attest the encoding of its own bytes. A proof over a DA root of *other* proofs gains nothing, because the merger verifies those proofs anyway.
- **Where it does help: the block.** If PQ blobs use LeanDA, each block needs a DA proof (leanVM's README: 290 KiB, 0.58 s for 32 blobs on an M4 Max). The vote proof and the DA proof can be children of one merge. If the merged proof is the size of a recursion proof (280 KiB), the block carries 290 KiB less, on the hop every node receives. Neither that size nor the merge's proving time is benchmarked.

### Reading 3: blob-style dissemination of an aggregate object

Reuse the mechanics, not the data: cells on column topics, custody, reconstruction.

- **Object.** An aggregate of size s is coded at rate 1/2 into cells laid out as ⌈s / 128 KiB⌉ rows of 128 cells (2 rows for a leaf proof), with a Merkle root. The aggregator signs a small header: slot, aggregator index, coverage bits, root, descriptor (~2.7 KiB with the XMSS signature).
- **Who gets what.** An ordinary node joins every aggregate column topic it custodies and receives its columns of every aggregate: a share 2c/128 of each. A merger declares interest in the whole of the aggregates it merges and rebuilds each from any half of the cells.
- **Group id.** (slot, aggregator index), known before any cell exists. That sidesteps the non-determinism of proofs ([2026-10-27 call](../../../meetings/2026-10-27.md)): deduplication is per sender, not per content, which matches the spec's one aggregate per aggregator per duty.
- **Independent of the coverage set.** Nothing in the group id, the custody or the topics depends on which subnets the aggregator covered; the coverage bits travel in the header. If the dispersed-assignment topic ends with aggregators that each cover d ≥ 2 subnets, a per-subnet topic no longer fits a proof: the aggregator publishes on all d topics, which multiplies the bytes by d, or topics follow coverage sets, which multiplies them in number. Sampled diffusion has neither problem. A merger finds a child by its header, whatever it covers.
- **Transport.** Either PeerDAS-style column topics with gossipsub Partial Messages (the group is the aggregate, the parts are cells; Silver already implements this for data columns, [notes](../../clients/silver/README.md)), or SEACAST with an aggregate object type: interest `DERIVED` for custodians, `ALL` for mergers, duty `FORWARD` (SEACAST spec §1.2). Kamil's announcement pool is SEACAST's announce-and-ask applied to whole proofs.

## 3. Arithmetic

### Bytes per node per slot

s = 204 KiB. "Copies" are data copies received per node. Gossipsub's 4.5 is this repo's runs of Barnabé's model. SEACAST's 3 is our reading of its Figure 6, which gives about 3.2 copies at 128 KiB falling to 1.6 at 4 MiB on the all-home network, most of the fall between 256 KiB and 1 MiB; it is not a measured point at this size. Custody assumes 3 copies plus the header in every copy. Merger topics: a node backs j = 2 subnets with k = 4 proofs each, which does not depend on P.

| P | Global, gossipsub | Global, SEACAST | Merger topics, gossipsub / SEACAST | Custody 4/128 | Custody 8/128 |
|---:|---:|---:|---:|---:|---:|
| 16 | 14.3 MiB | 9.6 MiB | 7.2 / 4.8 MiB | 0.7 MiB | 1.3 MiB |
| 64 | 57.4 MiB | 38.3 MiB | 7.2 / 4.8 MiB | 2.9 MiB | 5.3 MiB |
| 128 | 114.8 MiB | 76.5 MiB | 7.2 / 4.8 MiB | 5.8 MiB | 10.6 MiB |

A node on no subnet topic receives nothing under merger topics. As downlink floors (link otherwise idle):

| P | Global, gossipsub | Global, SEACAST | Merger topics, gossipsub / SEACAST | Custody 8/128 |
|---:|---:|---:|---:|---:|
| 16 | 1.2 s at 100 Mbit/s, 2.4 s at 50 | 0.8 / 1.6 s | 0.60 / 0.40 s at 100, 1.20 / 0.80 s at 50 | 0.11 / 0.22 s |
| 64 | 4.8 / 9.6 s | 3.2 / 6.4 s | same | 0.44 / 0.89 s |
| 128 | 9.6 / 19.3 s | 6.4 / 12.8 s | same | 0.89 / 1.8 s |

- **Global delivery caps P.** Within a 1 s floor on a 100 Mbit/s downlink it fits P ≤ 13 (gossipsub) or P ≤ 19 (SEACAST); custody 8 fits P ≤ 144. Halve each at 50 Mbit/s.
- **Merger topics already remove that cap,** which is why [`../../pq/README.md`](../../pq/README.md) put leaf proofs below the global topic. Custody costs grow with P = S·k; merger topics do not. At equal copies they break even at S = j·C/(2c): 16 subnets for c = 8, 32 for c = 4.
- **Merge levels.** m = 16 still forces two merge levels above 16 children in every mode; the propagation mode moves bytes, not the tree. A full merge takes one proof per subnet, because the k proofs of a subnet are alternatives. With one subnet per aggregator that is S children, not P = S·k: P = 64 at k = 4 is 16 subnets and one level, and two levels start above S = 16.

### Merger and aggregator

- **A sampled-diffusion merger of m children** receives m·s plus Merkle paths (12.5 % on 2 KiB cells, 1 % on 16 KiB chunks). For m = 16 leaf proofs that is 3.2–3.6 MiB at one copy and 9.7–10.8 MiB at three. The floors are 0.27–0.30 s and 0.81–0.90 s at 100 Mbit/s. For m = 16 recursion proofs it is 4.4–4.9 MiB at one copy.
- **A merger-topic merger** joins its 16 subnet topics and receives every proof on them: 57.4 MiB with gossipsub, 38.2 with SEACAST-like copies, 12.8 at one copy for k = 4. If only one aggregator per subnet publishes, which is what the spec's staggering intends when the first one succeeds, those fall to 14.3, 9.6 and 3.2 MiB, the same as sampled diffusion.
- **An aggregator** uploads its coded object once: 67 ms for a leaf proof at 50 Mbit/s up, 134 ms at 25.

### Latency from the vote deadline

The floors use one copy, the 16 → 1 merge time for every merge (an upper bound for the 4 → 1 merge of 64 children), and two bounds. The fast bound pairs the fastest machine with 16 KiB cells on a 100 Mbit/s downlink. The slow bound pairs the slowest machine with 2 KiB cells on a 50 Mbit/s downlink. Proving takes 0.70–1.27 s and merging 0.65–1.27 s (`benchmarks.json`, all threads, four machines). The rows count the children of the merge, one proof per subnet, not P.

| Tree | Prove + diffuse + merge | With aggregator uploads |
|---|---:|---:|
| One merge level (at most m = 16 children) | 1.61–3.14 s | 1.68–3.28 s |
| Two levels, 64 children (16 → 4 → 1) | 2.35–4.62 s | 2.51–4.94 s |
| Two levels, 128 children (16 → 8 → 1) | 2.45–4.83 s | 2.60–5.14 s |

Q17's 4 s aggregation phase holds one level on every machine and two levels only on the faster ones. Q19's 2 s holds one level only on the faster ones. Propagation to the merger is the small term, and it is about the same in every mode, because the merger receives its children whole in all of them.

### The final hop

The block's proof (~280 KiB, ~313 KiB block) goes to every node whole. SEACAST reports 0.32 s for 99 % of 500 all-home nodes at 128 KiB against 0.66 s for gossipsub, and 0.64 s against 4.5 s at 1 MiB. Blobs cannot help here: every node verifies.

## 4. Against the properties

| Property | Global whole delivery | Merger topics (baseline) | Sampled diffusion (reading 3) |
|---|---|---|---|
| **Performant: bytes** on topics every node joins | P·s·copies: 38 MiB at P = 64 (SEACAST copies) | none; j·k·s·copies on the topics a node backs: 4.8–7.2 MiB, 0 off them | P·s·2c/C·copies: 5.3 MiB at P = 64, c = 8 |
| **Performant: latency** | propagation binds as P grows (3.2 s floor at P = 64) | merger floor; it receives k proofs per subnet unless later aggregators stay silent | merger floor, 0.3–0.9 s for 16 children; the tree sets the total |
| **Performant: proofs verified before forwarding** | P STARKs per node (5.4 ms for a leaf proof, 8.8 ms after recursion, leanVM README) | j·k STARKs per node on the topics | none; one XMSS header check per aggregate, a hash path per cell |
| **Fault-tolerant** | reaches a merger if any path does | the topic's N·j/S members (1,000 at S = 16, 250 at S = 64) carry it whole | half the cells must arrive; N·c/C custodians per column (500 for c = 8). An aggregator that publishes fewer than half its cells is lost here and not in the other two |
| **Bounded spam** | STARK check before forwarding | STARK check before forwarding | custodians cannot check validity, so an invalid proof spreads its cells. The bound comes from the sender set and one object per (slot, aggregator), checked on the signed header, and equals the honest load. A signed header over rebuilt bytes is evidence of an invalid proof; whether to make it slashable is open |
| **Recoverable** | every node has every proof | N·j/S nodes hold each proof | every node holds 2c/C of every proof; a late merger fetches 64 columns by request, as PeerDAS sampling does |
| **Open to builders** | every node has every aggregate | a builder joins every subnet topic | a builder declares interest `ALL`: 12.8 MiB at P = 64 at one copy, 38.2 at three. A home proposer that cannot take that relies on merged proofs |
| **Encoding independent of the topology** | yes | no: topics follow subnets, so d ≥ 2 coverage sets do not fit | yes: keyed by (slot, aggregator) |

## 5. Blob transactions and blob streaming

*Added 2026-11-26 by the oversight thread, after Yann's answer. It is an agent's reading of two public texts, and nothing in it is computed.*

**What Yann means by a blob.** "blobs are a specific type of transaction", and "they are stored for say 2 weeks only". That is reading 1.

- **A blob is named by a transaction.** A blob transaction (type 3, EIP-4844) lists its blobs by the hashes of their KZG commitments. The data travels on the consensus layer, in columns that nodes custody and sample.
- **It is kept for about 18 days.** A node serves blob data for 4,096 epochs (`MIN_EPOCHS_FOR_DATA_COLUMN_SIDECARS_REQUESTS`, consensus-specs @ `d2021d2`).
- **Reading 1 failed on three counts** (section 2): KZG, capacity, and timing, because the sampled path carries blob data only with its block.

**What he pointed to: blob streaming.** The HackMD note he linked is the draft of EIP-8256, "Blob Streaming", which has been in the EIPs repository as a draft since 2026-06-11. The post "Scaling the DA layer with Blob Streaming" ([ethresear.ch topic 24202](https://ethresear.ch/t/24202), 2026-02-25) argues for it. What it changes:

- **Two kinds of blob.** JIT blobs are "propagated *on the critical path* as today's blobs", and AOT blobs are "propagated *ahead of time* (pre-propagated) using a ticket-based propagation mechanism" ([EIP-8256 L16](https://github.com/ethereum/EIPs/blob/bdc1d099649eefb8790b76f912e25487757f5f4e/EIPS/eip-8256.md?plain=1#L16)). Both travel on the consensus layer, and blob data leaves the execution layer's mempool ([EIP-8256 L130](https://github.com/ethereum/EIPs/blob/bdc1d099649eefb8790b76f912e25487757f5f4e/EIPS/eip-8256.md?plain=1#L130)).
- **A ticket is bought on chain, for one slot.** A system contract sells it a fixed lookahead before its slot, which "can be set to a value e.g. `1` epoch", and "A ticket is valid only during that exact `target_slot`" ([EIP-8256 L235](https://github.com/ethereum/EIPs/blob/bdc1d099649eefb8790b76f912e25487757f5f4e/EIPS/eip-8256.md?plain=1#L235)). Its price is the blob base fee, and "Ticket fees are burned at purchase time with no refund mechanism" ([EIP-8256 L440](https://github.com/ethereum/EIPs/blob/bdc1d099649eefb8790b76f912e25487757f5f4e/EIPS/eip-8256.md?plain=1#L440)).
- **A ticket names a key, not the data.** "This allows the ticket holder to defer data preparation until after purchase" ([EIP-8256 L456](https://github.com/ethereum/EIPs/blob/bdc1d099649eefb8790b76f912e25487757f5f4e/EIPS/eip-8256.md?plain=1#L456)). The holder signs its columns with that key, which is a BLS key.
- **Gossip admits by ticket.** New column subnets take a sidecar that carries a valid ticket, in its target slot or the slot before ([EIP-8256 L387–L393](https://github.com/ethereum/EIPs/blob/bdc1d099649eefb8790b76f912e25487757f5f4e/EIPS/eip-8256.md?plain=1#L387-L393)), and "Only the first valid sidecar per `(ticket_id, column_index)` is accepted". "Both JIT and AOT use a shared custody model (same column indices)" ([EIP-8256 L396–L398](https://github.com/ethereum/EIPs/blob/bdc1d099649eefb8790b76f912e25487757f5f4e/EIPS/eip-8256.md?plain=1#L396-L398)).
- **What that gives.** "there is at any time a globally agreed upon bounded set of eligible blob senders", and "the cost for honest and dishonest usage is equal" ([EIP-8256 L26](https://github.com/ethereum/EIPs/blob/bdc1d099649eefb8790b76f912e25487757f5f4e/EIPS/eip-8256.md?plain=1#L26)).

**Against the objections to reading 1.**

| Objection in section 2 | With blob streaming |
|---|---|
| Sampled blob data arrives only with its block, "a slot too late for the merger" | Gone. Columns sent ahead of time travel in the ticket's slot, before any block names them |
| The early path, the blobpool, delivers whole blobs to every node that fetches them | Gone. Blob data is no longer in the execution layer's mempool |
| KZG is not post-quantum | Stays. The ticket adds a BLS key and a BLS signature |
| Capacity: P = 64 leaf proofs are 128 blobs, against 21 per block | Open. The caps and the lookahead are "TBD" in the draft ([EIP-8256 L44–L47](https://github.com/ethereum/EIPs/blob/bdc1d099649eefb8790b76f912e25487757f5f4e/EIPS/eip-8256.md?plain=1#L44-L47)). The post expects more room off the critical path: "The AOT blob throughput that the system can provide is meaningfully higher than pure JIT throughput" |
| Aggregates compete with rollups in the blob fee market | Stays, and the fee is paid in advance: 2 to 3 blobs per proof |
| Custody does not deliver: only a node that rebuilds holds the proof | Stays. A merger rebuilds from half the columns, as in reading 3 |

**What it would mean for an aggregate** (the agent's reading).

- **It is reading 3's dissemination, with an admission rule that reading 3 lacks.** Reading 3 needs a new object type, and it bounds spam by the sender set. A blob sent ahead of time is such an object, already sampled and custodied, and a ticket bounds its senders without tying them to stake or to an assignment. That is a third answer to who may publish a proof: whoever paid. The properties leave this open for the third level of delivery, where the question is whether it "can carry a fallback, under the mempool's or a blob's own admission rules" ([Recoverable](../../../properties/aggregation-broadcast.md#recoverable)).
- **The ticket has to be bought before the duty.** With a lookahead of an epoch, an aggregator whose duty is known an epoch ahead can buy a ticket for its slot. An aggregator drawn by a private lottery would show itself by buying one. A prover that steps in after a failure has no ticket for that slot unless it bought spares.
- **Somebody pays.** Nothing pays an aggregator today ([Incentive compatibility](../../../properties/aggregation-broadcast.md#incentive-compatibility)). Here it would buy 2 to 3 blobs per proof and duty at the blob base fee.
- **A proof needs the propagation, not the transaction.** A blob transaction makes a block's validity depend on its blobs being available. A proposer that merges a proof into its block's proof has checked that proof itself. So an aggregate would use the ticket and the column subnets, and no transaction would have to name it. Whether an object of the consensus layer may depend on a ticket contract of the execution layer is open.
- **Two weeks of storage are enough for a proof and too little for a record.** An intermediate proof is needed until it is merged into a block's proof, or until its votes can no longer be included. What has to outlive it is what the chain keeps: the signer bits and the block's proof. Nothing that slashing needs later may live only in a blob ([Accountable](../../../properties/aggregation-broadcast.md#safety)).
- **Censorship.** The EIP leaves it out: "This EIP does not include mechanisms for mandatory inclusion of AOT blob transactions" ([EIP-8256 L472](https://github.com/ethereum/EIPs/blob/bdc1d099649eefb8790b76f912e25487757f5f4e/EIPS/eip-8256.md?plain=1#L472)). The post goes further. A committee records which blobs sent ahead of time are available, and the proposer has to take them: "they must include what the PTC requires (liveness) and cannot include what isn't available (safety)". For aggregates that would bind a proposer that leaves a proof out.
- **It is not post-quantum.** PQ-DC ships with post-quantum signatures from the start ([properties](../../../properties/README.md)). A path for votes through KZG commitments and tickets signed with BLS is not. So this is for a blob layer that is post-quantum itself, which is the ground of reading 2.

**What stays of the recommendation.** The conditional recommendation of the short version stands for the first two levels of delivery: merger topics, or sampled diffusion on topics of the consensus layer. Blob transactions come in at the third level, as a place where anyone who paid can leave a proof for a proposer to pick up. That needs blob streaming, or a post-quantum successor to it, to exist. So it is one of the "future improvements possible" (Yann), not a design for the first PQ-DC fork.

**The "asynchronous blobs write-up" is the post read above.** Yann named such a write-up next to the HackMD note. No text has that name: on 2026-11-26 the phrases "async blobs" and "asynchronous blobs" returned nothing on ethresear.ch, and the EIPs repository has neither. Asked again that day, Yann said "it might now be called something like blob streaming, it should also mention blob tickets". The post matches both.

- **Its name.** "Scaling the DA layer with Blob Streaming" ([ethresear.ch topic 24202](https://ethresear.ch/t/24202), 2026-02-25).
- **Blob tickets.** It has a section of that name: "Blob tickets take the ticketing concept further, moving pre-propagation to the CL".
- **The old name.** One [Discord message of 2026-02-05](https://github.com/ethereum/eth-rnd-archive/blob/18a6ec37623deb1b682080bedb3bddc854a95d0c/l1-zkevm-protocol/_threads/Stateless%20%2B%20DA%20sampling/2026-02-05.json) #3, by soispoke, says "async blob post coming soonTM". The post appeared twenty days later and thanks soispoke for input. What the message calls async, the post calls AOT, for ahead of time.

So this section has read the write-up Yann meant. That is an agent's conclusion from his description: he has not seen the post named back to him.

**Where the tickets come from** (skimmed on 2026-11-26 and not worked into this note). The post points to earlier proposals that sell the right to propagate a blob in the execution layer's blobpool. [On the future of the blob mempool](https://ethresear.ch/t/22613) (2025-06-14) sells blobpool tickets in "a simple first-price auction with a reserve". [Variants of Mempool Tickets](https://ethresear.ch/t/23338) (October 2025) lays out proposals for implementing them. Both cite Francesco D'Amato's note [Blob mempool tickets](https://hackmd.io/@fradamt/blob-mempool-tickets); a second note under his name, [Mempool DAS with blob tickets](https://hackmd.io/@fradamt/blob-tickets), is cited on the Discord in March 2025. A thread that takes the blob idea further should read these first.

## 6. Open

- **What Yann meant.** Answered on 2026-11-26: reading 1, blob transactions, with blob streaming as what may come ([section 5](#5-blob-transactions-and-blob-streaming)). Open there: the caps on blobs sent ahead of time, the price, whether an aggregator's duty is known a ticket's lookahead in advance, whether a consensus-layer object may depend on a ticket contract of the execution layer, and a post-quantum blob layer.
- **The "asynchronous blobs write-up".** It is the blob streaming post, going by Yann's description of 2026-11-26 ([section 5](#5-blob-transactions-and-blob-streaming)). Not worked in: the earlier texts on blobpool tickets that section 5 names.
- **Whether dispersal lands.** The case for sampled diffusion over merger topics rests mostly on coverage sets that do not match one subnet, and on recoverability. If the [dispersed-assignment](../README.md) topic keeps d = 1, merger topics are the simpler choice.
- **Merger topics keyed by merger** (added by the oversight thread, not worked out). The comparison takes merger topics to be per subnet. A topic per merger, on which that merger's children publish, would carry a proof of any coverage set once, so d ≥ 2 would not multiply the bytes. Which nodes back such a topic, and what joining it reveals about who the merger is, are open. If it works, what is left of the case for sampled diffusion is recoverability and forwarding without verifying.
- **Copies at 200–300 KiB.** SEACAST's copies per node at this size are read off a figure; custody copies (3) are assumed. Neither has been simulated with P concurrent objects from P sources, which is the case here and not SEACAST's one-source setting.
- **Who custodies what.** Whether aggregate columns ride the existing 128 column subnets (and their custody groups) or topics of their own, and whether cells of 2 KiB (blob-like) or 16 KiB (SEACAST's unit) suit a 200–300 KiB object better. Larger cells cut path overhead; more cells give finer custody.
- **Invalid-proof evidence.** Whether a signed header over an invalid proof becomes slashable, and who submits it.
- **Mixed merge cost.** Merging a LeanDA proof with a vote proof (reading 2) is permitted by the guest's statement, but its proving time and size are not benchmarked.
- **Merger exposure.** Mergers are known in advance and are the only nodes that rebuild, so flooding a merger costs its children. That is the fault-tolerance question of [dispersed assignment](../README.md) on the merge side.
