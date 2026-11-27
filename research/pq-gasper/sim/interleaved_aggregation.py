"""PQ Gasper: interleaved aggregation. 64 subnets with 64 aggregators that each prove 4
of them, against the pq spec's 16 subnets with 4 dedicated aggregators each.
Which tolerates more faults?

Stdlib only, deterministic (fixed seed), about 40 s. Prints the numbers quoted in
../interleaved-aggregation.md. Additions beyond the assigned span are in
voluntary_aggregation.py. The same layouts are studied for PQ-DC in
research/pq-aggregation/dispersed-assignment of yannvon/dc-networking @ 546d9a5,
whose layers are the cuts here; it has exact counts for a grid layout.

Equal footing: both have 64 aggregators per slot, proofs of 1/16 of a slot's votes,
4 proofs per vote, and nodes that relay 1/16 of all votes (1 of 16 subnets, 4 of 64).

Model, one slot. A subnet carries one committee. An aggregator proves the votes of
the subnets in its span, and a subnet's votes get in if one aggregator that spans
it is honest and reachable. Layouts:

  spec       16 subnets, 4 aggregators per subnet, each proves its own subnet
  aligned    64 subnets in 16 fixed groups of 4, with 4 aggregators per group:
             the spec's layout on topics a quarter the size
  interleaved  64 subnets, cut into 16 groups of 4 in four independent ways, with
             1 aggregator per group of each cut. A subnet has one aggregator from
             each cut, and they prove it together with different subnets.
  windows    aggregator i proves subnets i to i + 3, around the ring of 64
  3 cuts     interleaved with three cuts: 48 aggregators, 3 proofs per vote
  span 8     four cuts into 8 groups of 8: 32 aggregators, 4 proofs per vote

Faults are either random (each aggregator is faulty with probability beta) or
chosen by an attacker that floods the fewest aggregators it can (closed forms for
spec, aligned and windows, a search for the others). To halt finality it has to
empty a third of an epoch's subnet-slots. It can spread them over all 32 slots,
which needs the fewest floods at once, or silence whole slots, which costs as many
floods as a slot has aggregators in any layout.
"""
import random
from itertools import combinations
from math import ceil, exp

V = 800_000                    # posts/pq-gasper-avenues.md: "16 subnets with 800k validators"
SLOTS_PER_EPOCH = 32
SLOT_S = 12
SUBNETS = 64                   # ATTESTATION_SUBNET_COUNT
SPAN = 4                       # subnets per proof, and per node
GROUPS = SUBNETS // SPAN       # also the spec's subnets, and its committees per slot
AGGREGATORS = 64               # per slot, in the spec and in the proposal
PROOF_KIB, MERGED_KIB = 204, 280   # leanVM benchmarks.json @ be190e90a: 1,400 signatures; 16 such proofs into 1
PROVE_1400_S = {"M4 Max, 16 cores": 0.695, "EX63, 20 cores": 0.730, "AX42, 8 cores": 0.955, "NUC, 16 cores": 1.267}
PROVING_WINDOW_S = 2.4         # pq validator.md, "Proves for"
THIRD_OF_SUBNETS = SUBNETS * SLOTS_PER_EPOCH // 3 + 1     # subnet-slots per epoch that halt finality
THIRD_OF_GROUPS = GROUPS * SLOTS_PER_EPOCH // 3 + 1       # the same in groups, or in the spec's committees
CURVE = range(1, 41)           # numbers of emptied subnets that the search covers for the interleaved layout
SEED, SLOTS_SEARCHED, SLOTS_SAMPLED, SWAPS_PER_SUBNET = 1, 24, 5_000, 1_000

popcount = getattr(int, "bit_count", None) or (lambda x: bin(x).count("1"))


# --- Layouts: one span (the subnets it proves) per aggregator -----------------

def cut_spans(rng, cuts, span=SPAN, same=False, subnets=SUBNETS):
    """One aggregator on every group, for `cuts` ways to cut the subnets into groups of `span`."""
    spans, order = [], list(range(subnets))
    for cut in range(cuts):
        if cut == 0 or not same:
            rng.shuffle(order)
        spans += [tuple(order[i:i + span]) for i in range(0, subnets, span)]
    return spans


def aligned(rng):
    return cut_spans(rng, SPAN, same=True)


