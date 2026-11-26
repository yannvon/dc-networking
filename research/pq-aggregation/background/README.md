---
title: Background from public sources, for the broadcast properties
status: research notes
date: 2026-11-25
provenance: agent
---

> **Provenance: agent.** Written 2026-11-25 by the oversight thread of the [PQ aggregation strategy](../README.md) workstream. Yann asked that day for background from consensus-specs, ethresear.ch and the Eth R&D Discord, to improve the properties. Three research subagents wrote the three notes of this folder, and the oversight thread checked them and worked them into [`properties/`](../../../properties/README.md). Yann has not reviewed any of it.
> - What a source means for a property is an agent's reading throughout. The quotes are the sources' own.
> - Nothing here changes a property tagged `human`. Where a source disagrees with one, the property stays and the source is written next to it, tagged `external`.
> - **After Yann's answers of 2026-11-26.** He named the reference spec for decoupled consensus, kept the five properties below, and said which blobs he means. The last section records the answers. The three notes were written a day earlier and are unchanged: their entries on decoupled consensus (specs 29 to 32) describe the upstream branches, not the reference.

# Background from public sources

**What this is.** What the people who built today's aggregation, and those who are building the PQ one, said about the properties we want from attestation and aggregation broadcast. It is the source of every item tagged `external` in [`aggregation-broadcast.md`](../../../properties/aggregation-broadcast.md) and [`attestation-broadcast.md`](../../../properties/attestation-broadcast.md).

## The three notes

