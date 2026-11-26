"""The figures in machines of sections 9 and 10 of dispersal.py, under a measured node list.

The node list maps validators to the peers they were seen on (Kamil Salakhiev's). It is not in
this repo and was kept out on purpose; only aggregates derived from it are published (Yann,
2026-11-25). This script prints aggregates only: no peer keys, no validator indices, no rows.

Usage:  python3 measured.py <node list csv>      (stdlib, about half a minute)
The csv has one row per peer. The script reads one column, `validator_indices`: the validators
mapped to the peer, separated by ";", and empty for a peer without any.

The list leaves two things open, and the script brackets both:
- Repeats. A validator can be mapped to several peers. Three readings: each validator on the
  largest peer that claims it, split evenly over the peers that claim it, or on the smallest.
- Coverage. The list maps a part of the validators, and the figures are for 800,000. Two
  readings: the measured machines host all of them, in the measured proportions; or the
  validators that were not mapped sit on further machines of the same shape.
"""
import csv
import random
import sys
from collections import defaultdict
from math import floor, log

sys.dont_write_bytecode = True
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from dispersal import (cube_layers, hosting_figures, layouts_in_machines, machines_for_share, need,
                       shuffled_layers)

V = 800_000


def read_peers(path):
    """The validators mapped to each peer that has any."""
    csv.field_size_limit(10 ** 9)
    peers, without = [], 0
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            idx = [int(v) for v in row["validator_indices"].split(";") if v]
            if idx:
                peers.append(idx)
            else:
                without += 1
    return peers, without


def one_peer_each(peers, order):
    """Validators per peer when each validator counts for the first peer in `order` that claims it."""
    taken, sizes = set(), []
    for i in order:
        mine = [v for v in peers[i] if v not in taken]
        taken.update(mine)
        if mine:
            sizes.append(len(mine))
    return sizes


def to_whole(sizes, total):
    """Whole numbers in the proportions of `sizes` that add up to `total` (largest remainders)."""
    scale = total / sum(sizes)
    raw = [s * scale for s in sizes]
    base = [int(r) for r in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - base[i], reverse=True)[:total - sum(base)]:
        base[i] += 1
    return [b for b in base if b]


def same_machines(sizes, mapped):
    """The measured machines host all V validators, in the measured proportions."""
    return to_whole(sizes, V)


def more_machines(sizes, mapped):
    """The validators that were not mapped sit on further machines of the same shape: the measured
    list as often as it fits into V, and for the remainder an evenly spaced sample of it."""
    ints = sorted(to_whole(sizes, mapped), reverse=True)
    copies, rest = divmod(V, mapped)
    out = ints * copies
    if rest:
        step = mapped / rest
        ranks = sorted({min(len(ints) - 1, round((j + 0.5) * step)) for j in range(int(len(ints) / step) + 1)})
        out += to_whole([ints[r] for r in ranks], rest)
    return out


if __name__ == "__main__":
    peers, without = read_peers(sys.argv[1])
    claims = defaultdict(int)
    for p in peers:
        for v in p:
            claims[v] += 1
    mapped, total = len(claims), sum(map(len, peers))
    several = sum(1 for c in claims.values() if c > 1)
    print(f"node list: {len(peers) + without} peers, {len(peers)} of them with validators; {mapped} validators mapped, "
          f"{100 * several / mapped:.0f} % of them to more than one peer (at most {max(claims.values())})")
    print(f"peers with more than 10 validators: {sum(len(p) > 10 for p in peers)}, holding "
          f"{100 * sum(len(p) for p in peers if len(p) > 10) / total:.1f} % of what is mapped, repeats counted "
          f"(27 Oct call: super nodes hold 96 % of stake)")

    by_size = sorted(range(len(peers)), key=lambda i: len(peers[i]), reverse=True)
    readings = (
        ("each validator on the largest peer that claims it", one_peer_each(peers, by_size)),
        ("each validator split evenly over the peers that claim it", [sum(1 / claims[v] for v in p) for p in peers]),
        ("each validator on the smallest peer that claims it", one_peer_each(peers, by_size[::-1])),
    )
    S0, k0 = 64, 16                                   # section 9: today's subnets and aggregators per subnet
    n0, x0 = V // (32 * S0), need(S0)
    spare = floor(log(0.9) / log(1 - 1 / (n0 // k0)))
    S, d = 64, 4                                      # section 10: aggregators on 4 whole subnets
    x = need(S)
    cube, shuf = cube_layers(4), shuffled_layers(S, d, 4, random.Random(9))     # dispersal.py's draw 1
    for placing, build in (("the measured machines host all 800,000 validators", same_machines),
                           ("the validators that were not mapped sit on further machines of the same shape", more_machines)):
        print(f"\n# {placing}")
        for name, sizes in readings:
            whole = build(sizes, mapped)
            assert sum(whole) == V
            top = sorted(whole, reverse=True)
            f = hosting_figures(whole, n0, spare, x0, k0, S0)
            g = layouts_in_machines(whole, S, d, x, cube, shuf)
            print(f"{name}: {len(whole)} machines; the largest holds {100 * top[0] / V:.1f} % of the validators and the "
                  f"10 largest {100 * sum(top[:10]) / V:.1f} %; more than 1/10 on {machines_for_share(whole, 1, 10)}, "
                  f"1/4 on {machines_for_share(whole, 1, 4)}, 1/3 on {f['third']}, 1/2 on {machines_for_share(whole, 1, 2)}, "
                  f"2/3 on {machines_for_share(whole, 2, 3)}; machines with more than 100 validators hold "
                  f"{100 * sum(v for v in whole if v > 100) / V:.1f} %")
            print(f"  section 9: secret, with the map: one committee {f['one']}, the members of {x0} committees {f['many']} | "
                  f"known: the {x0 * k0} aggregators of {x0} subnets on {f['known']} or fewer | a slot's 64 pq aggregators on {f['pq']}")
            print(f"  section 10: the 64 roles sit on {g['machines']} machines | finality breaks at: pq layout {g['pq']} (exact) | "
                  f"cube {g['cube']} (attack found) | shuffled layers, draw 1: {g['shuffled']} (attack found)", flush=True)
