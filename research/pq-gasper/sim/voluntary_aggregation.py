"""PQ Gasper: voluntary aggregation. In the pq spec an aggregator proves
exactly its committee. Here that is a floor: in the same aggregate it may also prove
other committees of the slot whose votes its node holds. What does that buy, on the
spec's own layout?

Stdlib only, deterministic (fixed seed), about 20 s. Prints the numbers quoted in
../voluntary-aggregation.md.

Layout, as in the pq spec: 16 committees per slot, one per subnet, with 4 aggregators
each, so 64 aggregators and at most 64 aggregates per slot. A committee's votes get
in if one aggregator that proved them is honest and reachable.

Additions, made by a share of the aggregators:
  one       one other committee, picked at random, which an attacker cannot predict
  backbone  the committees on the node's backbone subnets: 2 consecutive subnets at a
            random place, as compute_subscribed_subnets gives them. They are public.
  slot      every committee of the slot

Faults are either random (each aggregator is faulty with probability beta) or chosen
by an attacker that floods the fewest aggregators it can. A committee's 4 aggregators
take turns, and one stays silent if earlier turns prove every committee in its aggregate.
"""
import random
from itertools import combinations

from interleaved_aggregation import (MERGED_KIB, PROOF_KIB, PROVE_1400_S, PROVING_WINDOW_S, SEED, SLOTS_PER_EPOCH, V,
                               mean, one_in, popcount)

COMMITTEES = 16                # MAX_COMMITTEES_PER_SLOT_PQ, and ATTESTATION_SUBNET_COUNT_PQ
PER_COMMITTEE = 4              # AGGREGATORS_PER_COMMITTEE
AGGREGATORS = COMMITTEES * PER_COMMITTEE
OTHERS = AGGREGATORS - PER_COMMITTEE                    # the aggregators of the other committees
SUBNETS_PER_NODE = 2           # configs/mainnet.yaml
THIRD = COMMITTEES * SLOTS_PER_EPOCH // 3 + 1           # committee-slots per epoch that halt finality
EVERY = (1 << COMMITTEES) - 1
MERGE_16_S = {"M4 Max, 16 cores": 0.648, "EX63, 20 cores": 0.775, "AX42, 8 cores": 1.018, "NUC, 16 cores": 1.273}
TURN_S = (7.2, 7.8, 8.4, 9.0)  # pq validator.md, "Broadcasts at"
SLOTS_SAMPLED, SLOTS_FLOODED = 20_000, 100


# --- Additions: the other committees an aggregator proves, as a bit mask ---------

def add_one(rng, own):
    other = rng.randrange(COMMITTEES - 1)
    return 1 << (other + (other >= own))


def add_backbone(rng, own):
    start = rng.randrange(COMMITTEES)
    held = sum(1 << (start + i) % COMMITTEES for i in range(SUBNETS_PER_NODE))
    return held & ~(1 << own)


def add_slot(rng, own):
    return EVERY & ~(1 << own)


REACH = {add_one: 1 / (COMMITTEES - 1), add_backbone: SUBNETS_PER_NODE / COMMITTEES, add_slot: 1.0}
"""P(an aggregator that adds proves a given committee other than its own)."""


def aggregates(rng, share, add):
    """A slot's aggregates as [turn][committee]: the committees each one proves, as a bit mask."""
    return [[1 << own | (add(rng, own) if rng.random() < share else 0) for own in range(COMMITTEES)]
            for _ in range(PER_COMMITTEE)]


# --- Random faults ------------------------------------------------------------

def lost(beta, share=0.0, reach=0.0):
    """P(a vote has no honest aggregator): its committee's 4 are faulty, and no honest aggregator added it."""
    return beta ** PER_COMMITTEE * (1 - share * reach * (1 - beta)) ** OTHERS


def sampled_loss(beta, share, add, slots=SLOTS_SAMPLED):
    """The same, counted on random slots."""
    rng = random.Random(SEED)
    missing = 0
    for _ in range(slots):
        proven = 0
        for turn in aggregates(rng, share, add):
            for cover in turn:
                if rng.random() >= beta:
                    proven |= cover
        missing += COMMITTEES - popcount(proven)
    return missing / slots / COMMITTEES


