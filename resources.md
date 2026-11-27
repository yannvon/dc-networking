---
title: Context and resources
status: wip
date: 2026-11-26
provenance: agent
---

> **Provenance: agent.** Written 2026-11-26 by an agent at Yann's request: "I want the repo to keep track of context / resources, such as discord, specs repo, ethresearch, etc., so agents know where to look in case of questions". It lists the outside sources that this repo's notes already cite, and how an agent read each of them from a cloud sandbox on 2026-11-25 and 26. Yann has not reviewed it.
> - **Keep it current.** Add a source when you use one that is missing. Move the "last read" of a source when you read it again. Correct an entry when its recipe stops working.
> - **Revisions are what was read, not what is newest.** Branches move, so check the tip before you rely on a "last read" below.

# Context and resources: where to look

**What this is.** The sources behind this repo: specifications, discussions, write-ups and measurements. Each entry says what the source is good for, where it lives, how to read it without a browser, and what the repo has already taken from it. Start here when a question is about decoupled consensus, post-quantum signatures or Ethereum's p2p layer and the answer is not in the repo.

## First, what the repo already has

| Question | Look in |
|---|---|
| What do we want from the p2p layer? | [`properties/`](properties/README.md) |
| Which parameters are binding? | [`design/requirements.md`](design/requirements.md) |
| What is settled, and what is open? | [`research/open_questions.md`](research/open_questions.md) |
| What does the spec say? | [`specs/README.md`](specs/README.md) |
| What have others said about aggregation and its networking? | [`research/pq-aggregation/background/`](research/pq-aggregation/background/README.md): 116 entries with quotes, from consensus-specs, ethresear.ch and the Discord |
| Sizes and proving times under PQ? | [`research/pq/README.md`](research/pq/README.md), "Sources" and "Arithmetic" |
| Can gossipsub carry a subnet of PQ votes? | [`research/pq-gasper/gossipsub/`](research/pq-gasper/gossipsub/README.md): Shadow simulations of one PQ Gasper subnet, with their own [list of sources](research/pq-gasper/gossipsub/sources.md) |
| What have we written up to share? | [`posts/`](posts/README.md): four posts on PQ Gasper |
| What was decided on a call? | [`meetings/`](meetings/) |

## Specifications

