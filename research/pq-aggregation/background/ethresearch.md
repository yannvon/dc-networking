---
title: Background — ethresear.ch, for the broadcast properties
status: research notes
date: 2026-11-25
provenance: agent
---

> **Provenance: agent.** Written 2026-11-25 by a research subagent of the oversight thread of the [PQ aggregation strategy](../README.md) workstream, at Yann's request for background from consensus-specs, ethresear.ch and the Eth R&D Discord. Source: ethresear.ch only, through its JSON and raw-Markdown endpoints; 58 topics were downloaded and 45 searches run. Yann has not reviewed it.
> - **Checked by the oversight thread:** 24 quoted fragments from 21 of the entries, against the downloaded posts. All were found. The rest is the subagent's reading, unchecked.
> - **"Bears on" is the subagent's judgement** of what a post means for our properties. Where the oversight thread reads it differently, the note below says so; [`README.md`](README.md) says what went into the properties.
> - **Note on entry 1** (an opt-in aggregator role). At `4c29678` the `pq` spec draws 4 aggregators per committee from the validators and keeps them in the state. An opt-in, opt-out or registered role is discussed on the Discord ([discord F31](eth-rnd-discord.md)) and is not in that spec.

# Background from ethresear.ch

How to read an entry:

- **Source** gives the post as `https://ethresear.ch/t/<topic>/<post>`, with the forum user name and the date the post was created.
- The indented `>` line under a source is a verbatim quote from that post's raw Markdown, with formatting marks (bold, italics, link targets, `$`) removed. `[…]` marks an omission.
- Every quote was checked by script against the downloaded post text. The script and the downloads are not in this repo. Numbers under **Numbers** are from the same post unless another post is named. Anything marked *inference* or *my arithmetic* is mine and is not in the post.
- "Our" properties are those of `properties/aggregation-broadcast.md` and `properties/attestation-broadcast.md`, by their section names.

Three caveats that apply throughout:

- Topic 26263 studies EIP-8288, the recursive aggregation of *transaction* signatures in the mempool, where every node folds once a second. It is the closest measured study of a network of leanVM provers, but what it says about attestation aggregators is by analogy.
- Topics 26263 and 26227 have no replies. Topic 26292 has three, none about attestation aggregation.
- Topic 26003 describes EIP-8292 (PQ attestation aggregators) second hand. I did not read the EIP itself; it is not on ethresear.ch.

---

## A. Post-quantum aggregation and its networking (2025 to 2026)

### 1. EIP-8292's aggregator is described as an opt-in role for stronger machines, not a role drawn from all validators

- **Source:** https://ethresear.ch/t/26003/1 — pardis-toolabi, 2026-09-15
  > because producing such proofs is far more expensive than BLS's elliptic-curve addition, the work is split off to an opt-in, higher-specification aggregator role.
- **Source:** https://ethresear.ch/t/24622/1 — muellerberndt, 2026-04-09
  > pq-devnet-3 and pq-devnet-4 are already about separate aggregator roles, propagation, recursive aggregation, and one final aggregate per message.
- **Bears on:** Model, "From stake to roles" (each role censoring or Byzantine with probability β under a stake-weighted draw); DoS resilience, both regimes; Fair to proposers. **Contradicts** the assumption that roles are drawn by stake, if the description is right: an opt-in set is smaller, changes slowly and can be listed. That makes "aggregators known" the default regime and ties β of the aggregators to who opts in, not to stake (*inference*).
- **Numbers:** none.
- **Status:** quotes verified. The first is a secondary description of the EIP; the EIP text was not read.

### 2. What travels between hops is a proof of 200 to 265 KiB; folding would move about 1 GiB of witness, so it stays inside one machine

- **Source:** https://ethresear.ch/t/26227/1 — arianaraghi, 2026-11-08
  > An accumulator must carry its witness: about 1 GiB of committed words for a 1,500-signature leaf, against a 265 KiB leanVM proof. Gossip hops therefore stay recursive.
  > EIP-8292 (draft) defines leaf aggregation, recursive merges and a gossip target of about 256 KiB per aggregate.
- **Source:** https://ethresear.ch/t/23639/1 — tcoratger, 2025-12-11
  > This design reframes the challenge from a cryptographic limitation to a P2P data availability problem: ensuring that aggregator nodes can locate and fetch the required witness chunks from the network
- **Bears on:** Bandwidth (our examples use 204 KiB per proof); Merge. **Sharpens** the proof size and **supports** treating every gossiped object as a self-contained proof.
- **Numbers:** proof sizes by source. 265.1 KiB for 1,500 signatures and 218 to 248 KiB for merge proofs (26227/1, leanVM `df7d122`, rate 1/4). 224 to 262 KiB "depending on the work the fold commits to" (26263/1, leanVM `990b935`). 202.626 kB per aggregate (26292/1, figure 8). "roughly 128 KiB to 350 KiB depending on the PCS rate" (25040/1, June 2026). "130-355 KB" for about 1,400 signatures (24906/1, May 2026). "300--500 KB" for over a thousand signatures (24418/1, March 2026).
- **Status:** quotes verified.

### 3. Merge time is a step function of committed size; on a low-end machine a merge holds 5 children before a jump of 1.4 to 1.8 times

- **Source:** https://ethresear.ch/t/26227/1 — arianaraghi, 2026-11-08
  > A merge node that steps from mu 25 to mu 26 takes 1.4 to 1.8x longer for about 3% more committed words.
  > With mu-25 leaves of up to 350 signatures, a baseline mu-25 node holds up to 5 children, so 1,750 signatures.
  > A cost model that is linear in fan-in and leaf size smooths over the mu step.
  > what aggregation interval and how many signatures per aggregator should we target? We assumed 1, 2 or 4 s intervals and 512 or 1,500 signatures.
- **Bears on:** Merge ("Proofs per merge, at most m", m = 16; "the fan-in bounds the aggregators per cover"); CPU load; Latency floors. **Contradicts** m = 16 as the only limit that matters: on that machine the cost cliff comes at the sixth child, long before 16. Latency floors computed with a cost that is linear in the fan-in, as in our blob note, are of the kind the post warns about (*inference*).
- **Numbers:** leaf cost about 18.5k + 805.7 N cycles for N signatures; merge cost about 19.4k + 186.8k n cycles for n children over 250-signature leaves. So verifying one child costs about as much as 232 raw signatures (*my arithmetic*: 186.8k / 805.7). For 1,500 signatures: 5 leaves of 300 give leaf 1.059 s + merge 1.176 s = 2.235 s to the deadline and 6.471 s of CPU per slot; 6 leaves of 250 give 3.108 s and 7.988 s. Machine: 8 GB Apple M2, "We treat it as a low-end aggregator". leanVM `df7d122` of 6 Nov 2026, binary tower field with Keccak-256. A linear model is off "by up to about 0.5 to 1 s on this machine". The post also cites a survey that "lists optimal aggregation-tree construction as an open problem", and says that leanBench measures trees with fan-in 2, 4 and 8.
- **Status:** quotes verified. Times hold for one machine and one commit, as the post says itself.