def interleaved(rng):
    return cut_spans(rng, SPAN)


def window_spans():
    """Aggregator i proves subnets i to i + 3 around the ring: consecutive subnet ids, as today's backbone has."""
    return [tuple((i + j) % SUBNETS for j in range(SPAN)) for i in range(SUBNETS)]


def masks_of(spans, subnets=SUBNETS):
    """For each subnet, the aggregators that span it, as a bit mask."""
    masks = [0] * subnets
    for aggregator, span in enumerate(spans):
        for subnet in span:
            masks[subnet] |= 1 << aggregator
    return masks


# --- Random faults ------------------------------------------------------------

def lost(beta, per_vote=SPAN):
    """P(a vote has no honest aggregator) when `per_vote` aggregators prove it."""
    return beta ** per_vote


def solve(f, target):
    """x in [0, 1] with f(x) = target, f increasing."""
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < target else (lo, mid)
    return hi


def finality_halt(lost_at):
    """Smallest stake beta that halts finality by withholding its votes and its aggregates."""
    return solve(lambda beta: 2 / 3 - (1 - beta) * (1 - lost_at(beta)), 0)


def slots_with_losses(layout, beta, slots=4 * SLOTS_SAMPLED):
    """Share of slots in which some subnet has no honest aggregator, share in which 4 or more have none
    (1/16 of the slot's votes), and such subnets per slot."""
    rng = random.Random(SEED)
    hit = big = empty = 0
    for _ in range(slots):
        spans = layout(rng)
        honest = sum(1 << aggregator for aggregator in range(len(spans)) if rng.random() >= beta)
        dead = sum(not mask & honest for mask in masks_of(spans))
        hit += dead > 0
        big += dead >= SPAN
        empty += dead
    return hit / slots, big / slots, empty / slots


def validators_for_all_subnets(trials=2_000):
    """Mean number of validators, each with a random interleaved span, until their spans cover every subnet."""
    rng = random.Random(SEED)
    total = 0
    for _ in range(trials):
        spans = interleaved(rng)
        left = set(range(SUBNETS))
        while left:
            left.difference_update(rng.choice(spans))
            total += 1
    return total / trials


# --- Proofs on the wire -------------------------------------------------------

def proofs_sent(spans, faulty, turns=SPAN):
    """Proofs sent when a cut's aggregators take one turn together and skip a proof whose subnets earlier turns cover."""
    per_turn = len(spans) // turns
    covered, sent = set(), 0
    for turn in range(turns):
        new = [spans[aggregator] for aggregator in range(turn * per_turn, (turn + 1) * per_turn)
               if aggregator not in faulty and not covered.issuperset(spans[aggregator])]
        sent += len(new)
        covered.update(*new)
    return sent


def mean_proofs_sent(layout, beta=0.0, down=0, slots=SLOTS_SAMPLED):
    """Proofs sent per slot if each aggregator is faulty with probability beta, and `down` of the first turn fail."""
    rng = random.Random(SEED)
    total = 0
    for _ in range(slots):
        spans = layout(rng)
        faulty = {aggregator for aggregator in range(len(spans)) if rng.random() < beta} | set(range(down))
        total += proofs_sent(spans, faulty)
    return total / slots


# --- Chosen faults ------------------------------------------------------------

def cheapest_attack(masks, m, rng, steps=None):
    """Fewest aggregators to flood so that m subnets have none left.

    The best of a greedy start and `steps` swaps under simulated annealing, so an
    upper bound on the true minimum. Any set of flooded aggregators that empties m
    subnets contains the union of their aggregators, so searching over sets of m
    subnets is enough. For m = 1 the greedy start is the minimum.
    """
    subnets = len(masks)
    steps = SWAPS_PER_SUBNET * m if steps is None else steps
    chosen, rest, union = [], list(range(subnets)), 0
    for _ in range(m):
        pick = min(rest, key=lambda s: (popcount(union | masks[s]), rng.random()))
        rest.remove(pick)
        chosen.append(pick)
        union |= masks[pick]
    cost = best = popcount(union)
    if m == 1 or m == subnets:
        return best
    heat = sum(popcount(mask) for mask in masks) / subnets / SPAN     # 1 when a subnet has 4 aggregators
    for step in range(steps):
        temperature = heat * 1.5 * (0.03 / 1.5) ** (step / steps)
        i, j = rng.randrange(m), rng.randrange(subnets - m)
        out, chosen[i] = chosen[i], rest[j]
        union = 0
        for subnet in chosen:
            union |= masks[subnet]
        new_cost = popcount(union)
        if new_cost <= cost or rng.random() < exp((cost - new_cost) / temperature):
            rest[j], cost = out, new_cost
            best = min(best, cost)
        else:
            chosen[i] = out
    return best