| Source | Good for | Where | Last read here |
|---|---|---|---|
| **Reference spec for PQ decoupled consensus** (Francesco D'Amato) | What a finality vote and a head vote are, who votes when and on which subnet, what a block may include. Aggregation as a network protocol is TODO in it | [`ethlabs-org/consensus-specs`](https://github.com/ethlabs-org/consensus-specs), branch `pq-dc`, under `specs/_features/pq/` | `1e9307b` (2026-11-25), on 2026-11-26. [`specs/README.md`](specs/README.md) |
| Its sibling with BLS signatures | The same protocol without leanXMSS, as EIP-8453 | Same repository, branch `decoupled-consensus`, under `specs/_features/eip8453/`. Drafts sit next to it on branches named `eip8453-*` | `c020075` (2026-11-23), on 2026-11-26 |
| Upstream branches of the same specs | What is merged upstream, where it differs from Francesco's branches, and the open pull requests: incentives (5856), fixes (5855), two head votes on gossip (5863), lock rules (5806). The EIP's draft names `decoupled-consensus` here as the work-in-progress spec | [`ethereum/consensus-specs`](https://github.com/ethereum/consensus-specs), branches `decoupled-consensus` and `pq-dc`. Two more carry decoupled consensus: `dc-lock-updates` and `dc-optimistic-confirmation` | `0f4fa3f` and `bde2349`, on 2026-11-25, and again on 2026-11-26, when neither tip had moved. [Where upstream differs](specs/README.md#where-upstream-differs). [Background, entries 29 to 32](research/pq-aggregation/background/consensus-specs.md) |
| PQ Gasper spec (Justin Traglia) | The only spec with PQ aggregators worked out: 4 per committee, staggered, with gossip rules | `ethereum/consensus-specs`, branch `pq`, under `specs/_features/pq/` | `4c29678` (2026-11-21), on 2026-11-25. [`research/pq-gasper/design.md`](research/pq-gasper/design.md). `b73c695` (2026-11-26), on 2026-11-27, when it was the tip. What the spec files change between the two is not about attestations or their aggregation. [Multi-subnet aggregation](https://github.com/yannvon/dc-networking/blob/c63e3e50a3f12254c7abf8a25eab6511d61da8bc/research/pq-gasper/multi-subnet-aggregation.md). On 2026-11-27 its three notes are on the branch `pq-gasper-multi-subnet-aggregation` of `yannvon/dc-networking`, at `c63e3e5`, and not on `main`, so this page links to them there |
| Today's specs | Why today's aggregation is the way it is: the issues and pull requests behind each rule | `ethereum/consensus-specs`, `master`, with its issues and pull requests | `d2021d2`, on 2026-11-25. [Background, entries 1 to 22](research/pq-aggregation/background/consensus-specs.md) |
| Simplex pyspec (Francesco D'Amato) | The reference until 2026-11-26. Finality votes that feed fork choice on arrival | [`fradamt/consensus-specs`](https://github.com/fradamt/consensus-specs), branch `simplex-healing` | `5750e57` (2026-07-27). [`specs/README.md`](specs/README.md#earlier-reference-the-simplex-pyspec) |
| First DC draft (Mikhail Kalinin) | What [Q18](research/fg/staggered-committees/README.md) was written against | [`mkalinin/eth2.0-specs`](https://github.com/mkalinin/eth2.0-specs), branch `dc-feature` | As cited in Q18 |
| EIPs | [EIP-8292](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-8292.md), PQ attestation aggregators as an opt-in role in lean consensus. [EIP-8256](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-8256.md), blob streaming. [EIP-8288](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-8288.md), aggregation in the mempool. [EIP-8070](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-8070.md), sparse blobpool. [EIP-7870](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-7870.md), hardware and bandwidth | [`ethereum/EIPs`](https://github.com/ethereum/EIPs), `EIPS/eip-<number>.md`. The EIP for decoupled consensus, EIP-8453, is an open pull request, [12566](https://github.com/ethereum/EIPs/pull/12566). Its text is `EIPS/eip-8453.md` at the pull request's head | 8292 at `6889815` and 8256 at `bdc1d09`, on 2026-11-26. The draft of 8453 at `645e812`, in full, the same day. 8288 was not read |
| leanVM and leanXMSS | Signature and proof sizes, proving and merging times, what a merge may take as input | [`leanEthereum/leanVM`](https://github.com/leanEthereum/leanVM): `doc/lean_xmss/main.tex`, `doc/leanvm/body/10-ethereum.tex`, `doc/site/benchmarks.json`. Benchmarks page: [leanethereum.github.io/leanVM](https://leanethereum.github.io/leanVM/) | `20a75c1`, on 2026-11-25. `3d84ffc` (2026-11-25), on 2026-11-27: `10-ethereum.tex`, and `benchmarks.json`, which names `be190e90a` as the commit it measured ([multi-subnet aggregation](https://github.com/yannvon/dc-networking/blob/c63e3e50a3f12254c7abf8a25eab6511d61da8bc/research/pq-gasper/multi-subnet-aggregation.md)). The numbers move between commits, so cite the commit |
| Lean consensus spec | What EIP-8292 defers to | [`leanEthereum/leanSpec`](https://github.com/leanEthereum/leanSpec) | Not read |
| Formal models | A Lean proof of a protocol with an available chain and a finality gadget, and the library our formal note may move to | [`ethlabs-org/verified-consensus`](https://github.com/ethlabs-org/verified-consensus), which was `eth-consensus-lean` until a rename that Yann reported on 2026-11-26. The old address redirects, and the Lake package (`consensus-lean`) and the module paths (`ConsensusLean/`) are unchanged. [`ethereum/EthLib`](https://github.com/ethereum/EthLib) | `c1bf08b` and `56d23b9`, on 2026-11-25. On 2026-11-26 only the rename was checked, with `main` at `5c24cb1`. [`research/pq-aggregation/formal/`](research/pq-aggregation/formal/README.md) |
| Clients | A DC fork of Prysm used in the benchmarks, and Silver's gossip stack | [`sukunrt/prysm`](https://github.com/sukunrt/prysm), [`gattaca-com/silver`](https://github.com/gattaca-com/silver) | [`benchmarking/`](benchmarking/), [`research/clients/silver/`](research/clients/silver/README.md) |

## Discussions

| Source | Good for | Where, and how to read it | Last read here |
|---|---|---|---|
| **Eth R&D Discord** | What client and spec developers are arguing about this week: `pq-networking`, `pq-cl` and its threads, `consensus-dev`, `networking`, `allcoredevs` | The public archive, [`ethereum/eth-rnd-archive`](https://github.com/ethereum/eth-rnd-archive). One folder per channel, one `YYYY-MM-DD.json` per day with a list of messages (`author`, `content`, `created_at`), and threads under `<channel>/_threads/<thread name>/`. Clone it and search the JSON with a script. Cite a message by file, position in the file and commit | `18a6ec3`, messages up to 2026-11-25. [Background: Discord](research/pq-aggregation/background/eth-rnd-discord.md) |
| **ethresear.ch** | Worked-out proposals and measurements, with their replies | Discourse, readable without a browser: `https://ethresear.ch/t/<id>.json` for a topic, `https://ethresear.ch/raw/<id>` for its Markdown, `https://ethresear.ch/search.json?q=<words>` to search, `https://ethresear.ch/topics/created-by/<user>.json` for an author | 58 topics, on 2026-11-25. On 2026-11-26: 24202 in full, and 22613, 23338 and 26264 in part. [Background: ethresear.ch](research/pq-aggregation/background/ethresearch.md). Start at [24527](https://ethresear.ch/t/24527), decoupled consensus |
| Ethereum Magicians | The discussion thread of an EIP, and the notes of the All Core Devs calls | Discourse as well: `https://ethereum-magicians.org/search.json?q=<words>` | Search only, on 2026-11-26 |
| All Core Devs and breakout calls | Decisions, such as [ACDC #191](https://forkcast.org/calls/acdc/191), which dropped BLS decoupled consensus | [forkcast.org/calls](https://forkcast.org/calls/acdc/191) for summaries, and the agenda issues of [`ethereum/pm`](https://github.com/ethereum/pm) | As cited in [`research/pq/README.md`](research/pq/README.md) |
| This group's calls | What we agreed among ourselves | [`meetings/`](meetings/). The transcripts they link are Google Docs that need a sign-in, so an agent cannot read them | |

## Write-ups

| Source | Good for | Where | Used in |
|---|---|---|---|
| Decoupled consensus | The protocol in prose | [ethresear.ch 24527](https://ethresear.ch/t/unblocking-faster-finality-with-decoupled-consensus/24527) | [`README.md`](README.md) |
| SEACAST (Csaba Kiraly) | Broadcast of large objects, as coded chunks | [Note](https://notes.ethereum.org/@cskiraly/seacast), and its [specification](https://github.com/cskiraly/informed-diffusion-spec) | [Blob note](research/pq-aggregation/blob-propagation/README.md) |
| Blob streaming | Blob data sent ahead of its block, admitted by tickets. Yann's "asynchronous blobs write-up": the post was announced as the "async blob post" | [EIP-8256](https://github.com/ethereum/EIPs/blob/master/EIPS/eip-8256.md), its [HackMD draft](https://hackmd.io/@gMH0wL_0Sr69C7I7inO8MQ/B125sCUtZx) that Yann pointed to, and the post that argues for it, "Scaling the DA layer with Blob Streaming", [ethresear.ch 24202](https://ethresear.ch/t/24202). Earlier texts on blobpool tickets, read in part only: [ethresear.ch 22613](https://ethresear.ch/t/22613) and [23338](https://ethresear.ch/t/23338), and Francesco D'Amato's notes [Blob mempool tickets](https://hackmd.io/@fradamt/blob-mempool-tickets) and [Mempool DAS with blob tickets](https://hackmd.io/@fradamt/blob-tickets) | [Blob note, section 5](research/pq-aggregation/blob-propagation/README.md#5-blob-transactions-and-blob-streaming) |
| PQ aggregation load model (Barnabé Monnot) | Gossip load per node as a formula | [`barnabemonnot/pq-aggregation-model`](https://github.com/barnabemonnot/pq-aggregation-model) | [`research/pq/README.md`](research/pq/README.md) |
| PQ attestation measurements and a first simulation (Anton Nashatyrev) | leanVM on two Macs: proving and merge times, proof sizes, memory and verification. One simulated slot of 16 subnets, in which pool nodes publish the aggregates | [`Nashatyrev/jvm-libp2p`](https://github.com/Nashatyrev/jvm-libp2p), branch `pq-gasper`: [`pq-gasper.md`](https://github.com/Nashatyrev/jvm-libp2p/blob/e7b69b840addf76b19b361988744754ea919588c/pq-gasper.md) and its follow-up on the mesh degree, [`pq-gasper-mesh-degree.md`](https://github.com/Nashatyrev/jvm-libp2p/blob/e7b69b840addf76b19b361988744754ea919588c/pq-gasper-mesh-degree.md). Both read at `e7b69b8` (2026-11-17) on 2026-11-26, which was still the tip on 2026-11-27 | [Avenues post](posts/pq-gasper-avenues.md), the [builders scripts](research/pq-gasper/builders/sim/), [multi-subnet aggregation](https://github.com/yannvon/dc-networking/blob/c63e3e50a3f12254c7abf8a25eab6511d61da8bc/research/pq-gasper/multi-subnet-aggregation.md) |
| PQ roadmap notes | The case for PQ decoupled consensus against PQ Gasper | [pqai27](https://ethlabs.org/writings/pqai27.html), [Potuz on PQ](https://www.potuz.net/posts/pq/) | [`research/pq/README.md`](research/pq/README.md) |
| Validator deanonymization (Heimbach, Vonlanthen et al., USENIX Security '25) | How validators are located on the p2p network, and how many sit on one machine | [arXiv:2409.04366](https://arxiv.org/abs/2409.04366), [ethresear.ch 20463](https://ethresear.ch/t/20463) | [`properties/`](properties/README.md), [aggregator selection](research/pq-gasper/aggregator-selection.md) |

## Kept out of this repo on purpose

- **Kamil Salakhiev's list of nodes and the validators on them.** It is not public and must not be added, in whole or in part. Aggregate figures computed from it may go in (Yann, 2026-11-25). [`measured.py`](research/pq-aggregation/dispersed-assignment/sim/measured.py) computes them and prints aggregates only. Ask Yann for the list.

## How to read these from a sandbox

What worked on 2026-11-25 and 26, from a cloud sandbox without a browser:

- **GitHub.** `gh api` for issues, pull requests, branches and single files. `git clone --filter=blob:none <url>` for a repository whose history you need. One commit on its own: `git fetch --depth 1 origin <full sha>`.
- **A file at a commit.** `gh api repos/<owner>/<repo>/contents/<path>?ref=<sha> -H 'Accept: application/vnd.github.raw'`.
- **A pull request's files.** In a clone, `git fetch origin refs/pull/<number>/head`. GitHub also shows a pull request's commit under the base repository, as `blob/<full sha>/<path>`, which is how the draft of EIP-8453 is linked.
- **A renamed repository.** GitHub redirects the old address on the web, in the API and in git. `gh api repos/<owner>/<old name> --jq .full_name` gives the new name.
- **A sentence in a spec.** The spec files wrap at 80 columns, so `grep` misses a sentence that runs over two lines. Collapse the whitespace before searching, as `check_citations.py` does.
- **Discourse forums** (ethresear.ch, Ethereum Magicians). `curl` on the JSON and raw endpoints above, one request a second. Search takes a phrase in double quotes and the operators `in:title`, `after:YYYY-MM-DD` and `order:latest`. Without an account it allows a few searches a minute; one every ten seconds worked.
- **HackMD.** Add `/download` to a note's address to get its Markdown.
- **Web search and page readers.** They failed on both days. Do not count on them.
- **Cite what you read.** Give the commit for a repository and the date for a page. Quote exactly, and let [`check_citations.py`](research/pq-aggregation/background/check_citations.py) check quotes that cite a background entry or a file at a commit.

## Looked for and not found, or not read

So that the next search does not start from nothing:

- **"Asynchronous blobs" is not a title.** Yann named an "asynchronous blobs write-up" on 2026-11-26. It is the ethresear.ch post on blob streaming, [24202](https://ethresear.ch/t/24202): he added that "it might now be called something like blob streaming, it should also mention blob tickets", and the post matches both. The phrases "async blobs" and "asynchronous blobs" return nothing on ethresear.ch. The post says "AOT", for ahead of time, where its announcement on the Discord said async. The [blob note](research/pq-aggregation/blob-propagation/README.md#5-blob-transactions-and-blob-streaming) has the grounds.
- **The Discord archive is not complete.** Its README says it is updated weekly, and an issue of 2026-11-16, [Archiving stalled](https://github.com/ethereum/eth-rnd-archive/issues/1), is open. Images posted there are in Git LFS and were not read.
- **Not read:** the lean consensus spec, EIP-8288, and documents that the forum threads link off-site. The texts on blobpool tickets that the blob streaming post points to were read in part only.
- **Searched without a result** on ethresear.ch and in the Discord archive: a dispersed or erasure-coded assignment of aggregators, consensus aggregates carried in blobs, an attack on known aggregators, and a worked-out way to pay aggregators. The searches are listed at the end of each [background note](research/pq-aggregation/background/README.md).