| Note | Source, as read | Entries |
|---|---|---|
| [`consensus-specs.md`](consensus-specs.md) | `ethereum/consensus-specs`: `master` at `d2021d2`, branches `pq` at `4c29678`, `decoupled-consensus` at `0f4fa3f` and `pq-dc` at `bde2349`, with issues, pull requests and commit messages. `fradamt/consensus-specs`, branch `simplex-healing`, at `5750e57` | 36, cited as "specs 1" to "specs 36" |
| [`eth-rnd-discord.md`](eth-rnd-discord.md) | [ethereum/eth-rnd-archive](https://github.com/ethereum/eth-rnd-archive) at `18a6ec3`, the public archive of the Discord up to 2026-11-25 | 40, cited as "discord F1" to "discord F40" |
| [`ethresearch.md`](ethresearch.md) | ethresear.ch: 58 topics downloaded after 45 searches | 40, cited as "ethresear.ch 1" to "ethresear.ch 40" |

Each entry gives the source with a link, the quote, what it bears on, and the numbers. Each note ends with three lists: what the source asks for that our properties lack, where it contradicts them, and what was searched for and not found.

## How it was checked

There are three layers, and none of them is a review by a person.

1. **By the subagents, against the sources.**
   - Discord: a script found all 193 quoted fragments in the cited file at the cited message, and all 108 links resolve.
   - ethresear.ch: a script found all 109 quotes in the downloaded posts.
   - consensus-specs: every quote was read at the link given, with no script.
2. **By the oversight thread, against the sources, on a sample.** 44 fragments from 24 entries of the specs note, 30 from 22 of the Discord note and 24 from 21 of the ethresear.ch note. All were found. The header of each note says so.
3. **By the oversight thread, between the properties and the notes, in full.**
   - It read the three notes from end to end against the properties.
   - [`check_citations.py`](check_citations.py) finds every quote of an `external` item in an entry cited right after it: 102 quotes behind 204 citations in the two property files, none missing. The same holds for the 13 citations in the workstream's [index](../README.md). It reports a changed quote or a wrong entry number, which was tried.
   - Since 2026-11-26 the same script also checks quotes cited by a file at a commit with a line range, against a local clone that has the commit. That covers the items that quote the reference spec, its upstream branch, EIP-8256, EIP-8292 and the draft of EIP-8453: 61 such quotes in the two property files and the blob note, all found, in a clone that has both `ethereum/consensus-specs` and `ethlabs-org/consensus-specs`, and one of `ethereum/EIPs`. Without a clone it counts them as not checked.
   - It read again, at the commits, the spec passages that a new statement rests on:
     - the gossip rules of the `pq` branch at `4c29678`: exactly one committee, the superset rule, one aggregate per aggregator and epoch;
     - its hash tree of per-slot secrets;
     - the date of commit `e26cc6f`;
     - the EIP-8453 branch's "Aggregates combine the attestations of several committees", and its TODOs;
     - the two Simplex rules on aggregates;
     - the state and base branch of pull requests 5856 and 5863.
   - On 2026-11-26, after Yann's "check also /ethereum/consensus specs", it read upstream's `pq-dc` at `bde2349` next to the reference, for every item that says "reference spec". Items that hold on Francesco's branch only now say "Not upstream", and [`specs/README.md`](../../../specs/README.md#where-upstream-differs) has the comparison. The upstream quotes are among the 61 above.

To run the script again, from the repository root:

```sh
python3 research/pq-aggregation/background/check_citations.py \
    properties/aggregation-broadcast.md properties/attestation-broadcast.md \
    research/pq-aggregation/README.md research/pq-aggregation/blob-propagation/README.md \
    --clone <consensus-specs> --clone <EIPs>
```

The clones need the commits that the files cite. For consensus-specs that is one clone with both `ethereum/consensus-specs` and `ethlabs-org/consensus-specs` as remotes, or two clones. For EIPs it is `ethereum/EIPs` after `git fetch origin refs/pull/12566/head`, which brings the draft of EIP-8453.

**What the checks do not cover.** One quote that is cited by a direct link and not by an entry (ethresear.ch topic 7547, in the aggregation file's point on where today's stack sits). Whether a paraphrase is fair, and whether a number that is not inside a quote is the source's: the oversight thread read those and no script did. Figures that a subagent read from images (ethresear.ch entries 10 and 11) were read by that subagent only; it checked the rows of entry 10 by multiplication. Images posted on the Discord were not read at all.

## Where the oversight thread reads a source differently

- **How the `pq` spec picks aggregators, and its gossip rule** (discord F23, F26, F33). The messages describe drafts. At the tip, `4c29678`, the aggregators come from committees kept in the state, since commit `e26cc6f` of 17 November, and gossip has only the superset rule. The rule that forwarded only a heavier aggregate lasted one day (specs 26). So F26 is cited nowhere.
- **A private lottery on a hash tree** (discord F33). The tree exists at the tip and serves the RANDAO reveal. The spec does not use it for aggregators. The properties file records it as a building block for the secret regime, not as a contradiction.
- **An opt-in aggregator role** (ethresear.ch 1). The entry is a second-hand description of EIP-8292. The oversight thread read the EIP itself on 2026-11-26, at `6889815`, and it says the same: "A node MAY opt in as an aggregator", with no stake threshold. It is a draft for the lean consensus spec. The `pq` spec draws its aggregators from all validators, and the reference spec leaves selection open. Five items in the aggregation file quote the EIP.
- **Nodes per subnet** (specs 10 against discord F19). The 500 of 2023 predates the rule that puts a node on 2 of 64 subnets. The 400 to 500 of 2025 comes from 13,000 nodes under that rule. Both are in the properties, and Yann's figure stands.
- **Announce and withhold** (ethresear.ch 6). The post raises it for raw transactions in a mempool and says that no rule against it was tested. The step to aggregators is the subagent's.
- **Why every node is on the aggregate topic** (specs 21). The quote is about the sync committee's topic. Discord F10 has the reason for attestation aggregates.

During the full read, eight sentences of the first integration said more than their entry, and were tightened. Three examples: one reviewer's remark that had become "its reviewers"; an untested attack that had become "measured"; and two Simplex rules on two topics that had been merged into one.

## What went into the properties

`external` marks 107 places in the aggregation file and 25 in the attestation file. 89 and 19 of them were written from the three notes on 2026-11-25, and 113 of the 116 entries are cited. The other 18 and 6 give what the reference spec, the blob streaming draft and EIP-8292 say, and were added on 2026-11-26.

**Properties that the sources state and the file lacked** (all in [`aggregation-broadcast.md`](../../../properties/aggregation-broadcast.md), each tagged `external`):

| Property | In one line | Entries |
|---|---|---|
| Reach | Every vote sent on time reaches an aggregate, with everyone honest | discord F14, F23 |
| Accountable | Who signed what stays provable when only proofs are left | ethresear.ch 15, 14 |
| Equivocation evidence travels | Gossip forwards a second, different message from the same sender | specs 32; ethresear.ch 24 |
| Tolerates missed proposals | Finality with 80 % of blocks missing, counted in slots of backlog | discord F32 |
| Degrades gracefully | Work that is half done still counts | discord F38 |

**By section of the aggregation file.** Places written from the three notes. The items added on 2026-11-26 for the reference spec, blob streaming and EIP-8292 are not counted.

| Section | Tagged places | specs | discord | ethresear.ch |
|---|---:|---|---|---|
| Model: votes and time | 13 | 10, 23, 25, 30, 31, 33, 36 | F14, F19, F21, F35, F37, F38 | 12, 27 |
| Model: aggregators | 4 | | F22, F28, F31 | 1, 3, 9, 17, 22 |
| Types of aggregator | 1, with 5 points | 14 | F31 | 6, 24, 29, 34 |
| Network adversary | 1, with 5 points | 11, 14 | F8, F11, F39 | |
| Baseline: today's p2p stack | 12 | 1, 2, 3, 5, 7, 12, 13, 15, 16, 17, 21 | F1, F2, F10, F12, F13, F14 | 11, 20, 23, 31, 37 |
| Safety | 11 | 4, 18, 20, 27, 29, 32, 34, 35 | F5, F17, F22 | 5, 14, 15, 19, 22, 24 |
| Liveness, with no displacement and loss unit | 4 | 6, 26 | F4, F18, F27 | 7, 20, 21, 26 |
| Complete and Reach | 2 | | F10, F14, F23, F34 | |
| DoS resilience | 8 | 3, 5, 12, 14, 19, 24, 28, 30 | F1, F3, F20, F23, F24, F33 | 31, 32, 33, 35 |
| Censorship resistance | 3 | | F36 | 20, 29, 36 |
| Byzantine tolerance | 1 | | | 6, 24 |
| Incentive compatibility | 4 | 3, 31 | F6, F20, F31 | 22, 29, 37, 38 |
| Fair to proposers | 2 | 7 | F24, F30 | 7 |
| Recoverable | 10 | 16, 17, 22, 31 | F9, F22, F29, F30, F32, F38 | 18, 23, 30 |
| Performant | 11 | 7, 8, 24, 26 | F7, F16, F25, F27, F28, F29 | 2, 4, 8, 10, 13, 14, 21, 25 |
| Also wanted | 2 | 19 | F40 | 14 |

**In the attestation file:** nodes per subnet (specs 9, 10; discord F19), Timely (specs 23, 35; discord F12, F13, F14, F21, F34; ethresear.ch 10, 28), Low load per node (discord F15, F25, F39; ethresear.ch 16), Fair vote timing (specs 14; discord F34; ethresear.ch 29), Reliable (specs 11; discord F11), Anonymity enhancing (specs 12; discord F8; ethresear.ch 31, 35) and Bounded spam (specs 20, 28, 32; ethresear.ch 19).

**Elsewhere.** [`specs/README.md`](../../../specs/README.md) now lists the two upstream branches that specify decoupled consensus. The [design space](../README.md#design-space) of the workstream has the designs that the sources add.

## Where the sources contradict the properties

"Left" means the sentence is tagged `human` or quotes Yann, and was not touched.

| What the properties said | What the source says | What was done |
|---|---|---|
| The baseline's 16 aggregators give its resilience | 16 was "chosen to be 16 for phase 0 without too much thought", and kept so that no committee draws zero aggregators (specs 1, 2; discord F2) | New row "Why 16 aggregators" |
| The baseline has no fallback | "Proposers are already and would continue to be the aggregators of last resort" (specs 17), and the chain takes an aggregate from anyone (ethresear.ch 23) | New row "Fallback", and "What the 352 leave out". The 352 stand as the figure for a stack without a fallback |
| Today's aggregators are secret as long as nothing leaks | The duty shows in the subnet subscription, and two studies locate validators by it (specs 12; ethresear.ch 31) | Recorded in the baseline row and under "Where today's stack sits" |
| With honest aggregators coverage is 1 | "the main reason for missed head votes today is not being included in aggregates" (discord F14). The first PQ devnet: 86 % on gossip, 77 % on chain (discord F34) | New property Reach; baseline row "Complete" |
| About 1,024 aggregates per slot | A median of 826 on mainnet (ethresear.ch 11); about 6 received per committee, 4 of them distinct (discord F7) | Recorded in the baseline's load row and under Redundant work |
| Load today: "Not the constraint" | BLS aggregation took "up to 3-4 seconds on lower end hardware" in one client (discord F13) | The row now reads "Light, not free"; the earlier wording was an agent's |
| A vote is kept out only if all k aggregators censor | Where one aggregate per subnet is picked by weight, one aggregator displaces the rest, and the proposer "can always choose" (ethresear.ch 20) | Recorded under Censorship resistance and No displacement |
| One honest aggregator is enough | As a target a margin is asked for (discord F18) | Recorded next to the rule |
| A later aggregator may stay silent when several earlier proofs together cover it | "Each received aggregate is compared on its own, not together with the others" (specs 24) | Sentence reworded (it was an agent's), with the quote under it |
| Aggregators on a few whole subnets | The `pq` gossip rejects an aggregate over more than one committee (specs 19). The EIP-8453 branch: "Aggregates combine the attestations of several committees" (specs 30) | Recorded under the design. Left |
| A private PQ lottery needs a PQ VRF | The `pq` spec has a hash tree of per-slot secrets, used for RANDAO, and a developer raised it for aggregators (discord F33) | Recorded as a building block under the two regimes |
| These votes do not play into fork choice | True in the EIP-8453 branch (specs 29). Not in the Simplex pyspec, where a finality attestation updates the latest-head view on arrival (specs 33) | Settled on 2026-11-26: the reference is Francesco's `pq-dc` branch, where an FG vote reaches fork choice only through a block. Upstream's `pq-dc` agrees. Yann's sentence holds. Left |
| Late aggregates stay includable until the round ends | Under the rewards proposed for EIP-8453, full pay needs the next slot and pay ends after 16 slots (specs 31, an open pull request) | Recorded next to it. Left. In the reference a vote is includable while its target is the current or the previous one, and its rewards do not decay; the pull request is not in it. Upstream's window is another one, and its rewards do not decay either |
| A set that anyone can join does not work | In the Simplex pyspec any node may aggregate on one topic, and gossip bounds content in place of senders (specs 34, 35) | Recorded as a counter-example. Left |
| One vote per validator bounds the spam | Gossip has to forward a second, different vote, for equivocation evidence (specs 32) | Recorded in both files |
| Silencing a machine for a slot costs that slot's roles | With top-layer caching a restarted node is a lesser aggregator for about 10 epochs (discord F39) | Recorded under the network adversary |
| The fan-in of 16 is the merge limit | On a low-end machine merge time steps up after 5 children (ethresear.ch 3) | Recorded under Merge |
| Latency floors of 1.61 to 3.14 s through one merge | On machines that stake, a merge of 16 alone takes 2.2 to 4 s (discord F28) | Recorded under Latency and under "Where we are" |
| Roles drawn by stake | An opt-in, opt-out or registered role is discussed (discord F31; ethresear.ch 1), and EIP-8292 specifies an opt-in one for lean consensus | Recorded under the types, in the model and in the design space |
| Blobs as a place for aggregates | Columns and the last slot's proofs peak on the same uplink (discord F37) | Recorded under the third level of delivery |
| Votes of about 2.4 kB | 3,112, 2,548, 2,404 and 1,204 bytes, by date and design (ethresear.ch 16; discord F25, F39) | Recorded in the attestation file |
| 8,000 nodes give 250 per subnet | 13,000 nodes give about 400 (discord F19) | Recorded next to the example |

## What no source had

Each note lists its searches. The absences that matter here:

- **A dispersed, erasure-coded, grid or layered assignment of aggregators.** No message in the Discord archive and no topic on ethresear.ch. The nearest is an open question from 2022: "Are there other election mechanisms we could use for collectors that would allow us to end up with less collectors?" (ethresear.ch 21).
- **Consensus aggregates carried in blobs.** Nothing.
- **An attack on known aggregators, described or measured.** No topic and no message. The `pq` files have no note on it either (specs 28).
- **Censoring or Byzantine aggregators as named adversaries.** Nothing beyond the remarks in ethresear.ch 20 and 36.
- **A worked-out way to pay aggregators.** Calls for one exist (ethresear.ch 38), and the stated plan for PQ Gasper is none (discord F31).
- **A derivation of 16,** or of attesting at 1/3 and aggregating at 2/3 of the slot.
- **A statement in the spec that the lottery is private in order to protect aggregators.** The spec gives spam as the reason (specs 3). A question of 2020 that reads it as protection got no reply in the Discord archive (discord F1). The one place that treats it as the answer is an exchange on ethresear.ch in June 2020: asked whether "aggregators could be DOSed similarly to proposers", protolambda replied "I think aggregators are already selected privately at random based on a signature" ([topic 7547, replies 11 and 12](https://ethresear.ch/t/7547/11)). It is in no numbered entry; the ethresear.ch note mentions it in its last list, and the oversight thread read it in the downloaded posts.

## Left out of the properties

- **Discord F26:** superseded, see above.
- **ethresear.ch 39 and 40:** aggregator selection that distributed validators can run, and a post-quantum plan for the transport. Both are next to this stage and not of it.
- **Parts of entries that are cited for something else:** the minutes it takes to rebuild keys and the hash tree after a restart (discord F33), an on-chain cost per vote (ethresear.ch 26), and the capacity of a subnet in signatures (ethresear.ch 13).

## Yann's answers, 2026-11-26

1. **Which spec is the reference for decoupled consensus.** "the right spec is the one francesco (fradamt) worked on this week, there should also be a PR from anders".
   - An agent took that to be the `pq-dc` and `decoupled-consensus` branches of `ethlabs-org/consensus-specs`, where Francesco's commits of 16 to 25 November are. [`specs/README.md`](../../../specs/README.md) has them, with what they fix for networking. Asked whether they are the ones, Yann answered "I think perhaps, but check also /ethereum/consensus specs". Upstream was read the same day: Francesco's commits are not there, and [`specs/README.md`](../../../specs/README.md#where-upstream-differs) says where the two differ.
   - Anders' two pull requests, 5855 and 5856, are against the upstream branch and are not in Francesco's.
   - What the reference says is in the two property files as items that say "reference spec". Those that hold on Francesco's branches only say "Not upstream".
2. **Which of the five new properties to keep.** "the properties sound good for now". All five stay, tagged `external`, each marked as kept.
3. **Which blobs.** "blobs are a specific type of transaction", "stored for say 2 weeks only", with blob streaming as what may come. It is in the [blob note](../blob-propagation/README.md#5-blob-transactions-and-blob-streaming) and under the third level of delivery.
   - The "asynchronous blobs write-up" he named with it is the ethresear.ch post on blob streaming, topic 24202. Asked again that day, he said "it might now be called something like blob streaming, it should also mention blob tickets", and the post matches both. No text carries the old name.

## Still open, for Yann

1. **Whether nodes per subnet should be tied to a node count** (13,000 behind today's 400 to 500), since the secret regime's figures scale with it.
2. **Whether lean consensus is in scope.** EIP-8292 gives it an aggregator role that any node may opt into, statically configured in its devnets. The properties record that as `external`. Nothing in this workstream is designed for it.
