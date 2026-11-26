# Specs

The DC networking spec itself is still to come. Until then, the reference is
Francesco's executable spec of decoupled consensus (EIP-8453), on the branches
he works on:

**[`ethlabs-org/consensus-specs`, branch `pq-dc`](https://github.com/ethlabs-org/consensus-specs/tree/pq-dc/specs/_features/pq)**
— decoupled consensus on leanXMSS signatures, which is what this repo designs
for. Tip as of 2026-11-26:
[`1e9307b`](https://github.com/ethlabs-org/consensus-specs/commit/1e9307bb73a92c7262bc7e571bed1a87570a7832) (2026-11-25).

**[`ethlabs-org/consensus-specs`, branch `decoupled-consensus`](https://github.com/ethlabs-org/consensus-specs/tree/decoupled-consensus/specs/_features/eip8453)**
— the same finality gadget and available chain with BLS signatures. Tip as of
2026-11-26: [`c020075`](https://github.com/ethlabs-org/consensus-specs/commit/c020075f17f7316a18f6ca962df2cee64324bad8) (2026-11-23).

*Set by Yann on 2026-11-26: "the right spec is the one francesco (fradamt)
worked on this week, there should also be a PR from anders". An agent found the
branches from that sentence: between 16 and 25 November these two, and drafts
next to them in the same repository, are where Francesco's commits to a
consensus spec are. Asked whether they are the ones he meant, Yann answered the
same day: "I think perhaps, but check also /ethereum/consensus specs". The check
is under [Upstream](#upstream-and-open-pull-requests): Francesco's commits are
not there, the pull requests are, and the two sides
[differ](#where-upstream-differs). So the reading stands, and it is still a
reading. The tables and the notes under them are an agent's reading at the
commits given. Both branches move, so cite them with the commit.*

| File on `pq-dc` | What it gives us |
|---|---|
| [`p2p-interface.md`](https://github.com/ethlabs-org/consensus-specs/blob/1e9307bb73a92c7262bc7e571bed1a87570a7832/specs/_features/pq/p2p-interface.md) | 16 attestation subnets (`ATTESTATION_SUBNET_COUNT_PQ`). `attestation_{subnet_id}` carries FG attestations as `SingleAttestation`: one per validator and round for the current target, and one more per validator for the previous target. The global `head_vote` topic forwards up to two different votes per validator and slot, "so one equivocation can propagate". The two aggregate topics, `head_vote_aggregate` and `attestation_aggregate`, are TODOs |
| [`validator.md`](https://github.com/ethlabs-org/consensus-specs/blob/1e9307bb73a92c7262bc7e571bed1a87570a7832/specs/_features/pq/validator.md) | A validator's committee and subnet are fixed by its index. It casts one FG attestation per round, in its committee's slot, at or after the support cutoff. An aggregate holds the attestations of one round with the same data, and can span committees. Aggregator selection, the aggregate messages and their deadlines are TODOs. A block takes up to 16 FG aggregates and 8 head vote aggregates, and the proposer merges their proofs into one |
| [`beacon-chain.md`](https://github.com/ethlabs-org/consensus-specs/blob/1e9307bb73a92c7262bc7e571bed1a87570a7832/specs/_features/pq/beacon-chain.md) | Rounds of 8 slots (`SLOTS_PER_ROUND`) and 2,048 attestation committees per round (`ATTESTATION_COMMITTEES_PER_ROUND`), so 256 per slot. `compute_attestation_committee_slot`: a committee's slot moves by at most one from round to round. `MAX_VALIDATORS_PER_AGGREGATE` = 131,072. `process_attestation`: an FG attestation can be included while its target is the chain's current or previous target; flags and rewards are settled per round, and there are no penalties. The head vote committee is drawn by a lottery over VRF openings, with an expected size of 512 |
| [`fork-choice.md`](https://github.com/ethlabs-org/consensus-specs/blob/1e9307bb73a92c7262bc7e571bed1a87570a7832/specs/_features/pq/fork-choice.md) | "The store follows the finality gadget (FG) through the beacon state and runs the available chain (AC) on head votes." Head votes reach fork choice from the wire; FG attestations reach it through the blocks that include them. Deadlines at 25 %, 50 % and 75 % of the slot (`HEAD_VOTE_DUE_BPS`, `SUPPORT_CUTOFF_BPS`, `VIEW_FREEZE_BPS`) |

The `decoupled-consensus` branch has the same four files under
`specs/_features/eip8453/`. Three differences matter here: it has 64 attestation
subnets, its head vote committee has 1,024 seats that are kept in the state, and
its aggregates may combine attestations of different rounds. On `pq-dc` they may
not, because every round has its own leanXMSS leaf.

### What it fixes for networking, and what it leaves open

Read on `pq-dc` at `1e9307b`. Numbers at 800,000 validators are an agent's
arithmetic. Three of the items are Francesco's and not upstream's: who votes
when and where, how long a vote can be included, and that an aggregate keeps
one encoding ([Where upstream differs](#where-upstream-differs)).

- **Fixed: who votes when, and where.**
  - Committee = validator index modulo 2,048, so about 390 validators each, and
    subnet = committee index modulo 16. Neither ever changes for a validator.
  - A slot has 256 committees and about 100,000 votes, 16 committees and about
    6,250 votes on each subnet.
  - The committees are cut into 8 blocks of 256, one per slot of a round, and
    neighbouring blocks swap slots from round to round. A committee votes
    7, 8 or 9 slots after its last vote.
  - This is what "Fair vote timing" and "Anonymity enhancing" in the
    [list of properties](../properties/README.md) propose: send times that
    rotate, and no churn across subnets
    ([Q18](../research/fg/staggered-committees/README.md)).
- **Fixed: where a finality vote counts, and how often it is sent.** Fork choice
  follows the finality gadget "through the beacon state", so a vote counts once
  a block has included it. A validator signs one target vote per height, whether
  or not it was included, and "cannot vote again while a height lasts across
  rounds". A vote that no aggregate picked up is not sent again.
- **Fixed: what an FG attestation is on the wire.** It carries a target, a
  timeout flag and a finality pair, and neither a slot nor a block root. Its
  `round` field is not signed; it selects the leanXMSS leaf the signature uses.
- **Fixed: how long a vote can be included.** While its target is the current
  or the previous target of the including chain. A vote for the previous target
  counts only towards a pending justification and pays nobody.
- **Fixed: what an aggregate may cover.** Any set of committees, up to 131,072
  validators counted over all their members. The proof has one statement per
  committee, "so that the proposer can merge the proofs of aggregates that cover
  different committees into the block's `proof`". Its encoding does not change
  while it can be included, "since the committees depend only on the epoch of
  the target".
- **Open: all of aggregation as a network protocol.** "*TODO*: Specify
  aggregator selection for head votes and FG attestations", and "*TODO*: Specify
  aggregate gossip messages, their proof wrappers and broadcast deadlines.
  Gossip deduplication must use the data, round and signers." That is the
  ground of the [PQ aggregation strategy](../research/pq-aggregation/README.md).
- **Open: the deadlines of an FG attestation.** "*TODO*: Specify the FG
  attestation deadline and source observation for each assigned slot and
  staggered committee schedule."
- **Open: pay.** Rewards for head votes are not specified, and nothing pays an
  aggregator.

### Upstream, and open pull requests

Francesco's branches build on two branches of `ethereum/consensus-specs`, which
is also where the pull requests go.

| Branch | Tip as of 2026-11-26 | Francesco's branch is ahead by |
|---|---|---|
| [`decoupled-consensus`](https://github.com/ethereum/consensus-specs/tree/decoupled-consensus/specs/_features/eip8453) | [`0f4fa3f`](https://github.com/ethereum/consensus-specs/commit/0f4fa3ffdd26ec083ff4dba65645d81433178413) (2026-11-02) | 53 commits, 51 of them his |
| [`pq-dc`](https://github.com/ethereum/consensus-specs/tree/pq-dc/specs/_features/pq) | [`bde2349`](https://github.com/ethereum/consensus-specs/commit/bde2349e1e86763aed845e8a064cb22805628e0c) (2026-11-17) | 66 commits, among them the merge of the `pq` branch at `4c29678` |

Yann asked to "check also /ethereum/consensus specs" (2026-11-26). An agent did
that day, at about 13:30 UTC:

- **The tips have not moved**, and Francesco's branches are ahead of them and
  not behind.
- **Francesco's commits are not there.** His newest commit on any of upstream's
  six branches is of 2026-01-05, and his newest pull request there of
  2026-01-16. The commits that upstream's `decoupled-consensus` adds to `master`
  are by Justin Traglia (42), terence (2) and Mikhail Kalinin (1). Its `pq-dc`
  is the `pq` branch of 2026-11-17 with one commit by terence on top.
- **`master` has no decoupled consensus.** Neither `specs/_features/eip8453`
  nor `specs/_features/pq` is on it at `d2021d2`. Both exist on branches only.
- **Two more upstream branches carry decoupled consensus**, both terence's:
  `dc-lock-updates` at `10d0ae4` (2026-11-06), which is the head of PR 5806,
  and `dc-optimistic-confirmation` at `259b6c7` (2026-11-08).
- **The EIP's draft names upstream as the place of the spec.** "The
  work-in-progress specification is in the decoupled-consensus feature of the
  consensus specifications"
  ([EIP-8453 draft L31](https://github.com/ethereum/EIPs/blob/645e812ee79729dc955ea45f1597245d4d72b002/EIPS/eip-8453.md?plain=1#L31)).
  The draft is an open pull request,
  [12566](https://github.com/ethereum/EIPs/pull/12566) on `ethereum/EIPs`, read
  at `645e812`. Its link goes to `specs/_features/dc`; the files are under
  `specs/_features/eip8453`.

So upstream is where the EIP points and where the pull requests go, and
Francesco's branches are where the spec was written this month (the agent's
reading). The two [differ](#where-upstream-differs).

Open pull requests against upstream `decoupled-consensus`, as of 2026-11-26.
There is none against upstream `pq-dc`, and none against Francesco's branches:
`ethlabs-org/consensus-specs` is a fork of upstream, and its one pull request,
of 2026-09-29, targets another branch. All may change. Anders opened his two
from his own fork, and neither is in Francesco's branches:

- [PR 5856](https://github.com/ethereum/consensus-specs/pull/5856), Anders Elowsson, incentives: full pay for a vote
  included in the slot after its own, none after 16 slots, and a penalty for
  the attester and for the proposer of that first slot.
- [PR 5855](https://github.com/ethereum/consensus-specs/pull/5855), Anders Elowsson, fixes: spec generation, and the
  fork version that a finality attestation is signed with.
- [PR 5863](https://github.com/ethereum/consensus-specs/pull/5863), gossip: up to two head votes per validator and slot.
  Francesco's branches already do this.
- [PR 5806](https://github.com/ethereum/consensus-specs/pull/5806), the fast and slow lock rules. Francesco's branches
  carry a version of it.

What the background research read at the upstream tips is in
[`research/pq-aggregation/background/consensus-specs.md`](../research/pq-aggregation/background/consensus-specs.md), entries 29 to
32. It was written a day before the reference was named.

### Where upstream differs

Read on 2026-11-26. "Upstream" is `pq-dc` of `ethereum/consensus-specs` at
`bde2349`, and "Francesco" is `pq-dc` of `ethlabs-org/consensus-specs` at
`1e9307b`. The BLS pair, `decoupled-consensus` at `0f4fa3f` and at `c020075`,
differs in the same way in the rows on attestation committees, inclusion, gossip
and the bits of an aggregate. Its two head vote rows were not compared, beyond
that both of its sides seat 1,024 validators on the head vote committee.

Upstream's tips are contained in Francesco's branches. So every difference
below came in on his branches after those tips, and is not upstream yet.

What this repo's notes call the "reference spec" is the column on the right. An
item there that rests on one of these rows says "Not upstream".

| | Upstream | Francesco |
|---|---|---|
| Who sits on an attestation committee | An even split of the active validators, "in index order rotated by `epoch`" ([`beacon-chain.md` L1962–L1964](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/beacon-chain.md?plain=1#L1962-L1964)). A validator moves to the neighbouring committee, and with it to another subnet, about every 390 epochs at 800,000 validators (the agent's arithmetic) | The validator index modulo 2,048: "A validator's committee index is fixed by its validator index, and so is its subnet" ([`validator.md` L280–L281](https://github.com/ethlabs-org/consensus-specs/blob/1e9307bb73a92c7262bc7e571bed1a87570a7832/specs/_features/pq/validator.md?plain=1#L280-L281)) |
| When a committee votes in the round | Always in the same slot: "The committees of a round are assigned to its slots in order" ([`beacon-chain.md` L1402](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/beacon-chain.md?plain=1#L1402)) | The slot rotates: "neighbouring blocks swap slots" ([`beacon-chain.md` L1581](https://github.com/ethlabs-org/consensus-specs/blob/1e9307bb73a92c7262bc7e571bed1a87570a7832/specs/_features/pq/beacon-chain.md?plain=1#L1581)) |
| How long a vote can be included | While its data "names the target checkpoint of `state`, or is a vote below the current height whose finality pair is pending" ([`beacon-chain.md` L1608–L1609](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/beacon-chain.md?plain=1#L1608-L1609)), with "its epoch no earlier than `compute_epoch_at_slot(state.finalized_slot)`" ([`validator.md` L904–L905](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/validator.md?plain=1#L904-L905)). Such a late vote still sets the finality flag, which pays (the agent's reading of `process_attestation`) | "Only attestations for the current or the previous target are included", and one for the previous target "credits no flag or reward" ([`beacon-chain.md` L3339–L3343](https://github.com/ethlabs-org/consensus-specs/blob/1e9307bb73a92c7262bc7e571bed1a87570a7832/specs/_features/pq/beacon-chain.md?plain=1#L3339-L3343)) |
| FG attestations on gossip | One per validator and round: "No other valid attestation seen for this round and validator" ([`p2p-interface.md` L1004](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/p2p-interface.md?plain=1#L1004)) | The same for the current target, and one more per validator for the previous target, which "uses its own seen key" ([`p2p-interface.md` L1037–L1039](https://github.com/ethlabs-org/consensus-specs/blob/1e9307bb73a92c7262bc7e571bed1a87570a7832/specs/_features/pq/p2p-interface.md?plain=1#L1037-L1039)) |
| Head votes on gossip | One per validator and slot: "This is the first valid head vote from this validator for the slot" ([`p2p-interface.md` L537](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/p2p-interface.md?plain=1#L537)). A second one is PR 5863 | Two: "Forward at most two distinct valid vote data values per validator and slot" ([`p2p-interface.md` L550–L551](https://github.com/ethlabs-org/consensus-specs/blob/1e9307bb73a92c7262bc7e571bed1a87570a7832/specs/_features/pq/p2p-interface.md?plain=1#L550-L551)) |
| The head vote committee | 1,024 seats, "sampled by effective balance" ([`beacon-chain.md` L239–L240](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/beacon-chain.md?plain=1#L239-L240)) and kept in the state, so known before the slot | A lottery over VRF openings: a validator "casts one head vote if it wins any tickets" ([`validator.md` L293–L294](https://github.com/ethlabs-org/consensus-specs/blob/1e9307bb73a92c7262bc7e571bed1a87570a7832/specs/_features/pq/validator.md?plain=1#L293-L294)), and "The committee size is an expectation, not a bound" ([`beacon-chain.md` L742](https://github.com/ethlabs-org/consensus-specs/blob/1e9307bb73a92c7262bc7e571bed1a87570a7832/specs/_features/pq/beacon-chain.md?plain=1#L742)), of 512 |
| Head votes in a block | "A block carries head votes and marks which of the previous slot's votes the proposer counted as support" ([`beacon-chain.md` L240–L241](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/beacon-chain.md?plain=1#L240-L241)), and fork choice reads them from the block (the agent's reading of `get_view_from_blocks`) | Declarations, which "carry no signature and are used only if the store holds the signed vote" ([`fork-choice.md` L112–L113](https://github.com/ethlabs-org/consensus-specs/blob/1e9307bb73a92c7262bc7e571bed1a87570a7832/specs/_features/pq/fork-choice.md?plain=1#L112-L113)). So the signed vote has to arrive over the wire (the agent's reading) |
| The bits of an aggregate | Laid out in the committees of the epoch of the aggregate's round ([`beacon-chain.md` L2870–L2878](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/beacon-chain.md?plain=1#L2870-L2878), the agent's reading) | "laid out in the committees of the target's epoch, so an aggregate keeps one encoding for as long as it can be included" ([`beacon-chain.md` L279–L281](https://github.com/ethlabs-org/consensus-specs/blob/1e9307bb73a92c7262bc7e571bed1a87570a7832/specs/_features/pq/beacon-chain.md?plain=1#L279-L281)) |

The EIP's draft does not settle the head vote committee. It has
"approximately 512 validators", which is Francesco's size, chosen by
effective balance
([EIP-8453 draft L39](https://github.com/ethereum/EIPs/blob/645e812ee79729dc955ea45f1597245d4d72b002/EIPS/eip-8453.md?plain=1#L39)).
It says that sampling a small committee
"makes a smaller set of validators a potential denial-of-service target", and:
"Private selection using a verifiable random function (VRF) is one option being
explored; neither the selection mechanism nor the committee size is fixed here"
([EIP-8453 draft L71](https://github.com/ethereum/EIPs/blob/645e812ee79729dc955ea45f1597245d4d72b002/EIPS/eip-8453.md?plain=1#L71)).

The same on both sides, on the PQ branches:

- Rounds of 8 slots, 2,048 attestation committees per round, 16 subnets, and
  subnet = committee index modulo 16. Up to 131,072 validators per aggregate,
  and up to 16 FG aggregates and 8 head vote aggregates per block.
- One target vote per height: a validator "cannot vote again while a height
  lasts across rounds"
  ([`beacon-chain.md` L2357](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/beacon-chain.md?plain=1#L2357)).
- An FG attestation carries "neither a slot nor a block root"
  ([`p2p-interface.md` L969–L970](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/p2p-interface.md?plain=1#L969-L970)),
  and fork choice has no handler for one. The EIP's draft has it in one
  sentence: "only inclusion in an accepted block changes the finality chain
  state"
  ([EIP-8453 draft L35](https://github.com/ethereum/EIPs/blob/645e812ee79729dc955ea45f1597245d4d72b002/EIPS/eip-8453.md?plain=1#L35)).
- A validator takes the source of its vote from the frame that fork choice
  returns "At or after the support cutoff"
  ([`fork-choice.md` L1790–L1796](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/fork-choice.md?plain=1#L1790-L1796)),
  half way through the slot. The deadline of the vote is a TODO
  ([`validator.md` L578](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/validator.md?plain=1#L578)).
- Aggregator selection is a TODO
  ([`validator.md` L772](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/validator.md?plain=1#L772)),
  and so are both aggregate topics and their messages.
- "There are no penalties", and rewards for head votes are not specified
  ([`beacon-chain.md` L253–L260](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/beacon-chain.md?plain=1#L253-L260)).
- An aggregate holds the votes of one round. Upstream has a TODO for more:
  "Specify how attestations cast in different rounds are aggregated"
  ([`validator.md` L819](https://github.com/ethereum/consensus-specs/blob/bde2349e1e86763aed845e8a064cb22805628e0c/specs/_features/pq/validator.md?plain=1#L819)).

## PQ Gasper

Justin Traglia's executable PQ Gasper spec, an emergency fork that replaces BLS
with leanXMSS and keeps Gasper:

**[`ethereum/consensus-specs`, branch `pq`](https://github.com/ethereum/consensus-specs/tree/pq/specs/_features/pq)**
— tip as of 2026-11-25: [`4c29678`](https://github.com/ethereum/consensus-specs/commit/4c296784bb6ff54cbdcf72ebdda2a1057cce8893)
(2026-11-21). The branch moves, so cite it with the commit; the links below are
pinned to that one.

| File | What it gives us |
|---|---|
| [`p2p-interface.md`](https://github.com/ethereum/consensus-specs/blob/4c296784bb6ff54cbdcf72ebdda2a1057cce8893/specs/_features/pq/p2p-interface.md) | 16 attestation subnets (`ATTESTATION_SUBNET_COUNT_PQ`) and the modified `beacon_aggregate_and_proof` topic: an aggregate covers exactly one committee, and one whose attesters are all in an aggregate already seen is ignored |
| [`validator.md`](https://github.com/ethereum/consensus-specs/blob/4c296784bb6ff54cbdcf72ebdda2a1057cce8893/specs/_features/pq/validator.md) | The aggregator's duty: the staggered cutoffs and broadcasts of a committee's 4 aggregators, `should_broadcast_aggregate`, and the proposer's merge of the aggregates' proofs into the block's |
| [`beacon-chain.md`](https://github.com/ethereum/consensus-specs/blob/4c296784bb6ff54cbdcf72ebdda2a1057cce8893/specs/_features/pq/beacon-chain.md) | `MAX_COMMITTEES_PER_SLOT_PQ = 16`, `AGGREGATORS_PER_COMMITTEE = 4`, the aggregation committees kept in the state, the STARK interface (`stark_prove_aggregates`, `stark_merge_proofs`, `stark_verify_aggregates`) and `MIN_ATTESTATION_INCLUSION_DELAY_PQ = 2` |

Our reading of it is [`../research/pq-gasper/design.md`](../research/pq-gasper/design.md),
written at `ee867e9` with the changes up to `4c29678` noted at its top. The
[PQ aggregation strategy](../research/pq-aggregation/README.md) takes it as the
load an aggregator may carry: one committee, a 512th of the validators, in one
proof.

## Earlier reference: the Simplex pyspec

*Until 2026-11-26 this was the reference at the top of this file. The text
below is unchanged. Two things differ in the reference above: a finality
attestation here updates a node's latest-head view when it arrives, and
aggregation here is inherited from today's aggregators.*

**[`fradamt/consensus-specs`, branch `simplex-healing`](https://github.com/fradamt/consensus-specs/tree/simplex-healing)**
— the finality gadget (fresh Simplex with height filter and timeouts) layered
on Gloas, replacing Casper FFG. Tip as of 2026-08-11: `5750e57` (2026-07-27).

| File | What it gives us |
|---|---|
| [`p2p-interface.md`](https://github.com/fradamt/consensus-specs/blob/simplex-healing/specs/_features/simplex/p2p-interface.md) | The wire layer: new global topic [`available_attestation`](https://github.com/fradamt/consensus-specs/blob/simplex-healing/specs/_features/simplex/p2p-interface.md#new-available_attestation) (AC votes, 512-to-all) and [modified `beacon_attestation_{subnet_id}`](https://github.com/fradamt/consensus-specs/blob/simplex-healing/specs/_features/simplex/p2p-interface.md#modified-beacon_attestation_subnet_id) (FG votes on committee subnets), plus gossip validation, `Seen` equivocation tracking, and Status v3 |
| [`beacon-chain.md`](https://github.com/fradamt/consensus-specs/blob/simplex-healing/specs/_features/simplex/beacon-chain.md) | SSZ containers (`AvailableAttestation`, the reworked `AttestationData`) and state transition — the byte accounting in [`../bls/ssz.md`](../bls/ssz.md) is derived from here |
| [`fork-choice.md`](https://github.com/fradamt/consensus-specs/blob/simplex-healing/specs/_features/simplex/fork-choice.md) | Height filter, anchor/grade layer, Goldfish descent, confirmation rule |
| [`validator.md`](https://github.com/fradamt/consensus-specs/blob/simplex-healing/specs/_features/simplex/validator.md) | Honest-validator duties: when each vote is produced, aggregation duty |
| [`configs/mainnet.yaml`](https://github.com/fradamt/consensus-specs/blob/simplex-healing/configs/mainnet.yaml) | `# Simplex` block — round schedule (`SLOTS_PER_ROUND`) and gadget constants |

Sibling branch
[`simplex-height-filter`](https://github.com/fradamt/consensus-specs/tree/simplex-height-filter)
is the height-filter base without the healing layer — a diff target, not an
ancestor of `simplex-healing`.

**Caveats for networking work.** The pyspec fixes vote *semantics* and vote
*objects*, not our delivery design: it inherits today's subnet/aggregator
propagation, whereas the DC proposal pipelines FG rounds across slots and
stretches the vote window over two slots (see
[`../bls/explainer.md`](../bls/explainer.md)). Where the two disagree,
[`../design/requirements.md`](../design/requirements.md) is binding for
networking parameters. The spec also trails the theory: the blessed protocol
document is `height_filter_healing.tex`.