### 4. Pushing proofs costs peers × proof size ÷ interval whatever the load; announcing coverage and fetching makes upload follow demand

- **Source:** https://ethresear.ch/t/26263/1 — cskiraly, 2026-11-18
  > Pushing proofs makes upload depend mainly on peer count.
  > With proofs of 224–262 KiB and an interval of 1,000 ms, six peers cost 11–13 Mbit/s.
  > Treat the degree, interval and proof size as one budget.
- **Source:** https://ethresear.ch/t/19921/1 — yiannisbot, 2024-06-27
  > the expected value is to receive 3 duplicate messages for each message
- **Bears on:** Bandwidth; Redundant work. **Sharpens:** the bandwidth property has to name the mesh degree of the proof topics and whether proofs are pushed or fetched. **Supports** the copy factor in our "38 to 57 MiB when every node receives every proof whole", which is 3 to 4.5 copies of 64 proofs of 204 KiB (*my arithmetic*): gossipsub at degree 8 is expected to deliver each message once plus 3 duplicates (19921/1).
- **Numbers:** with every node aggregating, fetch on announced coverage used 7.9 to 8.1 Mbit/s per node against 11.9 to 13.3 for the designs that push, and 2.4 against 10.5 at low load. Budget for comparison: "EIP-7870 recommends 25 Mbit/s for an attester's whole node, both clients together, 15 Mbit/s for a full node and 50 Mbit/s for a local block builder". 19921/1: with mesh degree k = 8, (k − 2)/2 = 3 duplicates; half of the aggregate messages arrived with fewer than 2.
- **Status:** quotes verified. Mempool setting; transfer to attestation proofs is by analogy.

### 5. A node can skip or defer a proof only if the announcement says what the proof covers

- **Source:** https://ethresear.ch/t/26263/1 — cskiraly, 2026-11-18
  > Two digests can't tell a node how many new transactions an overlapping proof adds.
  > A peer reads the list of transactions covered by an announced proof. It fetches the proof if its next fold would take it, and skips a raw transaction fetch if an announced proof covers the transaction.