def brute_force(masks, m):
    """The true minimum, by trying every set of m subnets."""
    best = SPAN * len(masks) ** 2
    for subnets in combinations(range(len(masks)), m):
        union = 0
        for subnet in subnets:
            union |= masks[subnet]
        best = min(best, popcount(union))
    return best


def check_search(slots=40, subnets=16):
    """Cases in which the search equals brute force, on interleaved slots small enough to enumerate."""
    rng = random.Random(SEED)
    same = cases = 0
    for _ in range(slots):
        masks = masks_of(cut_spans(rng, SPAN, subnets=subnets), subnets)
        for m in (4, 5, 6):
            exact, found = brute_force(masks, m), cheapest_attack(masks, m, rng)
            assert found >= exact
            same += found == exact
            cases += 1
    return same, cases


def attacks(layout, targets, slots=SLOTS_SEARCHED):
    """For each of `slots` random slots, the cheapest attack found per number of emptied subnets in `targets`."""
    rng = random.Random(SEED)
    found = []
    for _ in range(slots):
        masks = masks_of(layout(rng))
        cost = {m: brute_force(masks, m) if m <= 3 else cheapest_attack(masks, m, rng) for m in targets}
        cheapest = None
        for m in sorted(targets, reverse=True):       # an attack that empties more subnets also empties m
            cheapest = cost[m] if cheapest is None else min(cheapest, cost[m])
            cost[m] = cheapest
        found.append(cost)
    return found


def spread_plan(cost):
    """The plan that halts finality with the fewest floods at once: empty 21 or 22 of 64 subnets in every slot.
    Returns the most floods in one slot, and the floods per epoch."""
    low = THIRD_OF_SUBNETS // SLOTS_PER_EPOCH
    extra = THIRD_OF_SUBNETS - low * SLOTS_PER_EPOCH
    return cost[low + 1], cost[low] * (SLOTS_PER_EPOCH - extra) + cost[low + 1] * extra


def most_emptied(cost, floods):
    """Most subnets that `floods` floods empty, by the attacks found."""
    return max((m for m in cost if cost[m] <= floods), default=0)


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def one_in(p):
    return "never" if p <= 0 else f"1 in {1 / p:,.0f}" if p > 1e-9 else f"1 in {1 / p:.1e}"