def turns(beta, share, add, slots=SLOTS_SAMPLED):
    """Aggregates sent per slot, and the share of committees proven after each turn, when an honest aggregator
    sends at its turn unless the aggregates of earlier turns prove every committee in its own."""
    rng = random.Random(SEED)
    sent, proven_by = 0, [0] * PER_COMMITTEE
    for _ in range(slots):
        proven = 0
        for turn, row in enumerate(aggregates(rng, share, add)):
            new = [cover for cover in row if rng.random() >= beta and cover & ~proven]
            sent += len(new)
            for cover in new:
                proven |= cover
            proven_by[turn] += popcount(proven)
    return sent / slots, [count / slots / COMMITTEES for count in proven_by]


# --- Chosen faults ------------------------------------------------------------

def floods_unpredictable(share):
    """Aggregators of a slot that an attacker has to flood at once to halt finality, if a share of the aggregators
    left standing each add one other committee that it cannot predict. It floods whole committees, as many in
    every slot as it takes; expected values."""
    need = THIRD / SLOTS_PER_EPOCH
    for flooded in range(1, COMMITTEES + 1):
        adding = PER_COMMITTEE * (COMMITTEES - flooded) * share
        if flooded * (1 - 1 / (COMMITTEES - 1)) ** adding >= need:
            return PER_COMMITTEE * flooded


def floods_predictable(share, add, slots=SLOTS_FLOODED):
    """The same if the attacker knows every addition: to empty a set of committees it floods every aggregator
    whose aggregate proves one of them. Exact per slot, by trying every set of 5 and of 6 committees.
    Returns the most floods in one slot and the floods per epoch, for the plan that spreads over all slots."""
    rng = random.Random(SEED)
    low = THIRD // SLOTS_PER_EPOCH                       # 5 committees in 21 slots and 6 in 11
    extra = THIRD - low * SLOTS_PER_EPOCH
    sets = {size: [sum(1 << c for c in chosen) for chosen in combinations(range(COMMITTEES), size)]
            for size in (low, low + 1)}
    at_once, per_epoch = [], []
    for _ in range(slots):
        counts = {}
        for row in aggregates(rng, share, add):
            for cover in row:
                counts[cover] = counts.get(cover, 0) + 1
        covers = list(counts.items())
        cost = {size: min(sum(count for cover, count in covers if cover & chosen) for chosen in masks)
                for size, masks in sets.items()}
        at_once.append(cost[low + 1])
        per_epoch.append(cost[low] * (SLOTS_PER_EPOCH - extra) + cost[low + 1] * extra)
    return mean(at_once), mean(per_epoch)


def floods_for_one(share, add, slots=2_000):
    """Floods that silence the cheapest committee of a slot, if the attacker knows every addition: the committee's
    4 aggregators and everyone who added it."""
    rng = random.Random(SEED)
    total = 0
    for _ in range(slots):
        provers = [0] * COMMITTEES
        for row in aggregates(rng, share, add):
            for cover in row:
                for committee in range(COMMITTEES):
                    provers[committee] += cover >> committee & 1
        total += min(provers)
    return total / slots