- **Bears on:** Redundant work (the `pq` spec's staggered aggregators; under a dispersed assignment a later aggregator "can stay silent only when several earlier proofs together do"); No displacement (the superset rule). **Sharpens:** both need the coverage, here the bitlist, in the announcement, before the 200 KiB are fetched and verified.
- **Numbers:** none beyond entry 4.
- **Status:** quotes verified; the link to staggering is my inference.

### 6. Holding back on the strength of an announcement can be abused: a proof that is announced and never served blocks the alternative

- **Source:** https://ethresear.ch/t/26263/1 — cskiraly, 2026-11-18
  > An announced proof that the node never requests can still hold back the raw fetch. Skipping fetches on the strength of announcements would need an expiry and limits on repeated offers. We haven't tested those rules.
- **Bears on:** No displacement; Byzantine tolerance ("publish late or to some nodes only"); Redundant work. **Names a failure mode our list lacks:** a Byzantine aggregator announces coverage and withholds the proof, so that staggered honest aggregators stay silent. Silence is then not the worst a single aggregator can do (*inference*; the post is about raw transactions).
- **Numbers:** none.
- **Status:** quote verified.

### 7. With few aggregators a proposer can starve, and the relay rule that fixes it strands votes

- **Source:** https://ethresear.ch/t/26263/1 — cskiraly, 2026-11-18
  > With a quarter aggregating, none of the proposer's six neighbours aggregated on 5 of the 28 networks. The proposer starved on those networks unless relays forwarded only their best proof, the one covering the most live transactions. This rule is a heuristic for honest networks. It can strand a proof that covers transactions missing from the best proof.
- **Bears on:** Fair to proposers (first level of delivery); No displacement. **Supports** no displacement as a property of its own and gives a concrete forwarding rule that breaks it. See entry 20 for the same pattern in Horn.
- **Numbers:** 5 of 28 simulated networks; six peers per node.
- **Status:** quote verified.

### 8. Whether the interval holds depends on the prover, so the specification has to name the machine and say what a slower node does

- **Source:** https://ethresear.ch/t/26263/1 — cskiraly, 2026-11-18
  > EIP-8288 should name the prover its interval is set for and say what a slower node should do.
  > Spare compute or bandwidth alone did not help.
  > Each hop can cost up to one fold interval.
- **Bears on:** CPU load ("the hardware it assumes"); Latency; Fair to proposers. **Sharpens:** state the reference prover with the deadline, and the rule for a node that cannot keep it (take fewer inputs, in which order).
- **Numbers:** a 2-to-1 fold takes 303 ms on leanVM's M4 Max benchmark machine and 871 ms on four cores of a Ryzen 9 8945HS. Model prices: 25.9 ms per proof, plus 108.2 ms per nested proof, plus 1.667 ms per leanSPHINCS signature; verification 9.2 ms. A merge of 7 proofs: 783 ms against 2,252 ms. A newer leanVM (`e4dcb8d5`, 11 November) "reports 154 ms for a 2→1 fold in a different configuration". At the slower timing a 1,000 ms fold has room for its own aggregate and one peer's.
- **Status:** quotes verified.

### 9. A design with no assigned aggregators is on the table for the consensus layer: every node folds what it holds each tick

- **Source:** https://ethresear.ch/t/23838/1 — vbuterin, 2026-01-12
  > Post-quantum consensus-layer signature aggregation, to handle a large number of validators
  > Each node has extra inbound and outbound bandwidth equal to the size of one STARK per tick, multiplied by its number of peers […] This is constant, and does not increase as the number of objects that users send in grows.
- **Source:** https://ethresear.ch/t/17386/1 — asn, 2023-11-10
  > For networks with a big number of validators but a small number of networking nodes, gossip-based aggregation can be more efficient than a tree-based structure
- **Bears on:** Model (an aggregator is a role with a coverage set; A·d = S·k). **Names a design our list lacks.** Without duty holders there is nobody to silence, at a standing bandwidth and CPU cost for every node (*inference*). Our design space keeps secret and known aggregators, but no design without aggregators.
- **Numbers:** "with 8 peers and 500ms ticks, that's 128 kB * 8 / 0.5 = 2 MB/sec"; "in the consensus-layer aggregation case, this can be compressed down to 1 bit per participant". Measured in 26263/1 for transactions: a tenth of the nodes aggregating was enough at the loads tried ("Every share included at least 96.9% of transactions"). 17553 (entry 26) simulates the BLS version.
- **Status:** quotes verified.

### 10. Load figures for PQ Gasper published today: 64 aggregates per slot need 17.29 Mbit/s over 6 s, one subnet's votes 8.85 to 17.69 Mbit/s

- **Source:** https://ethresear.ch/t/26292/1 — jihoonsong, 2026-11-25
  > the current draft suggests that propagating PQ attestations and aggregates require substantially more bandwidth than it does under BLS.
  > disseminating PQ attestations and aggregates on time looks difficult even without IL traffic.
  > This back-of-the-napkin math didn't account for gossipsub's message duplication.
- **Bears on:** Bandwidth; attestation broadcast, Timely and Low load per node. **Supports** the open point under Timely with a second, public calculation. One copy per message, so a lower bound.
- **Numbers (read from the post's figures 8 and 9, which are images):** 202.626 kB per aggregate; 16, 32, 48, 64 aggregates per slot need 4.32, 8.65, 12.97, 17.29 Mbit/s over a 6 s window and 1.85, 3.71, 5.56, 7.41 over 14 s ("4s final aggregation time assumed"). Votes on one subnet, "32 slots per epoch · 16 subnets · 2,548 B per attestation": 17.69, 13.27, 10.62, 8.85 Mbit/s for windows of 1.8, 2.4, 3, 3.6 s at 800,000 validators, and 11.94, 8.96, 7.17, 5.97 at 540,000. For 16 inclusion lists with a recursive proof each, the post gets 42.88 Mbit/s over 1 s and proposes a one-slot delay or 8 lists instead of 16.
- **Status:** quotes verified; figure numbers read from the images, each row checked by multiplication.

### 11. Today's stack in practice: 826 aggregates per slot, not 1,024, and aggregates are already about a quarter of a default node's gossip bytes

- **Source:** https://ethresear.ch/t/26292/1 — jihoonsong, 2026-11-25
  > With 64 committees per slot and a target of 16 aggregators per committee, the nominal count is 1,024 aggregates per slot. In the three months of mainnet data shown in Figure 4, the median was 826 and the average was 826.13 aggregates per slot.
  > An attestation aggregate is 506 B, so 826 aggregates total about 418 kB per slot.
- **Source:** https://ethresear.ch/t/26078/1 — Nashatyrev, 2026-09-24
  > This came up while researching networking for Fast Finality, where attestation and aggregate traffic grows a lot, so we looked for ways to shrink it.
- **Bears on:** Baseline ("about 1,024 aggregators per slot"; the row "Bandwidth and CPU load", which reads "Not the constraint: making an aggregate takes no proof"). **Sharpens.** The post does not say why the count is 19 % under the nominal one. If it is the superset rule dropping covered aggregates, the number of aggregators is unchanged; if aggregators are missing, the baseline's 16 per subnet is nearer 13 (*inference*, undecided).
- **Numbers:** 0.84 Mbit/s over Fulu's 4 s window and 0.56 over Gloas's 6 s. Share of slots by aggregate count, 24 Aug to 23 Nov 2026 (figure 4, image): 700 to 799, 20.38 %; 800 to 849, 56.51 %; 850 to 899, 21.62 %; 900 to 999, 1.46 %; 1,000 and more, under 0.01 %. 26078/1, inbound gossip per hour on mainnet: default node 609 MiB, of which aggregates 138 MiB (23 %) and attestations 107 MiB (18 %); node on all subnets 5,601 MiB, of which attestations 3,188 MiB (57 %) and control messages 1,946 MiB (35 %).
- **Status:** quotes verified; the distribution is read from the image.

### 12. Decoupling takes finality votes off the latency-critical path; one reply estimates single-digit Mbit/s for 1M validators over 48 s

- **Source:** https://ethresear.ch/t/24418/1 — luca_zanolini, 2026-03-17
  > Finality still involves the full validator set, but it proceeds in parallel with the dynamically available component, off the critical path. The two layers do not compete for the same latency budget.
- **Source:** https://ethresear.ch/t/24418/3 — latifkasuli, 2026-03-20
  > with ~350 KiB proof objects, 1M validators, a 48s finality budget, and a simple two-layer topology (1024 local aggregates -> 32 regional aggregators -> root), peak per-node ingress stays in the single-digit Mbps range
  > proving cost and vote-accounting / bitfield structure may dominate instead.
- **Source:** https://ethresear.ch/t/26292/1 — jihoonsong, 2026-11-25
  > PQ Decoupled Consensus could smooth out bandwidth demand over time, thanks to the decoupling of the available chain and the finality gadget
- **Bears on:** Delivered, second level ("more relaxed in DC than in Gasper"); Bandwidth. **Supports.**
- **Numbers:** 6.6 Mbit/s peak ingress, 9.8 with 50 % retry overhead. This is a forum reply's own back-of-envelope, with no model published.
- **Status:** quotes verified.

### 13. Aggregation takes about log_C(validators) network rounds, where C is what one subnet can carry; the PQ example is C = 256

- **Source:** https://ethresear.ch/t/22856/1 — vbuterin, 2025-08-01
  > Where C is the capacity: how many signatures can be safely simultaneously broadcasted within a single subnet. It seems like realistic values for C are in the hundreds or low thousands. If we want to be quantum-resistant, we should assume more conservative numbers (eg. if a quantum-resistant signature takes up 3 KB and there's 256 of them per slot, that's 768 kB per slot, roughly similar to worst-case execution block sizes).
- **Source:** https://ethresear.ch/t/22856/18 — vbuterin, 2025-08-14
  > I was assuming a future based on STARK aggregation, where there isn't that much difference between 2-layer, 3-layer, etc.
- **Source:** https://ethresear.ch/t/17989/17 — vbuterin, 2023-12-28
  > you need O(log(N)) rounds of aggregation: 2 now, likely 3 with SSF with that many validators, and 1 with my cap-to-8192 proposal
- **Bears on:** attestation broadcast, Timely and the link "The subnet count comes from the other line"; Latency; Merge levels h. **Sharpens:** it puts a capacity figure on a subnet that is six times below the `pq` committee of 1,563, and it frames the number of levels as the latency unit.
- **Numbers:** "we allocate 4 seconds to each round of communication" (14219/1). "we can safely broadcast 512 signatures in about a second to the global network" and "broadcast and aggregate 35K attestations in about 6 seconds" (22856/7, potuz, 2025-08-08). A cap of N = 2^15, about 32k active validators, "which we know we can handle because it is the size of a committee today. If we wanted to completely remove attestation aggregation, we would likely need to drop this number to a few thousands." (19928/1, fradamt, 2024-06-28). "~28,000 today; 1,790,000 post-SSF" signatures per slot (17989/1).
- **Status:** quotes verified.

### 14. One bit per validator is the cost aggregation cannot remove, and a bitfield over the whole set in every merge is what an encoding independent of the topology costs

- **Source:** https://ethresear.ch/t/22856/8 — vbuterin, 2025-08-09
  > the only cost that cannot be cut through aggregation is the bitfield (1 bit per validator must be broadcasted globally).
- **Source:** https://ethresear.ch/t/17386/1 — asn, 2023-11-10
  > Note that merged signatures must have size linear to the number of signers, otherwise the GetSigners method would not be able to recover all the signers of a merged signature
- **Source:** https://ethresear.ch/t/24622/1 — muellerberndt, 2026-04-09
  > The cover used by aggregators has to be deterministic from the validator snapshot and protocol randomness. The merge tree has to be canonical.
- **Bears on:** Bandwidth (bytes per aggregate are proof plus bitfield); Also wanted, "Encoding independent of the topology". **Sharpens**, and 24622 is a proposal that goes the other way: it fixes the topology to shrink the object.
- **Numbers:** 24622/1, toy case with N = 131,072 validators in 64 patches: a full bitfield through 63 merges is about 1008 KiB against 1.97 KiB of overlap commitments. *My arithmetic:* a bitfield over 800,000 validators is 100 kB, about half a 200 kB proof; a bitlist over one `pq` committee of 1,563 is 196 B.
- **Status:** quotes verified. 24622 is one author's proposal and leans on an unrelated physics preprint; I use it only for the requirement it states.

### 15. The aggregate has to say exactly who signed, and has to keep supporting slashing after the raw signatures are gone

- **Source:** https://ethresear.ch/t/25040/1 — tcoratger, 2026-06-01
  > Because the consensus layer must know exactly who participated to process rewards, inactivity leaks, fork choice weight, and slashing, the aggregate payload includes both the leanVM proof and a signer bitfield
- **Source:** https://ethresear.ch/t/24622/1 — muellerberndt, 2026-04-09
  > A final aggregate must support later proofs of the form "validator v signed message m" or "validator v signed conflicting messages m and m'." Local commitments therefore need per-validator openings and retention long enough to cover slashing windows.
- **Source:** https://ethresear.ch/t/17386/1 — asn, 2023-11-10
  > Knowing the identity of the participants is essential for the Ethereum consensus because of slashing, staking rewards and the inactivity leak.
- **Bears on:** Integrity. **Supports** it, and 17386 gives the formal version: a Signature Merge scheme is unforgeable if nobody can produce a valid merged signature whose signer bitfield has an honest party's bit set unless that party signed. **Names something our list lacks:** accountability, meaning that who signed what stays provable for the slashing window once only proofs exist.
- **Numbers:** none.
- **Status:** quotes verified; the unforgeability definition is paraphrased from 17386/1, "Security of Signature Merge Schemes".

### 16. The signature size is still moving, and one MTU is the threshold its designers aim at

- **Source:** https://ethresear.ch/t/25040/12 — b-wagn, 2026-06-22
  > The main discussion here is not standard model vs ROM. It is if we can get signature sizes below one MTU. With the parameters presented here, we can't, but with more optimistic parameters, we can.
- **Bears on:** attestation broadcast, Low load per node and Timely. **Names a threshold our list lacks:** a vote that fits one packet. Our files say about 2.4 kB.
- **Numbers:** 3,112 bytes in June 2026 (25040/1: Merkle path 1,024, randomness 28, chain values 2,048). "leanSig ~1.2 KB" (26003/1, citing EIP-8292). 2,548 B per attestation (26292/1, figure 9). "With ~1 million validators each broadcasting a ~3.1 KiB signature, the bandwidth requirements for aggregators would easily exceed 3 GiB per slot" (25040/1).
- **Status:** quote verified. The three sizes come from three posts at three dates; which is current is for the specs to say.

### 17. A proof can cover votes that differ, so "proves every valid vote" is a real duty; a BLS aggregator only takes votes equal to its own

- **Source:** https://ethresear.ch/t/26152/1 — cskiraly, 2026-10-13
  > a proof handles signatures over different messages just as well, and it can compute over them.
  > Counts alone wouldn't do: view merge and discarding an equivocator's votes need to know who entered what.
- **Source:** https://ethresear.ch/t/13739/1 — fradamt, 2022-09-21
  > To be precise, they only aggregate attestations which agree with their own
- **Source:** https://ethresear.ch/t/22856/7 — potuz, 2025-08-08
  > The finality votes being separated from head are much more aggregatable.
- **Bears on:** "What an honest aggregator does", step 2; Complete; Loss unit. **Sharpens:** say whether one proof covers several vote values, and what its public output is (a bitlist per value).
- **Numbers:** 20020/1: about 150 missed target votes and 100 missed source votes per slot of about 32,000 (0.48 % for targets); "if their head vote is incorrect, it might result in the entire attestation being ignored by an aggregator".
- **Status:** quotes verified.

### 18. One proposed chain rule: every included aggregate merges the previous one on chain, and the proposer proves the total

- **Source:** https://ethresear.ch/t/25369/1 — vbuterin, 2026-07-06
  > We require each attestation (bitfield) to point to either the previous attestation for the same block, or the block itself, and include it in its STARK merge. Hence, each attestation's bitfield is the most up-to-date bitfield for the object it's applying to, OR'ing together any previous attestations and the new ones.
  > The proposer must prove a "total effective balance" for any objects in attestations included in their block
- **Bears on:** Recoverable, late inclusion; Fair to proposers; Integrity ("A vote counts once"). **Sharpens:** under this rule a late aggregate costs one more merge with what is on chain, by the proposer or the last merger, and the proposer has a proving duty of its own.
- **Numbers:** none.
- **Status:** quotes verified.

### 19. Valid votes with old targets have overloaded clients twice, and shedding them is safe only while the network is not forked

- **Source:** https://ethresear.ch/t/26236/1 — cskiraly, 2026-11-11
  > In May 2023, attestations with old targets made two clients regenerate the same old states again and again, and finality was delayed twice, by 4 and by 9 epochs.
  > Lighthouse stayed up because it dropped the attestations that would have needed the old states.
  > What to drop under overload, and when, is a question about the whole system.
- **Bears on:** Safety ("no honest node is overloaded"); Sybil resilience; attestation broadcast, Bounded spam; Recoverable (late inclusion widens the set of targets a node must accept). **Names something our list lacks:** the cost of validating late or old votes, which is not the proof check, and a rule for shedding load.
- **Numbers:** December 2025: "participation fell to about 75%, and finality held".
- **Status:** quotes verified.

---

## B. Requirements and failure modes from the aggregation posts of 2018 to 2024

### 20. Horn: when a merger keeps the "best" aggregate per subnet, one malicious aggregator displaces the honest ones

- **Source:** https://ethresear.ch/t/14219/1 — asn, 2022-11-16
  > Eve, a malicious aggregator (who also controls N validators) can always create the best aggregate by stealing the second best aggregate, removing N-1 honest public keys, and adding her own N public keys.
  > If Alice could aggregate overlapping bitfields, she could just aggregate all 16 bitfields into her collection, addressing any such attack, because she would always include some aggregate from a honest aggregator
  > It's worth pointing out that this attack is also possible in the current system since the proposer can always choose which attestations get included in the final block
- **Bears on:** No displacement; Censorship resistance ("kept out only if all k aggregators of its subnet censor"); the baseline's 0.002 %. **Contradicts** the k-fold protection wherever a merger or proposer picks one child per subnet by weight: one censor is enough. The baseline figure also leaves out the proposer, who "can always choose".
- **Numbers:** the post's appendix prices the attack: "N adversarial votes are required to censor N honest votes", in the same subcommittee. With leanVM children may overlap, so the fix exists, but merging all k proofs of a subnet uses k places of the fan-in instead of one (*inference*).
- **Status:** quotes verified.

### 21. Horn: replication multiplies the bytes on the global topic, and every aggregation layer costs a communication round

- **Source:** https://ethresear.ch/t/14219/1 — asn, 2022-11-16
  > We currently elect 16 aggregators to be almost certain that we will never end up without at least one honest aggregator. However, the number 16 acts as an amplification factor for the bandwidth in this proposal.
  > This proposal requires an additional round of communication for the new aggregation layer. At the moment, we allocate 4 seconds to each round of communication
  > adversaries can flood the P2P network with corrupted proofs that will cause the batch verification to fail.
- **Bears on:** "One honest aggregator is enough" (**supports**); Redundant work; Latency and merge levels; Sybil resilience ("cheap checks before the proof check"). The post asks the open question of our dispersed-assignment work: "Are there other election mechanisms we could use for collectors that would allow us to end up with less collectors?"
- **Numbers:** for 1M validators, one layer gives 2,048 subcommittees × 16 = 32,768 aggregates, about 8 MB on the global topic; Horn's second layer gives 512 collections, about 2.1 MB in 10 s. Verifying 512 collections with 2^15-bit bitfields: 2.8 s on an i9-11980HK, 6.1 s on an i7-8550U, 36 s on a Raspberry Pi. Nodes then moved "an average of 390KB/s when not subscribed to any subnets and 6-7MB/s when subscribed to all subnets". The design goal is stated as "minimizing the global topic bandwidth is a central part of this proposal".
- **Status:** quotes verified.

### 22. Signature Merging defines the interface, and notes that an operator with many validators can start from its own aggregate

- **Source:** https://ethresear.ch/t/17386/1 — asn, 2023-11-10
  > A Signature Merge (SM) scheme supports the recursive merging of signatures and their bitfields while still allowing the extraction of the signer set out of them.
  > in such a setting if Alice has 1000 validators she can start the protocol with a populated bitfield of weight 1000 without any prior communication. Furthermore the unstructured property of gossip-based approach can allow more privacy-friendly aggregation protocols.
- **Bears on:** Integrity (**supports**); Model, Machine ("one node can run many validators"); attestation broadcast, Low load per node and Anonymity enhancing. **Names something our list lacks:** aggregation at the source. An operator proves its own validators' votes before anything is gossiped, which takes raw signatures off the subnets and changes who counts as an aggregator. Our incentives proposal discourages exactly this ("little gain from aggregating your own votes").
- **Numbers (2023):** a recursive STARK proof of "about 300kb"; RISC0 took 2.5 seconds to verify 2 STARKs recursively, on an Nvidia A4000 GPU, "specialized hardware that validators normally don't have". In the post's Appendix A the last aggregator sends "his best merged signature" to the global topic, picked by weight: the select-best rule of entry 20.
- **Status:** quotes verified.

### 23. Today's chain accepts an aggregate from anyone: aggregators exist only at the p2p layer, so the proposer is already a fallback

- **Source:** https://ethresear.ch/t/13739/1 — fradamt, 2022-09-21
  > Today, aggregators are purely a p2p concept, absent both from the Beacon Chain spec and from the fork-choice spec. In practice, this means that blocks can include attestations which do not come from an aggregate, at least not an "official" one with a valid proof, as they look exactly the same to the Beacon Chain.
- **Bears on:** Recoverable, Fallback; Baseline (the table has no row for it); Sybil resilience. **Sharpens:** the baseline has a permissionless fallback at inclusion. Whoever holds the raw votes can aggregate them at almost no cost, and the gate on senders exists only on the gossip topic. Under PQ the same fallback needs a prover.
- **Numbers:** `TARGET_AGGREGATORS_PER_COMMITTEE = 16`, "sufficient to ensure a high probability of there being at least one honest aggregator in every subnet"; about 200 validators per committee at the time.
- **Status:** quote verified.

### 24. An aggregator can publish two valid aggregates for one slot; the first-seen rule bounds the load but splits views

- **Source:** https://ethresear.ch/t/13739/1 — fradamt, 2022-09-21
  > An aggregator can produce two valid aggregates for the same slot, differing in the attesting indices, without there being any equivocation in the underlying attestations. The way we deal with this today is first-seen, i.e., only the first aggregate from any given aggregator is accepted and forwarded, to prevent a DoS vector.
  > an aggregator could aggregate attestations that no one else has access to in unaggregated form, e.g. their own, so that anyone not processing such an aggregate necessarily has a different view from all who do.
  > Since equivocating as an aggregator cannot lead to double-finality, an option could be to not punish it with slashing, but only with a forced exit.
- **Source:** https://ethresear.ch/t/26292/1 — jihoonsong, 2026-11-25
  > nodes that detect equivocation could drop the two equivocating ILs and broadcast an IL equivocation proof
- **Bears on:** Sybil resilience ("one aggregate per aggregator and epoch"); No displacement; the Byzantine type ("publish many proofs"). **Sharpens:** under one proof per aggregator, a Byzantine aggregator decides which of its proofs each node keeps, and a vote found only in the other is displaced at those nodes. **Lacks:** a rule for aggregator equivocation (evidence gossiped, sender ignored or exited).
- **Numbers:** references to one slot's aggregates take 16 × 64 × 32 B = 32 KB. 26292/1: "In the worst case, IL bandwidth consumption can double if all includers equivocate"; an equivocation proof saves "up to 616 kB".
- **Status:** quotes verified.

### 25. Choosing which aggregates to include is a maximum-coverage problem, and the advice of the BLS years is that aggregators should not wait for one another

- **Source:** https://ethresear.ch/t/7265/10 — michaelsproul, 2021-08-30
  > They shouldn't wait until other aggregators have sent them aggregates, and as such shouldn't be solving difficult optimisation problems at aggregation time.
  > You need to select up to k attestations from all subnets, and sometimes multiple aggregates from the same subnet if they overlap and this is the most profitable thing to do.
- **Bears on:** Merge ("16 children that leave some subnets out"; after failures the merger mixes layers); Redundant work. **Sharpens:** picking at most m children for the most coverage is the maximum-coverage problem that clients approximate today when they pack a block. The opening post of the topic calls attestation aggregation "NP-Complete" and cites an approximation ratio of about 0.6 for maximum coverage. **In tension** with the `pq` spec's staggered aggregators, who do wait.
- **Numbers:** the budget was `MAX_ATTESTATIONS_PER_BLOCK` = 128; about 16 aggregates per subnet to choose among.
- **Status:** quotes verified.

### 26. The 2023 flooding proposal lists four requirements, and calls the loss of a whole committee's aggregators negligible because it is 1 of 64

- **Source:** https://ethresear.ch/t/17553/1 — jtapolcai, 2023-11-28
  > If an attacker were to successfully suppress every aggregator node in a given committee, it would result in the loss of all signatures gathered by that committee. Given that there are 64 committees, the impact of such an attack is negligible in the consensus process.
  > without revealing the IP addresses of the validators
  > has a succinct proof about the supermajority on the chain
  > being resilient against malicious nodes.
- **Bears on:** DoS resilience, outcome "one vote"; Loss unit. **Supports** the loss unit as a property: the argument works at 1/64 and is four times weaker at the `pq` spec's 1/16. **Lacks:** an on-chain cost per vote; the post tracks "chain cost per ID".
- **Numbers:** the fourth requirement is bandwidth of about 8 GB per day. Chain cost today about 2 bits per validator. Simulation on a crawled topology of 9,294 nodes with 800,000 validators, every node merging and forwarding: with 14 random neighbours it "consumes 6.16 GB per day, and achieves 86% finality in 12 seconds" (reply 5; the charts count nodes that have seen a supermajority). Messages are scored by bits per new signer and dropped when they add none.
- **Status:** quotes verified.

### 27. Committees are not sampled by balance, so subnets differ in weight once balances differ

- **Source:** https://ethresear.ch/t/15547/1 — adiasg, 2023-05-10
  > However, the sampling for committees is not weighted by the effective balance. Increasing MAXIMUM_EFFECTIVE_BALANCE would allow for large differences between the total weight of committees.
- **Bears on:** Model ("A subnet's weight is the stake of its validators"); DoS resilience, outcome "finality", t(q) and the baseline's "22 neighbouring subnets". **Sharpens:** figures that count subnets as equal are upper bounds; an adversary that knows the draw takes the heaviest subnets first (*inference*).
- **Numbers:** in 2023, "About 50% of the current 560,000 validators are controlled by 10 entities".
- **Status:** quote verified.

### 28. Measured propagation on a subnet today: two thirds of the votes within 0.83 s, the 95th percentile at about 2 s

- **Source:** https://ethresear.ch/t/23016/1 — misilva73, 2025-09-03
  > Attestations for missed slots, which reveal pure propagation times, arrive on average 831ms after the 4s mark. Subnet supermajorities form in under 830ms, while the 95th percentile takes 1962ms.
  > Validator entities are the strongest drivers of late attestations.
- **Bears on:** attestation broadcast, Timely (the aggregator's cutoff, and so the definition of a timely vote) and Fair vote timing. **Sharpens:** a cutoff under 2 s after the vote deadline leaves out more than 5 % of votes at today's message size (*inference* from the 95th percentile).
- **Numbers:** 95th percentile over all attestations 2,066 ms, and 1,782 ms after one operator fixed a misconfiguration. In ordinary slots, with a cutoff at 4.5 s, the aggregation deadline proposed for 6 s slots, "Late arrivals account for 11.1% of all attestations". The post calls its figures "likely an overestimation", because in a missed slot everybody sends at once. These are BLS votes; a PQ vote is roughly ten times the bytes (*my estimate*).
- **Status:** quotes verified.

### 29. Rational attesters delay their votes, and one proposed remedy makes aggregators the judges of timeliness

- **Source:** https://ethresear.ch/t/17612/1 — casparschwa, 2023-12-05
  > In response to late proposals, rational attesters may delay their attestation deadline to vote accurately.
- **Source:** https://ethresear.ch/t/17612/5 — Nero_eth, 2023-12-06
  > maybe letting the aggregaters categorize attestations into early and late attestations that come with different payouts.
- **Bears on:** attestation broadcast, Timely and Fair vote timing; Incentive compatibility; Censorship resistance. **Lacks:** a rational *attester*; our types describe aggregators only. If aggregators grade timeliness, a censoring one can cut a validator's yield without leaving its vote out. A finality vote in DC has no head component, so there is less to gain from waiting (*inference*).
- **Numbers:** none.
- **Status:** quotes verified.

### 30. Late inclusion needs room on chain: today half of the proposals can fail and an epoch's votes still fit, and many late inclusions are repeats

- **Source:** https://ethresear.ch/t/7547/6 — djrtwo, 2020-06-18
  > there is enough room for an epoch's worth of attestations (in most cases) even if 50% of proposals fail. We can make this number better (at the cost of bigger/more expensive blocks by increasing MAX_ATTESTATIONS to 256).
- **Source:** https://ethresear.ch/t/20020/1 — Nero_eth, 2024-07-09
  > almost half of the attestations included with a delay of 2 slots (note: best is 1) have already been included in an earlier slot.
- **Bears on:** Recoverable, late inclusion; Redundant work. **Sharpens:** late inclusion is bounded by the proofs a block may carry. Under PQ a vote included twice costs proof bytes or a merge, so "A vote counts once" needs a rule on who pays for the second time.
- **Numbers:** 20020/1: "a block can contain the same attestations multiple times, aggregated differently".
- **Status:** quotes verified.

---

## C. Attack models

### 31. The aggregator duty is visible in practice: a node subscribes to one more subnet for the epoch in which it aggregates

- **Source:** https://ethresear.ch/t/19920/1 — jonasbostoen, 2024-06-27
  > Remember that in theory, only attestation aggregators need to be listening to all incoming attestations in order to do their jobs.
  > This means that on average, there will only be 16 validators per committee that will be subscribed to an additional short-lived subnet for the duration of an epoch
- **Source:** https://ethresear.ch/t/20463/1 — liobaheimbach, 2024-09-20
  > the validators hosted on the peer are occasionally tasked with being aggregators in a subnet approximately every 30 epochs per validator. During these times, they temporarily become a backbone (smaller pink horizontal strips) for these subnets
- **Bears on:** DoS resilience, "Aggregators secret" ("as long as nothing leaks"). **Contradicts** the baseline's secret-regime row as a description of today: two measurement studies use the leak as their method, and the subscription lasts an epoch, so it can be seen before the slot. Today's stack sits between the two regimes.
- **Numbers:** 20463/1: over 15 % of validators located in three days with four nodes; about 90 % of them at cloud providers; "On average, we observe 678 validators on a given peer for staking pools, with the largest node running 19,263 validators"; for a proposer "this attack only needs to last for four seconds", by "DoS or BGP hijack". 19920/1 can count at most 62 validators per node this way. 20463's own mitigation, subscribing to more subnets all the time, hides duty joins; an aggregator that joins d subnets for one duty shows more (*inference*, consistent with the note in our file).
- **Status:** quotes verified.

### 32. Anonymity sets have to be counted in nodes, and Whisk's author says a blind attack on every candidate node could be doable

- **Source:** https://ethresear.ch/t/11763/1 — asn, 2022-01-13
  > we find that an anonymity set of 8,192 validators corresponds to 2,108 nodes on average.
- **Source:** https://ethresear.ch/t/11763/8 — asn, 2022-05-16
  > even with SSLE, an attacker can indeed enumerate and blind-DDoS the entire set of home stakers. Given the current network size, and assuming a strong adversary, this could even potentially be doable.
  > if validators use separate IPs for attestations and proposals, then an adversary wouldn't even know what's the IP address to DoS.
- **Source:** https://ethresear.ch/t/3912/8 — nikkolasg, 2018-10-26
  > one only needs to advertise the ip address used to collect aggregated signatures, and diffuse one's own contribution from anywhere.
- **Bears on:** DoS resilience, secret regime, and the count in machines. **Supports** counting machines, not validators, with a method (a Pareto spread, "20% of the nodes run 80% of the validators"). **Sharpens:** the blind budget is an upper bound that Whisk's author already treats as within reach of a strong adversary. A mitigation our list lacks: a separate address for the duty.
- **Numbers:** 250,000 validators on about 5,000 nodes in 2022. Topic 3912 is the thread of the Handel authors, before the name; reply 7 there raises the cost of structure: "There would have to be a way to connect to specific validators which makes them vulnerable to DoS attacks."
- **Status:** quotes verified. That 3912 is the Handel precursor is my inference from its authors.

### 33. Precedent for a hybrid: a public primary with secret probabilistic backups, and the two incentive problems it creates

- **Source:** https://ethresear.ch/t/7633/1 — djrtwo, 2020-07-03
  > SPBE probabilistically selects a set of backup proposers via a local secret that can be proven in the block proposal
  > We might worry that it becomes rational for a backup proposer to eagerly create and broadcast backup proposals at the start of any selected slot rather than waiting to see if a backup is actually needed.
  > We might worry that it becomes rational for a backup proposer to attack the leader to increase the backup proposer's chance for inclusion in the canonical chain.
- **Bears on:** DoS resilience (our two regimes are alternatives; this mixes them); Recoverable, Fallback; Redundant work; Incentive compatibility. **Names a design our list lacks:** known aggregators plus secret backups that publish only when the known ones are late.
- **Numbers:** backups publish at 1/6 of the slot, and gossip drops them earlier or once the leader's block is seen; reward "PROPOSAL_REWARD // BACKUP_DISCOUNT_FACTOR where BACKUP_DISCOUNT_FACTOR >= 2". The selection is "very similar" to `is_aggregator`. A secret PQ lottery has a price: the PQ VRF of 24906/1 has a 116 KB proof, 81 ms to prove and 19.2 ms to verify. That post is about the proposer's RANDAO reveal; applying it to aggregators is my inference.
- **Status:** quotes verified.

### 34. Motives the adversary model lacks: a validator gains from silencing the duty holder before it, and public duty holders can be bribed

- **Source:** https://ethresear.ch/t/7633/2 — jrhea, 2020-07-03
  > if I know that I am the next to propose a block, then stopping the current block proposer could allow me to be rewarded with more attestations or slashings than would have been available.
- **Source:** https://ethresear.ch/t/20463/1 — liobaheimbach, 2024-09-20
  > the incentive for the proposer of slot n+1 to prevent the proposer of slot n from publishing a block.
- **Source:** https://ethresear.ch/t/24527/1 — fradamt, 2026-03-28
  > This way, the committee members are only known when they have already acted, which protects against an adaptive adversary (bribing, targeted DoS...)
- **Bears on:** Network adversary ("holds no stake and no keys"); the Rational type; Incentive compatibility; Recoverable. **Sharpens:** silencing can be a rational move, not only a Byzantine one, and it pays more with late inclusion, where votes nobody has included yet are the most valuable ones (*inference* from our incentives proposal). **Lacks:** bribery of known aggregators.
- **Numbers:** none.
- **Status:** quotes verified.

### 35. Secrecy erodes over repeated duties, and anonymity at the network layer has so far failed on latency, a constraint that decoupling loosens

- **Source:** https://ethresear.ch/t/25343/5 — kamilsa, 2026-07-16
  > This means that even fairly low per message deanonymization attack accuracy gives limited protection when the same validator produces the message on a regular basis
- **Source:** https://ethresear.ch/t/12698/1 — blagoj, 2022-05-22
  > However because of latency constraints we've come to a conclusion that this proposal is infeasible for the Ethereum consensus layer (at least not for any strong anonymity guarantees).
- **Source:** https://ethresear.ch/t/10664/1 — blagoj, 2021-09-09
  > Because in private p2p networks it's not clear who to block in response to spam.
- **Bears on:** attestation broadcast, Anonymity enhancing; DoS resilience, secret regime; Sybil resilience. **Sharpens:** secrecy has to be judged over many duties, and hidden senders pull against a bounded sender set. 12698 names the way out itself: "except other changes are made at the consensus layer which relax the latency constraint", which is what DC does for finality votes (*inference*).
- **Numbers:** 25343/5: at 20 % accuracy per epoch with 5 % curious nodes, 90 % after 10 to 11 epochs. 12698/3: Dandelion++ adds "300ms added per stem hop on average" and "2.5 seconds for the fluff phase initiation".
- **Status:** quotes verified.

### 36. A withholding aggregator cannot be told from a slow network; this has been said since 2018

- **Source:** https://ethresear.ch/t/1659/9 — NicLin, 2018-04-28
  > Seems to me there's no way to distinguish a vote being ignored and a vote that's only signed after?
- **Source:** https://ethresear.ch/t/13739/1 — fradamt, 2022-09-21
  > such adversarial behavior is not distinguishable from high latency.
- **Source:** https://ethresear.ch/t/22856/19 — kladkogex, 2025-09-14
  > the problem with aggregation is that a malicious aggregator may just refrain from doing its job.
- **Source:** https://ethresear.ch/t/24622/1 — muellerberndt, 2026-04-09
  > A malicious aggregator could withhold one small overlap opening and stall a merge.
- **Bears on:** Censorship resistance ("Nothing here relies on catching the censor"); Silent. **Supports.**
- **Numbers:** none.
- **Status:** quotes verified.

---

## D. Incentives

### 37. Today an aggregator's only reward is getting its own vote included; nothing pays for the duty

- **Source:** https://ethresear.ch/t/13739/1 — fradamt, 2022-09-21
  > this is the only incentive which they currently have to perform their aggregation duty, since it's not rewarded in the Beacon Chain.
- **Source:** https://ethresear.ch/t/20907/8 — AgeManning, 2024-11-06
  > If they didn't aggregate they might not get their attestation included into a block which is a financial loss. So they are incentivized to aggregate.
- **Source:** https://ethresear.ch/t/13044/1 — OisinKyne, 2022-07-12
  > Aggregations are not currently directly rewarded nor punished in protocol, rather their absence would indirectly affect the participation rate for a slot.
- **Source:** https://ethresear.ch/t/20907/10 — AgeManning, 2024-11-08
  > they are unlikely to include your sole attestation as they can profit more from including aggregate attestations with more validator signatures.
- **Bears on:** Incentive compatibility; the baseline's row on it. **Sharpens:** the baseline does have an incentive, an indirect one, and it is the one our incentives proposal removes ("little gain from aggregating your own votes"). Under PQ the duty costs a proof, so the gap is wider. A proposer packs by signature count, so small aggregates lose their place first.
- **Numbers:** none.
- **Status:** quotes verified.

### 38. Calls to pay for aggregation and for inclusion exist; none is worked out

- **Source:** https://ethresear.ch/t/25040/1 — tcoratger, 2026-06-01
  > Aggregator economics: Who bears the computational cost of SNARK proving? Should aggregation be compensated via protocol rewards?
- **Source:** https://ethresear.ch/t/17989/13 — OisinKyne, 2023-12-28
  > Make aggregations attributable and economically rewarded/punished in protocol such that they are more respected.
- **Source:** https://ethresear.ch/t/25369/6 — vbuterin, 2026-07-08
  > I agree with this, we would need to explicitly reward the proposer.
- **Source:** https://ethresear.ch/t/26263/1 — cskiraly, 2026-11-18
  > The model leaves out incentives to aggregate and concentrations of aggregators at builders or gateways.
- **Bears on:** Incentive compatibility. **Supports** "open". The third quote is about including validators' balance-update proofs, which a rational proposer would skip, not about vote aggregates.
- **Numbers:** none. Pointers: 26236/1 links an off-forum note, "Paying the mempool workers", that I did not read. 21429/1 (AmbitionCX, 2025-01-12) proposes to reward only the votes inside the final quorum certificate, so that "becoming an aggregator and participating in the aggregation process can significantly increase the possibility of earning benefits".
- **Status:** quotes verified.

---

## E. Adjacent requirements

### 39. The aggregator lottery is one of the places that blocks distributed validators, and native DVT would assign roles to all of a validator's identities together

- **Source:** https://ethresear.ch/t/13044/1 — OisinKyne, 2022-07-12
  > the current method for the selection of aggregators from committees prevents us from implementing DVT as a convenient middleware solution.
- **Source:** https://ethresear.ch/t/23894/1 — vbuterin, 2026-01-20
  > This creates n "virtual identities" that all follow the protocol fully independently, but are always assigned to roles (proposer, committee, p2p subnet) together.
- **Bears on:** Model, Machine (several roles on one machine is in the model; one role on several machines is not); DoS resilience. **Lacks:** a selection rule that a distributed validator can run. 23894/1 adds that today's DVT depends "on the linearity property of BLS, which is exactly the property that makes it not quantum-secure".
- **Numbers:** up to n = 16 identities per validator with a threshold m.
- **Status:** quotes verified.

### 40. The transport under all of this has no post-quantum plan yet

- **Source:** https://ethresear.ch/t/26183/1 — adust09, 2026-10-27
  > Ethereum consensus-layer networking has no adopted post-quantum migration profile.
- **Bears on:** Network adversary ("It cannot forge", holds no keys); Sybil resilience, which rests on peer identity and scoring. **Lacks:** peer identity and channel security against the same adversary that motivates the PQ signatures.
- **Numbers:** an ENR is at most 300 bytes and a Discovery v5 packet 1,280 bytes; an ML-DSA-44 public key is 1,312 bytes and its signature 2,420 bytes.
- **Status:** quote verified.

---

## Requirements or properties stated in the source that our list lacks

1. **Accountability.** Who signed what stays provable for the slashing window once only proofs exist (15).
2. **A rule for aggregator equivocation.** Two valid proofs from one aggregator for one slot (24).
3. **Parameters of proof propagation.** Mesh degree of the proof topics, push or fetch, and coverage in the announcement (4, 5), with the withheld-announcement attack that fetch brings (6).
4. **A reference prover with the deadline,** and what a slower node does; merge cost as a step function, not a fan-in constant (3, 8).
5. **Designs outside the model.** No assigned aggregators at all (9); aggregation at the source by operators with many validators (22); known aggregators with secret backups (33).
6. **Rational attesters,** who choose when to send (29), and **rational silencing and bribery** of known duty holders (34).
7. **Overload from valid votes** with old targets, and a load-shedding rule (19).
8. **Unequal subnet weights** (27).
9. **On-chain cost per vote** and the one-bit-per-validator floor (14, 26); room on chain for late inclusion and a rule against paying for a vote twice (30).
10. **Votes that differ inside one proof,** and the proof's public output (17).
11. **One packet per vote** as a size threshold (16).
12. **Selection that distributed validators can run** (39).
13. **Post-quantum peer identity and channels** (40).

## Places where the source contradicts our list

1. **Stake-weighted draw of aggregators** against an "opt-in, higher-specification" aggregator role in EIP-8292, as 26003 describes it (1). Secondary source; check the EIP.
2. **A vote "kept out only if all k aggregators of its subnet censor"** against Horn: where one aggregate per subnet is picked by weight, one malicious aggregator displaces the others, and the proposer "can always choose" (20). The baseline's 0.002 % leaves the proposer out.
3. **Merge fan-in m = 16** against a measured cliff after 5 children on a low-end machine (3).
4. **Baseline of about 1,024 aggregators per slot** against 826 aggregates observed per slot on mainnet (11). Cause not stated.
5. **Aggregators that stay secret "as long as nothing leaks"** against two studies that locate validators by the aggregator's extra subscription, held for an epoch (31).
6. **"With acceptance gated to assigned aggregators a fallback covers nothing"** is true of gossip, but today's chain takes aggregates from anyone, so the baseline has a fallback through the proposer (23).
7. **Encoding independent of the topology** against the bit-per-validator floor and a proposal that fixes a canonical cover and merge tree to cut the encoding (14).
8. **Staggered aggregators that wait** against the advice that aggregators "shouldn't wait until other aggregators have sent them aggregates" (25), and against the abuse of announcements (6).
9. **Votes of about 2.4 kB** against 3,112 bytes (June 2026), about 1.2 KB (as cited from EIP-8292) and 2,548 B per attestation (today's FOCIL post) (16).

## Searches that found nothing

Discourse search matches terms, so "nothing" means no post on the subject among the results, not proof of absence.

- **Handel.** `Handel protocol signatures`: 0 results. `Handel aggregation`: one unrelated mention. No topic carries the name; topic 3912 is its authors' earlier thread (32).
- **Naive aggregation as a strategy.** `naive aggregation attestation` and `attestation aggregation strategies` returned nothing on the subject. Topic 7265 (entry 25), which other searches found, is the only one on aggregation strategies.
- **A topic on EIP-8292 or on PQ attestation aggregators.** `EIP-8292`: two posts that mention it (26227, 26003), none about it.
- **Post-quantum Gasper.** `post-quantum Gasper`: only today's FOCIL post (26292) is relevant.
- **Lean consensus aggregation topology.** `lean consensus aggregation`, `leanSpec devnet aggregation`, `aggregation topology`, `aggregation subnets proofs`: no topic. The nearest statement is 26227's citation of a survey that lists optimal aggregation-tree construction as an open problem.
- **Aggregation through builders or blobs.** `aggregation builders attestations`, `builders aggregate attestations proofs`, `attestations blobs aggregates`, `attestations in blobs`: none of the 200 results is about carrying attestation aggregates through builders or blobs, judging by titles and matched excerpts; I did not open them all.
- **Lazy aggregators.** `lazy aggregator`: nothing relevant; only the remarks in entry 36.
- **Paying aggregators.** `aggregator incentives reward`, `aggregator duty reward`: no dedicated topic; only the remarks in entries 37 and 38.
- **Denial of service on aggregators.** `aggregator DoS`: no dedicated topic; one exchange in topic 7547 (replies 11 and 12: "Seems like aggregators could be DOSed similarly to proposers", answered with the private lottery).
- **Spam on attestation topics.** `attestation spam gossipsub`: 5 results, none on the subject.
- **leanSig, leanMultisig.** Mentions only (24906, 26003, 24622, 24418); no topic on their networking.