def main():
    per_slot = V // SLOTS_PER_EPOCH
    third = 1 / 3
    low = THIRD_OF_SUBNETS // SLOTS_PER_EPOCH
    targets = (1, SPAN, low, low + 1)

    print(f"V = {V:,}: {per_slot:,} votes per slot")
    print(f"  {'':36s}{'subnets x votes':>18s}{'aggregators x signatures':>27s}{'proofs per vote':>17s}")
    for label, subnets, aggregators, span in (("spec", GROUPS, AGGREGATORS, 1), ("interleaved aggregation", SUBNETS, AGGREGATORS, SPAN),
                                              ("64 subnets, dedicated aggregators", SUBNETS, SPAN * SUBNETS, 1),
                                              ("3 cuts", SUBNETS, 48, SPAN), ("span 8", SUBNETS, 32, 8)):
        print(f"  {label:36s}{subnets:>8d} x {per_slot / subnets:7,.1f}{aggregators:>15,d} x {span * per_slot / subnets:9,.1f}"
              f"{aggregators * span / subnets:>17.0f}")
    every = V / (AGGREGATORS * SLOTS_PER_EPOCH)
    print(f"  with {AGGREGATORS} aggregators per slot, a validator aggregates every {every:.1f} epochs"
          f" = {every * SLOTS_PER_EPOCH * SLOT_S / 3600:.1f} h")

    print("\nShare of all votes that a node relays")
    for label, held, subnets in (("spec, SUBNETS_PER_NODE = 2", 2, GROUPS), ("spec with 1 subnet per node", 1, GROUPS),
                                 ("interleaved, 4 subnets per node", SPAN, SUBNETS)):
        print(f"  {label:33s}{held} of {subnets}: {held / subnets:6.2%}")
    print(f"  aggregator duties for which the node has to join a subnet: spec {1 - 2 / GROUPS:.1%} with 2 subnets per node"
          f" ({AGGREGATORS * (1 - 2 / GROUPS):.0f} joins per slot), {1 - 1 / GROUPS:.1%} with 1; interleaved aggregation none")
    print("  validators at which a node that holds all their spans holds every subnet, on average:"
          f" aligned {GROUPS * sum(1 / i for i in range(1, GROUPS + 1)):.0f}, interleaved {validators_for_all_subnets():.0f}")

    print("\nRandom faults: each aggregator is faulty with probability beta")
    betas = (0.1, 0.2, third, 0.5)
    print(f"  {'a vote has no honest aggregator':39s}" + "".join(f"{f'beta = {beta:.0%}':>16s}" for beta in betas))
    for label, per_vote in (("4 proofs per vote: spec, aligned, interleaved", 4), ("3 proofs per vote: 48 aggregators", 3)):
        print(f"  {label:39s}" + "".join(f"{one_in(lost(beta, per_vote)):>16s}" for beta in betas))
    for miss in (1e-2, 1e-4):
        beta = solve(lost, miss)
        print(f"  a vote gets in with probability {1 - miss:.2%} up to beta = {beta:.1%}:"
              f" {AGGREGATORS * (1 - beta):.0f} honest of {AGGREGATORS} on average")
    print(f"  stake that halts finality by withholding its votes and its aggregates: {finality_halt(lost):.1%};"
          f" a third of the votes lost at beta = {solve(lost, third):.1%}")
    print(f"  beta = 1/3, spec: a slot loses votes with probability {1 - (1 - lost(third)) ** GROUPS:.1%},"
          f" 1/{GROUPS} of them at a time; {lost(third):.2%} of the votes")
    for label, layout in (("aligned", aligned), ("interleaved", interleaved)):
        hit, big, empty = slots_with_losses(layout, third)
        print(f"  beta = 1/3, {label} (sampled): a slot loses votes with probability {hit:.1%}, and 1/{GROUPS} of them or more"
              f" with probability {big:.1%}; {empty:.2f} subnets per slot = {empty / SUBNETS:.2%} of the votes")
    none = (1 - SPAN / SUBNETS) ** AGGREGATORS
    single = AGGREGATORS * SPAN / SUBNETS * (1 - SPAN / SUBNETS) ** (AGGREGATORS - 1)
    print(f"  unassigned spans (each aggregator proves 4 subnets of its own, at random):"
          f" {none:.1%} of subnets have no aggregator, {single:.1%} a single one")

    print(f"\nChosen faults: aggregators of a slot to flood (search: mean of {SLOTS_SEARCHED} slots,"
          f" {SWAPS_PER_SUBNET:,} swaps per emptied subnet)")
    same, cases = check_search()
    print(f"  the search equals brute force in {same} of {cases} small cases (16 subnets, 4 to 6 emptied)")
    rng = random.Random(SEED)
    known = masks_of(aligned(rng)), masks_of(window_spans())
    for m in targets:                                 # the search finds the two known optimums
        assert cheapest_attack(known[0], m, rng) == SPAN * ceil(m / SPAN)
        assert cheapest_attack(known[1], m, rng) == m + SPAN - 1
    curve = attacks(interleaved, CURVE)
    three_cuts = attacks(lambda rng: cut_spans(rng, 3), targets)
    span_8 = attacks(lambda rng: cut_spans(rng, SPAN, span=8), targets)
    whole_slots = ceil(THIRD_OF_SUBNETS / SUBNETS)     # silent slots per epoch that halt finality
    eighths = 8 * SLOTS_PER_EPOCH // 3 + 1             # the same in groups of 8 subnets
    rows = [("spec, and aligned", AGGREGATORS, SPAN, SPAN, SPAN * ceil(THIRD_OF_GROUPS / SLOTS_PER_EPOCH), SPAN * THIRD_OF_GROUPS),
            ("windows", AGGREGATORS, SPAN, 2 * SPAN - 1, low + SPAN, THIRD_OF_SUBNETS + (SPAN - 1) * SLOTS_PER_EPOCH)]
    rows += [(label, aggregators, mean(c[1] for c in found), mean(c[SPAN] for c in found),
              mean(spread_plan(c)[0] for c in found), mean(spread_plan(c)[1] for c in found))
             for label, aggregators, found in (("interleaved", AGGREGATORS, curve), ("3 cuts", 48, three_cuts),
                                               ("span 8, interleaved", 32, span_8))]
    rows += [("span 8, aligned", 32, SPAN, SPAN, SPAN * ceil(eighths / SLOTS_PER_EPOCH), SPAN * eighths)]
    print(f"  {'':20s}{'aggregators':>12s}{'first votes':>13s}{'1/16 of a slot':>16s}"
          f"{'halt finality, spread over all slots: at once':>47s}{'per epoch':>11s}"
          f"{f'or {whole_slots} whole slots: at once':>28s}{'per epoch':>11s}")
    for label, aggregators, first, sixteenth, at_once, per_epoch in rows:
        print(f"  {label:20s}{aggregators:>12d}{first:>13.1f}{sixteenth:>16.1f}{at_once:>47.1f}{per_epoch:>11,.0f}"
              f"{aggregators:>28d}{whole_slots * aggregators:>11,d}")
    print("  a flood takes an aggregator away from its span, so no layout halts finality with fewer floods per epoch than"
          f" {THIRD_OF_SUBNETS} (4 per vote, spans of 4), {ceil(THIRD_OF_SUBNETS * 3 / 4)} (3 per vote, spans of 4)"
          f" or {ceil(THIRD_OF_SUBNETS * 4 / 8)} (4 per vote, spans of 8)")
    print("  share of a slot's votes lost when f of its aggregators are flooded, by the attacks found:")
    print(f"  {'f':>6s}{'spec, aligned':>16s}{'windows':>10s}{'interleaved':>12s}")
    for floods in (4, 8, 16, 24, 32, 48):
        assert all(c[CURVE[-1]] > floods for c in curve)
        print(f"  {floods:>6d}{floods // SPAN / GROUPS:>16.1%}{max(0, floods - SPAN + 1) / SUBNETS:>10.1%}"
              f"{mean(most_emptied(c, floods) for c in curve) / SUBNETS:>12.1%}")
    print(f"  {AGGREGATORS:>6d}{1:>16.1%}{1:>10.1%}{1:>12.1%}")
    print("  interleaved, floods to empty m subnets: "
          + ", ".join(f"{m}: {mean(c[m] for c in curve):.1f}" for m in (1, 2, 3, 4, 8, 16, 21, 22, 32, 40)))

    print("\nProofs sent per slot, when a cut's aggregators take one turn together and skip what earlier turns cover")
    mib = PROOF_KIB / 1024
    print(f"  {'':20s}{'nothing fails':>14s}{'one of the first turn fails':>29s}{'a third faulty':>16s}")
    for label, layout in (("spec, and aligned", aligned), ("interleaved", interleaved)):
        print(f"  {label:20s}{mean_proofs_sent(layout):>14.1f}{mean_proofs_sent(layout, down=1):>29.1f}"
              f"{mean_proofs_sent(layout, beta=third):>16.1f}")
    print(f"  check, aligned at a third faulty: 16 (1 - beta^4) = {GROUPS * (1 - lost(third)):.1f};"
          f" a proof is {PROOF_KIB} KiB, so {GROUPS} are {GROUPS * mib:.1f} MiB and all {AGGREGATORS} are {AGGREGATORS * mib:.1f} MiB")

    print("\nProving, leanVM benchmarks.json @ be190e90a (1,400 signatures, all threads), taken as linear in signatures")
    for label, subnets in (("a span of 4 subnets", SPAN), ("a span of 8 subnets", 8)):
        times = [subnets * per_slot / SUBNETS * seconds / 1400 for seconds in PROVE_1400_S.values()]
        print(f"  {label}: {subnets * per_slot / SUBNETS:,.1f} signatures, {min(times):.2f}-{max(times):.2f} s;"
              f" the spec allows {PROVING_WINDOW_S} s")


if __name__ == "__main__":
    main()