def main():
    per_slot = V // SLOTS_PER_EPOCH
    committee = per_slot / COMMITTEES
    third = 1 / 3
    cases = (("half add one committee", 0.5, add_one), ("all add one committee", 1, add_one),
             ("half add their backbone", 0.5, add_backbone), ("all add their backbone", 1, add_backbone),
             ("a quarter prove the slot", 0.25, add_slot))

    print(f"V = {V:,}: {COMMITTEES} committees of {committee:,.1f} per slot, {PER_COMMITTEE} aggregators each,"
          f" {AGGREGATORS} aggregators and at most {AGGREGATORS} aggregates per slot")
    print(f"  an aggregator's node holds its committee's subnet and {SUBNETS_PER_NODE} backbone subnets of {COMMITTEES};"
          f" the backbone holds its own committee in {SUBNETS_PER_NODE / COMMITTEES:.1%} of duties,"
          f" so it holds {SUBNETS_PER_NODE - SUBNETS_PER_NODE / COMMITTEES:.2f} other committees on average")

    print("\nProving, leanVM benchmarks.json @ be190e90a (all threads), taken as linear in signatures;"
          f" the spec allows {PROVING_WINDOW_S} s")
    print(f"  {'':18s}{'own committee':>15s}{'and 1 more':>12s}{'and 2 more':>12s}{f'committees in {PROVING_WINDOW_S} s':>22s}"
          f"{'the slot, one machine':>23s}{'the slot, 16 provers and a merge':>34s}")
    for machine, seconds in PROVE_1400_S.items():
        own = committee * seconds / 1400
        print(f"  {machine:18s}{own:>13.2f} s{2 * own:>10.2f} s{3 * own:>10.2f} s{PROVING_WINDOW_S / own:>22.1f}"
              f"{COMMITTEES * own:>21.1f} s{own + MERGE_16_S[machine]:>32.2f} s")
    print(f"  a proof is {PROOF_KIB} KiB for 1,400 signatures; 16 such proofs merge into one of {MERGED_KIB} KiB")

    print("\nRandom faults: each aggregator is faulty with probability beta")
    betas = (0.1, 0.2, third, 0.5)
    print(f"  {'':27s}{'aggregators per vote':>22s}" + "".join(f"{f'beta = {beta:.0%}':>20s}" for beta in betas)
          + f"{'99.99 % of votes get in up to beta =':>40s}")
    rows = (("spec", 0.0, add_one),) + cases
    for label, share, add in rows:
        reach = REACH[add]
        tolerated = max(b / 1000 for b in range(1001) if lost(b / 1000, share, reach) <= 1e-4)
        print(f"  {label:27s}{PER_COMMITTEE + OTHERS * share * reach:>22.1f}"
              + "".join(f"{one_in(lost(beta, share, reach)):>20s}" for beta in betas) + f"{tolerated:>40.1%}")
    print("  check at beta = 0.6, sampled against the formula: "
          + "; ".join(f"{label}: {sampled_loss(0.6, share, add):.4f} / {lost(0.6, share, REACH[add]):.4f}" for label, share, add in cases[:4]))

    print("\nTurns: aggregates sent per slot, and committees proven after each turn (at "
          + ", ".join(f"{t} s" for t in TURN_S) + ")")
    for beta, name in ((0.0, "nothing fails"), (third, "a third faulty")):
        print(f"  {name}")
        for label, share, add in rows:
            sent, proven_by = turns(beta, share, add)
            late = sum((TURN_S[i] - TURN_S[0]) * (proven_by[i] - (proven_by[i - 1] if i else 0)) for i in range(PER_COMMITTEE))
            print(f"    {label:27s}{sent:>6.1f} sent   " + "  ".join(f"{share_proven:6.1%}" for share_proven in proven_by)
                  + f"   mean wait after the first turn {late / proven_by[-1]:.2f} s")

    print(f"\nChosen faults: floods that silence one committee, 1/{COMMITTEES} of a slot's votes ({PER_COMMITTEE} in the spec)")
    for label, share, add in cases[:4]:
        alone = (1 - share * REACH[add]) ** OTHERS
        print(f"  {label:27s} if the attacker knows the additions: {floods_for_one(share, add):4.1f};"
              f" if it cannot predict them, the committee's own {PER_COMMITTEE} are enough with probability {alone:.1%}")

    print("\nChosen faults: aggregators of a slot to flood at once to halt finality, spread over all slots")
    print(f"  spec: {PER_COMMITTEE * -(-THIRD // SLOTS_PER_EPOCH)} at once, {PER_COMMITTEE * THIRD} per epoch;"
          f" or all {AGGREGATORS} of a slot in {-(-THIRD // COMMITTEES)} slots: {AGGREGATORS * -(-THIRD // COMMITTEES)} per epoch,"
          " whatever is added")
    for share in (0.5, 1):
        print(f"  {share:.0%} add one committee that the attacker cannot predict: {floods_unpredictable(share)} at once")
    assert floods_unpredictable(0) == PER_COMMITTEE * -(-THIRD // SLOTS_PER_EPOCH)
    at_once, per_epoch = floods_predictable(0, add_backbone, slots=3)
    assert (at_once, per_epoch) == (24, PER_COMMITTEE * THIRD), (at_once, per_epoch)
    for label, share, add in (("half add one committee, and the attacker knows which", 0.5, add_one),
                              ("all add one committee, and the attacker knows which", 1, add_one),
                              ("half add their backbone, which is public", 0.5, add_backbone),
                              ("all add their backbone, which is public", 1, add_backbone)):
        at_once, per_epoch = floods_predictable(share, add)
        print(f"  {label}: {at_once:.1f} at once, {per_epoch:,.0f} per epoch")

    print("\nOn interleaved aggregation's 64 subnets an addition is one subnet, a quarter of a committee")
    for extra in (1, 2, 4):
        loss = third ** PER_COMMITTEE * (1 - extra / 60 * (1 - third)) ** OTHERS
        print(f"  all add {extra} of the other 60 subnets: {extra / 4:.0%} more signatures to prove,"
              f" {PER_COMMITTEE + extra:.0f} aggregators per vote, {one_in(loss)} at beta = 1/3")


if __name__ == "__main__":
    main()
