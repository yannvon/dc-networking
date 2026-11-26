"""Dispersed vs redundant aggregator assignment: threshold tolerance t(q).

Stdlib only, deterministic. Prints every number in ../README.md except the
rows marked exact.py: its CP-SAT rows, the exact loss profile of the cube layers
and the merge counts of section 10 (`exact.py` needs ortools).

Model (terms of properties/aggregation-broadcast.md):
  S subnets, A aggregators, each aggregator covers d subnets, each subnet is
  covered by k aggregators, so A*d = S*k. A subnet has no proof when all k of
  its aggregators fail. t(q) is the fewest failures, chosen by an attacker
  who knows the assignment, that leave more than a share q of the scope's
  subnets without a proof, i.e. at least x = floor(q*S) + 1 of them.
  Equivalently t(q) = min over sets T of x subnets of |N(T)|, the number of
  aggregators touching T (a vertex-expansion / disperser quantity).
"""
import os
import random
import sys
from fractions import Fraction
from itertools import combinations
from bisect import bisect_left, bisect_right
from math import ceil, comb, log, exp, floor


# ---------------------------------------------------------------- assignments

def gf(q):
    """(add, mul) for GF(q), q prime or 4, 8, 16, 32."""
    polys = {4: 0b111, 8: 0b1011, 16: 0b10011, 32: 0b100101}
    if q in polys:
        P, m = polys[q], q.bit_length() - 1

        def mul(a, b):
            r = 0
            while b:
                if b & 1:
                    r ^= a
                b >>= 1
                a <<= 1
                if a >> m:
                    a ^= P
            return r
        return (lambda a, b: a ^ b), mul
    return (lambda a, b: (a + b) % q), (lambda a, b: (a * b) % q)


def redundant(S, d, k):
    """Groups of d subnets, k identical aggregators per group (today: d = 1)."""
    return [tuple(range(g * d, g * d + d)) for g in range(S // d) for _ in range(k)]


def affine_plane(w, k):
    """Subnets = the w^2 points of AG(2, w); aggregators = the lines of k of its
    w + 1 parallel classes. d = w, A = k*w. Each class is a full cover."""
    add, mul = gf(w)
    pt = lambda x, y: x * w + y
    classes = [[tuple(sorted(pt(b, y) for y in range(w))) for b in range(w)]]   # vertical
    for m in range(w):
        classes.append([tuple(sorted(pt(x, add(mul(m, x), b)) for x in range(w))) for b in range(w)])
    return [l for c in classes[:k] for l in c]


def rs_net(d, w, k):
    """Reed-Solomon style: subnets (i, c) for i < d, c in GF(w); S = d*w.
    Aggregator (a, b) covers {(i, a*i + b)}: k slopes a, w offsets b, A = k*w.
    Each slope is a full cover; two aggregators share at most one subnet."""
    add, mul = gf(w)
    return [tuple(i * w + add(mul(a, i), b) for i in range(d)) for a in range(k) for b in range(w)]


def random_biregular(S, d, k, rng):
    A = S * k // d
    while True:
        stubs = [s for s in range(S) for _ in range(k)]
        rng.shuffle(stubs)
        blocks = [tuple(stubs[i * d:(i + 1) * d]) for i in range(A)]
        if all(len(set(b)) == d for b in blocks):
            return blocks


# ---------------------------------------------------------------- tolerance

def need(S, q_num=1, q_den=3):
    """x = floor(q*S) + 1 subnets without a proof (exact rational q)."""
    return (q_num * S) // q_den + 1


def floor_t(S, d, k, x):
    """Any assignment: each lost subnet takes k failures, a failure covers <= d."""
    return -(-k * x // d)


def redundant_t(S, d, k, x):
    return k * (-(-x // d))


def ceiling_t(S, d, k, x):
    """Any assignment: a uniformly random set of f failures loses on average
    S*C(A-k, f-k)/C(A, f) = S*C(f, k)/C(A, k) subnets. The largest loss over
    sets of f failures is a whole number and at least that average, so
    t <= the least f whose average is more than x - 1. Roughly q^(1/k) * A.
    (Oversight edit: "more than x - 1" replaces "reaches x"; it lowers the
    A = 64, k = 4 rows from 50 to 49 and changes no other number in the note.)"""
    A = S * k // d
    for f in range(k, A + 1):
        if S * comb(A - k, f - k) > (x - 1) * comb(A, f):
            return f
    return A


def masks(blocks, S):
    m = [0] * S
    for a, b in enumerate(blocks):
        for s in b:
            m[s] |= 1 << a
    return m


def t_enum(blocks, S, x):
    """Exact min |N(T)| over all x-subsets T (small S only)."""
    m = masks(blocks, S)
    best = len(blocks)
    for T in combinations(range(S), x):
        u = 0
        for s in T:
            u |= m[s]
        c = bin(u).count("1")
        if c < best:
            best = c
    return best


def profile_enum(blocks, S):
    """g[x] = fewest failures that leave >= x subnets without a proof, all x (2^A sets)."""
    A = len(blocks)
    m = masks(blocks, S)
    g = [A + 1] * (S + 1)
    for F in range(1 << A):
        lost = sum(1 for v in m if v & F == v)
        c = bin(F).count("1")
        if c < g[lost]:
            g[lost] = c
    for x in range(S - 1, -1, -1):
        g[x] = min(g[x], g[x + 1])
    return g


def scope_t(g, S_inst, instances, x):
    """Scope of `instances` disjoint copies of one instance with profile g:
    fewest failures losing >= x subnets of the scope (knapsack over copies)."""
    INF = 10 ** 9
    best = [0] + [INF] * x
    for _ in range(instances):
        new = best[:]
        for have in range(x + 1):
            if best[have] == INF:
                continue
            for y in range(1, S_inst + 1):
                tgt = min(x, have + y)
                new[tgt] = min(new[tgt], best[have] + g[y])
        best = new
    return best[x]


def scope_t_capped(g, S_inst, instances, x, cap):
    """As scope_t, with at most `cap` failures in each instance: the instances
    are on duty at different times, and the attacker is limited in how many
    aggregators it fails at the same time. None when no such attack leaves
    >= x subnets without a proof. (Added by the oversight thread.)"""
    INF = 10 ** 9
    best = [0] + [INF] * x
    for _ in range(instances):
        new = best[:]
        for have in range(x + 1):
            if best[have] == INF:
                continue
            for y in range(1, S_inst + 1):
                if g[y] > cap:      # g is non-decreasing
                    break
                tgt = min(x, have + y)
                new[tgt] = min(new[tgt], best[have] + g[y])
        best = new
    return None if best[x] == INF else best[x]


def capped_floor_plane(w, k, instances, x, cap):
    """Lower bound on the failures over a scope of `instances` planes (k
    classes of AG(2, w)) when at most `cap` aggregators fail in each. Tanner's
    bound c(y) = k^2 y w / (w^2 + (k - 1) y) on the failures behind y lost
    subnets of one instance is concave in y, so the cheapest way to split x
    lost subnets fills instances up to the most the cap allows and puts the
    rest in one more. None when the cap rules the attack out. (Added by the
    oversight thread.)"""
    c = lambda y: Fraction(k * k * y * w, w * w + (k - 1) * y)
    ymax = max(y for y in range(w * w + 1) if c(y) <= cap)
    if instances * ymax < x:
        return None
    full, rest = divmod(x, ymax)
    return ceil(full * c(ymax) + c(rest))


def balanced_random(S, d, k, rng):
    """Random assignment with exact loads: each subnet gets k distinct
    aggregators, each aggregator d subnets (shuffle stubs, then swap away
    repeats inside a subnet)."""
    A = S * k // d
    stubs = [a for a in range(A) for _ in range(d)]
    rng.shuffle(stubs)
    subs = [stubs[i * k:(i + 1) * k] for i in range(S)]
    bad = True
    while bad:
        bad = False
        for i in range(S):
            if len(set(subs[i])) < k:
                bad = True
                j, jj = rng.randrange(S), rng.randrange(k)
                ii = rng.randrange(k)
                subs[i][ii], subs[j][jj] = subs[j][jj], subs[i][ii]
    blocks = [[] for _ in range(A)]
    for s, agg in enumerate(subs):
        for a in agg:
            blocks[a].append(s)
    return [tuple(b) for b in blocks]


def complete_design(A, k):
    """One subnet per k-set of aggregators: S = C(A, k), d = C(A-1, k-1)."""
    blocks = [[] for _ in range(A)]
    for s, agg in enumerate(combinations(range(A), k)):
        for a in agg:
            blocks[a].append(s)
    return [tuple(b) for b in blocks]


def lost_all(blocks, S):
    """lost[F] = subnets whose aggregators all lie in F, for every F (zeta
    transform over 2^A; fine up to A ~ 20)."""
    A = len(blocks)
    cnt = [0] * (1 << A)
    for v in masks(blocks, S):
        cnt[v] += 1
    for i in range(A):
        bit = 1 << i
        for F in range(1 << A):
            if F & bit:
                cnt[F] += cnt[F ^ bit]
    return cnt


def t_zeta(blocks, S, x):
    lost = lost_all(blocks, S)
    return min(bin(F).count("1") for F in range(1 << len(blocks)) if lost[F] >= x)


def random_guarantee(A, k, S, x):
    """Union bound for an assignment where each subnet picks a uniform random
    k-set of the A aggregators: P(t <= f) <= sum_{f' <= f} C(A, f') *
    P(Bin(S, C(f',k)/C(A,k)) >= x). Returns the least f at which that sum
    reaches 1/2: a random draw has t >= f with probability > 1/2."""
    def tail(n, p, m):
        if p == 0:
            return 0.0
        if p >= 1:
            return 1.0
        # first term in logs (lgamma), then ratios; stop once terms are negligible
        from math import lgamma
        lt = lgamma(n + 1) - lgamma(m + 1) - lgamma(n - m + 1) + m * log(p) + (n - m) * log(1 - p)
        term, tot, r = exp(lt), 0.0, p / (1 - p)
        for j in range(m, n + 1):
            tot += term
            if term < 1e-30 * max(tot, 1e-300) and j > n * p:
                break
            term *= (n - j) / (j + 1) * r
        return min(tot, 1.0)
    acc = 0.0
    for f in range(A + 1):
        acc += comb(A, f) * tail(S, comb(f, k) / comb(A, k), x)
        if acc >= 0.5:
            return f
    return A


# ---------------------------------------------------------------- asymptotics

def H(p):
    return 0.0 if p in (0, 1) else -p * log(p) - (1 - p) * log(1 - p)


def rate(phi, q, k):
    """Large-deviation rate per subnet for 'a fixed set holding a share phi of
    aggregator slots contains >= q of the subnets entirely', random biregular
    assignment: min KL(e || Bin(k, phi)) with mean k*phi and e_k >= q."""
    if phi ** k >= q:
        return 0.0
    b = [comb(k, j) * phi ** j * (1 - phi) ** (k - j) for j in range(k)]
    target = (k * phi - k * q) / (1 - q)            # mean of j over j < k
    if target <= 0:
        return float("inf")
    lo, hi = -50.0, 50.0
    for _ in range(200):
        lam = (lo + hi) / 2
        w = [b[j] * exp(lam * j) for j in range(k)]
        mean = sum(j * w[j] for j in range(k)) / sum(w)
        lo, hi = (lam, hi) if mean < target else (lo, lam)
    w = [b[j] * exp(lam * j) for j in range(k)]
    Z = sum(w)
    e = [(1 - q) * wj / Z for wj in w]
    return q * log(q / phi ** k) + sum(e[j] * log(e[j] / b[j]) for j in range(k) if e[j] > 0)


def random_assignment_share(d, k, q):
    """First-moment bound: as S -> infinity, a random biregular assignment has
    t(q)/A >= this share with high probability (expected number of failure
    sets of that size that lose a share q of subnets goes to 0)."""
    phi, step = 1e-4, 1e-4
    while phi < 1:
        if H(phi) >= (d / k) * rate(phi, q, k):
            return phi
        phi += step
    return 1.0


# ---------------------------------------------------------------- random failures

def p_break_redundant(S, d, k, p, x):
    """P(>= x subnets lost) when each aggregator fails independently w.p. p."""
    G, r = S // d, p ** k
    gx = -(-x // d)
    return sum(comb(G, j) * r ** j * (1 - r) ** (G - j) for j in range(gx, G + 1))


def p_break_mc(blocks, S, p, x, runs, rng):
    m = masks(blocks, S)
    A = len(blocks)
    hit = 0
    for _ in range(runs):
        F = 0
        for a in range(A):
            if rng.random() < p:
                F |= 1 << a
        if sum(1 for v in m if v & F == v) >= x:
            hit += 1
    return hit / runs


# ---------------------------------------------------------------- machines (sections 9 and 10)

def supernode_shape(V, big, small):
    """`big` machines that share, as evenly as possible, the validators the small ones leave."""
    q, r = divmod(V - sum(small), big)
    return [q + 1] * r + [q] * (big - r) + list(small)


def hosting_scenarios():
    """(label, validators per machine), each for 800,000 validators. Validators are not spread
    evenly over machines (Yann, 2026-11-25), so the even spread that aggregator selection's
    script also has is left out. What is left are two kinds of approximation:
    - the shape Heimbach et al. measured, as ../../../pq-gasper/sim/blind_attack.py builds it;
    - the shapes this repo's benchmarks run with (benchmarking/): supernodes that share the
      validators evenly, and home nodes with one to three each. devnet-0 is "about 1/8 of
      mainnet" with 200 supernodes and 800 home nodes of one validator. eth-slot-sim is "1/2 the
      mainnet size" with 2,000 cloud nodes of 100 to 1,000 validators, 200 on average, and
      2,000 home nodes of 2 to 3; here every cloud node gets the average.
    The figures under a measured node list come from measured.py, which needs the list; the list
    is not in this repo."""
    sys.dont_write_bytecode = True
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(here, "..", "..", "..", "pq-gasper", "sim"))
    import blind_attack
    V = blind_attack.V
    out = [(label, blind_attack.scenario(key, machines))
           for key, machines, label in blind_attack.SCENARIOS if key != "even"]
    out.append(("benchmark shape of devnet-0 at mainnet scale: 1,600 supernodes with 496 validators, "
                "6,400 home nodes with 1", supernode_shape(V, 1_600, [1] * 6_400)))
    out.append(("benchmark shape of eth-slot-sim at mainnet scale: 4,000 cloud nodes with 197 or 198 "
                "validators, 4,000 home nodes with 2 or 3", supernode_shape(V, 4_000, [2, 3] * 2_000)))
    return out


def machines_for_share(sizes, num, den):
    """Fewest machines that together hold more than num/den of the validators."""
    total, acc = sum(sizes), 0
    for used, size in enumerate(sorted(sizes, reverse=True), 1):
        acc += size
        if den * acc > num * total:
            return used


def machines_of(cum, validators):
    """How many of the given validators each machine hosts, most-loaded machine first.
    cum[j] is the number of validators on machines 0..j."""
    counts = {}
    for v in validators:
        j = bisect_right(cum, v)
        counts[j] = counts.get(j, 0) + 1
    return sorted(counts.values(), reverse=True)


def hosting_figures(sizes, n0, spare, x0, k0, S0, seed=6):
    """Section 9's figures in machines for one way validators sit on machines (`sizes`:
    validators per machine). Medians over random draws of who is in a committee of n0 and who
    aggregates:
      third  the fewest machines that hold more than a third of the validators;
      one    machines hosting all but `spare` members of one committee, most-loaded first;
      many   machines hosting a member of any of x0 committees;
      known  machines hosting the k0 aggregators of each of x0 subnets, where the attacker
             takes the subnets greedily, fewest new machines first (so: that many or fewer);
      pq     machines hosting a slot's 64 aggregators."""
    V = sum(sizes)
    cum, run = [], 0
    for size in sizes:
        run += size
        cum.append(run)
    rng = random.Random(seed)
    median = lambda xs: sorted(xs)[len(xs) // 2]
    one = []
    for _ in range(300):
        covered = 0
        for used, c in enumerate(machines_of(cum, rng.sample(range(V), n0)), 1):
            covered += c
            if covered >= n0 - spare:
                break
        one.append(used)
    many = [len(machines_of(cum, rng.sample(range(V), x0 * n0))) for _ in range(40)]
    known = []
    for _ in range(300):
        subs = [set(bisect_right(cum, v) for v in rng.sample(range(V), k0)) for _ in range(S0)]
        hit, left = set(), list(range(S0))
        for _ in range(x0):
            best = min(left, key=lambda s: len(subs[s] - hit))
            hit |= subs[best]
            left.remove(best)
        known.append(len(hit))
    pq = [len(machines_of(cum, rng.sample(range(V), 64))) for _ in range(300)]
    return {"third": machines_for_share(sizes, 1, 3), "one": median(one), "many": median(many),
            "known": median(known), "pq": median(pq)}


def by_machine(blocks, owners):
    """One coverage set per machine: the subnets of all the aggregators it hosts (owners[a] is
    the machine of aggregator a). Silencing a machine silences those together, so t counted in
    machines is t of these merged sets."""
    merged = {}
    for b, m in zip(blocks, owners):
        merged.setdefault(m, set()).update(b)
    return [tuple(sorted(v)) for v in merged.values()]


def groups_t_in_machines(owners, k, groups_needed):
    """Exact t in machines for redundant(S, d, k), where aggregators g*k .. g*k + k - 1 prove
    group g: a subnet is lost only with its whole group, so it is the fewest machines that host
    every aggregator of `groups_needed` groups."""
    ids = {}
    masks = [0] * (len(owners) // k)
    for a, m in enumerate(owners):
        masks[a // k] |= 1 << ids.setdefault(m, len(ids))
    best = len(ids)

    def go(i, left, mask):
        nonlocal best
        if not left:
            best = min(best, bin(mask).count("1"))
        elif len(masks) - i >= left and bin(mask).count("1") < best:
            go(i + 1, left - 1, mask | masks[i])
            go(i + 1, left, mask)
    go(0, groups_needed, 0)
    return best


def layouts_in_machines(sizes, S, d, x, cube, shuffled, draws=30, seed=8):
    """Section 10 in machines, for 64 aggregators with k = 4. Each draw gives the 64 roles to
    distinct validators picked evenly, so to machines by their share of the validators. Medians
    over the draws of: the machines the roles sit on, and the fewest machines whose silence
    leaves x subnets without a proof. That is exact for the pq layout. For the cube and the
    shuffled layers it is an attack found by annealing, so the true value is that or lower."""
    cum, run = [], 0
    for size in sizes:
        run += size
        cum.append(run)
    rng = random.Random(seed)
    median = lambda xs: sorted(xs)[len(xs) // 2]
    out = {"machines": [], "pq": [], "cube": [], "shuffled": []}
    for _ in range(draws):
        owners = [bisect_right(cum, v) for v in rng.sample(range(run), 64)]
        out["machines"].append(len(set(owners)))
        out["pq"].append(groups_t_in_machines(owners, 4, -(-x // d)))
        for name, blocks in (("cube", cube), ("shuffled", shuffled)):
            out[name].append(attack(by_machine(blocks, owners), S, x, rng, restarts=3, steps=15_000)[0])
    return {name: median(v) for name, v in out.items()}


# ---------------------------------------------------------------- whole subnets (section 10)
# A layer is one pass of a round robin: S/d aggregators take d subnets each and together take
# every subnet once. k layers give replication k and A = k*S/d aggregators.

def sliding_windows(S, d):
    """Round robin on a ring: every layer deals windows of d consecutive subnets, and each
    layer starts one subnet further on. After d layers every window has one aggregator: k = d."""
    return [tuple(sorted((d * j + c + i) % S for i in range(d))) for c in range(d) for j in range(S // d)]


def shuffled_layers(S, d, k, rng):
    """Every layer deals a fresh shuffle of the S subnets, d to each of its S/d aggregators."""
    blocks = []
    for _ in range(k):
        order = list(range(S))
        rng.shuffle(order)
        blocks += [tuple(sorted(order[d * j:d * j + d])) for j in range(S // d)]
    return blocks


CUBE_DIRECTIONS = ((0, 0, 1), (0, 1, 0), (1, 0, 0), (1, 1, 1))


def cube_layers(k):
    """64 subnets as the points of a 4 x 4 x 4 grid, coordinates mod 4. Layer c is the 16 lines
    of direction CUBE_DIRECTIONS[c], 4 subnets each. Two lines of one layer share no subnet and
    two lines of different layers share at most one (section 10 prints the check)."""
    blocks = []
    for v in CUBE_DIRECTIONS[:k]:
        seen = set()
        for p in range(64):
            if p not in seen:
                q = (p // 16, p // 4 % 4, p % 4)
                line = tuple(sorted(sum((q[j] + i * v[j]) % 4 * 4 ** (2 - j) for j in range(3))
                                    for i in range(4)))
                seen.update(line)
                blocks.append(line)
    return blocks


def independent_picks(S, d, A, rng):
    """No layers: every aggregator draws its d subnets on its own."""
    return [tuple(sorted(rng.sample(range(S), d))) for _ in range(A)]


def touching(blocks, subnets):
    """The aggregators that cover at least one of the given subnets."""
    inside = set(subnets)
    return [a for a, b in enumerate(blocks) if inside.intersection(b)]


def attack(blocks, S, x, rng, restarts=8, steps=40_000):
    """An attack found by annealing over sets of x subnets: (the number of aggregators that
    touch the set, the set). Silencing those aggregators leaves the x subnets without a proof,
    so the number is an upper bound on t. It is not a lower bound: a better set may exist."""
    A = len(blocks)
    cover = [[] for _ in range(S)]
    for a, b in enumerate(blocks):
        for s in b:
            cover[s].append(a)
    hot = max(1.0, A / (2 * S))
    cool = 0.02 ** (1 / steps)
    best, best_set = A + 1, None
    for _ in range(restarts):
        order = list(range(S))
        rng.shuffle(order)
        inside, outside = order[:x], order[x:]
        cnt = [0] * A
        for s in inside:
            for a in cover[s]:
                cnt[a] += 1
        cost = sum(1 for c in cnt if c)
        if cost < best:
            best, best_set = cost, tuple(sorted(inside))
        temp = hot
        for _ in range(steps):
            temp *= cool
            i, j = int(rng.random() * x), int(rng.random() * (S - x))
            out, new = inside[i], outside[j]
            delta = 0
            for a in cover[out]:
                cnt[a] -= 1
                if not cnt[a]:
                    delta -= 1
            for a in cover[new]:
                if not cnt[a]:
                    delta += 1
                cnt[a] += 1
            if delta <= 0 or rng.random() < exp(-delta / temp):
                inside[i], outside[j] = new, out
                cost += delta
                if cost < best:
                    best, best_set = cost, tuple(sorted(inside))
            else:
                for a in cover[new]:
                    cnt[a] -= 1
                for a in cover[out]:
                    cnt[a] += 1
    assert len(touching(blocks, best_set)) == best
    return best, best_set


def layers_guarantee(S, d, k, x, eps):
    """k shuffled layers: t >= the returned f, except with probability eps over the shuffles.
    First moment. A fixed set of x subnets meets g of a layer's S/d groups with the probability
    that a random set of x meets g groups of a fixed deal. The layers are independent, so the
    number of aggregators that touch the set is a sum of k such counts. f is the least count at
    which the expected number of sets of x subnets touched by at most f aggregators reaches eps."""
    G = S // d
    poly, law = [1], [0] * (G + 1)
    for g in range(1, G + 1):                    # poly = ((1 + z)^d - 1)^g, up to z^x
        nxt = [0] * min(len(poly) + d, x + 1)
        for i, c in enumerate(poly):
            if c:
                for j in range(1, d + 1):
                    if i + j <= x:
                        nxt[i + j] += c * comb(d, j)
        poly = nxt
        if len(poly) > x:
            law[g] = comb(G, g) * poly[x]
    sets = comb(S, x)
    assert sum(law) == sets
    dist = [Fraction(1)]
    for _ in range(k):
        new = [Fraction(0)] * (len(dist) + G)
        for i, p in enumerate(dist):
            if p:
                for g in range(1, G + 1):
                    if law[g]:
                        new[i + g] += p * Fraction(law[g], sets)
        dist = new
    acc = Fraction(0)
    for f, p in enumerate(dist):
        acc += p
        if acc * sets >= eps:
            return f
    return len(dist) - 1


def ceiling_cover(S, d, A, x):
    """Any assignment in which every aggregator covers d subnets: a random set of x subnets
    touches an aggregator with probability 1 - C(S-x, d)/C(S, d), and some set touches no more
    aggregators than the average. Roughly (1 - (1 - q)^d) * A; it binds once k is large."""
    return A * (comb(S, d) - comb(S - x, d)) // comb(S, d)


def tanner(S, d, k, x, mu):
    """Tanner's bound: any x subnets touch at least k^2 x / (mu + (k d - mu) x / S) aggregators,
    where mu is the second-largest eigenvalue of M M^T (M the subnet-by-aggregator incidence)."""
    return ceil(Fraction(k * k * x) / (mu + Fraction((k * d - mu) * x, S)))


def cube_eigenvalues(k):
    """Eigenvalues of M M^T for cube_layers(k), k = 3 or 4, with multiplicities. Checks that
    B (B - 4)(B - 8)(B - 4k) = 0, solves the multiplicities of 4 and 8 from the traces of B and
    B^2 with 4k taken once, and checks them against the trace of B^3."""
    B = [[0] * 64 for _ in range(64)]
    for blk in cube_layers(k):
        for s in blk:
            for r in blk:
                B[s][r] += 1

    def mul(P, Q):
        Qt = list(zip(*Q))
        return [[sum(p * q for p, q in zip(row, col)) for col in Qt] for row in P]

    def shift(P, c):
        return [[P[i][j] - (c if i == j else 0) for j in range(64)] for i in range(64)]
    top = 4 * k
    zero = mul(mul(mul(B, shift(B, 4)), shift(B, 8)), shift(B, top))
    assert all(v == 0 for row in zero for v in row)
    B2 = mul(B, B)
    tr = [sum(M[i][i] for i in range(64)) for M in (B, B2, mul(B2, B))]
    m8 = Fraction(tr[1] - top * top - 4 * (tr[0] - top), 32)
    m4 = Fraction(tr[0] - top - 8 * m8, 4)
    assert m4.denominator == m8.denominator == 1 and 64 * m4 + 512 * m8 + top ** 3 == tr[2]
    return {top: 1, 8: int(m8), 4: int(m4), 0: 63 - int(m4) - int(m8)}


def cube3_floor(x):
    """cube_layers(3), the three axis directions. A subnet (a, b, c) has no proof when its three
    lines failed, i.e. (a, b), (a, c) and (b, c) lie in the three sets of failed lines. By the
    Loomis-Whitney inequality the lost subnets number at most the square root of the product of
    the three set sizes. Returns the least total of three sizes whose product reaches x^2."""
    for f in range(3, 49):
        if max(a * b * (f - a - b) for a in range(1, 17) for b in range(1, 17) if 1 <= f - a - b <= 16) >= x * x:
            return f


def p_all_covered(S, d, m):
    """m aggregators that each draw d of S subnets on their own leave no subnet out."""
    return float(sum((-1) ** j * comb(S, j) * Fraction(comb(S - j, d), comb(S, d)) ** m
                     for j in range(S - d + 1)))


def disjoint_cover(blocks, S, alive):
    """Whether S/d of the alive aggregators cover every subnet once: an exact-cover search that
    always branches on the uncovered subnet with the fewest usable aggregators."""
    by = [[] for _ in range(S)]
    for a in alive:
        for s in blocks[a]:
            by[s].append(a)
    covered = [False] * S

    def go(left):
        if not left:
            return True
        best = None
        for s in range(S):
            if not covered[s]:
                opts = [a for a in by[s] if not any(covered[r] for r in blocks[a])]
                if best is None or len(opts) < len(best):
                    best = opts
                    if len(opts) <= 1:
                        break
        for a in best:
            for r in blocks[a]:
                covered[r] = True
            if go(left - len(blocks[a])):
                return True
            for r in blocks[a]:
                covered[r] = False
        return False
    return go(S)


# ---------------------------------------------------------------- report

def net_guarantee(w, k, x):
    """Tanner's spectral bound for k parallel classes of AG(2, w): the
    incidence matrix M has M M^T eigenvalues k*w, w, 0, so any x subnets touch
    at least k^2 x / (w + (k - 1) x / w) aggregators. As a share of A = k*w
    with x = q*w^2: k q / (1 + (k - 1) q)."""
    return -(-k * k * x * w // (w * w + (k - 1) * x))


if __name__ == "__main__":
    rng = random.Random(1)
    Q = 1 / 3

    print("# 1. Yann's example: S = A = 16, d = k = 4, finality q = 1/3 (x = 6)")
    S, d, k = 16, 4, 4
    x = need(S)
    red, pl = redundant(S, d, k), affine_plane(4, 4)
    g_red, g_pl = profile_enum(red, S), profile_enum(pl, S)
    print(f"floor {floor_t(S, d, k, x)}, redundant {g_red[x]}, plane {g_pl[x]} "
          f"(Tanner bound {net_guarantee(4, 4, x)}), ceiling (any assignment) {ceiling_t(S, d, k, x)}")
    print("fewest failures to lose >= j subnets, j = 0..16")
    print("  redundant", g_red)
    print("  plane    ", g_pl)
    covered = lambda g, alive: S - max(j for j in range(S + 1) if g[j] <= A_ - alive)
    A_ = 16
    for alive in (4, 5, 8):
        print(f"  any {alive} live aggregators cover >= {covered(g_pl, alive)} subnets (plane), "
              f">= {covered(g_red, alive)} (redundant)")
    draws = [t_enum(random_biregular(S, d, k, rng), S, x) for _ in range(200)]
    print("200 random biregular draws:", {v: draws.count(v) for v in sorted(set(draws))})
    for I in (8, 32):
        X = need(S * I)
        print(f"scope of {I} instances ({S*I} subnets, {16*I} aggregators, x = {X}): "
              f"floor {floor_t(S*I, d, k, X)}, redundant {scope_t(g_red, S, I, X)}, "
              f"plane {scope_t(g_pl, S, I, X)}")

    print("\n# 2. Same load (A = 16, k = 4), finer subnets: exact t(1/3)")
    print(f"{'S':>5} {'d':>4} | red ceil | 5 balanced random draws | union bound (t >=, p > 1/2)")
    rng = random.Random(3)
    for S in (16, 32, 64, 128, 256, 512):
        d, x = S * 4 // 16, need(S)
        ts = sorted(t_zeta(balanced_random(S, d, 4, rng), S, x) for _ in range(5))
        print(f"{S:>5} {d:>4} | {redundant_t(S, d, 4, x):>3} {ceiling_t(S, d, 4, x):>4} | {str(ts):<23} | "
              f"{random_guarantee(16, 4, S, x)}")
    S = comb(16, 4)
    print(f"{S:>5} {S*4//16:>4} | complete design (one subnet per 4-set of aggregators): "
          f"t = {t_zeta(complete_design(16, 4), S, need(S))}")

    print("\n# 3. Same load, A aggregators per instance: t(1/3) by subnet count S (d = S k / A)")
    for A, k in ((64, 4), (64, 2), (64, 8), (128, 4)):
        G = A // k
        print(f"A = {A}, k = {k}: floor/redundant {redundant_t(G, 1, k, need(G))} at any S")
        for S in (64, 128, 256, 1024, 4096, 16384):
            if S * k % A:
                continue
            d, x = S * k // A, need(S)
            w = int(round(S ** 0.5))
            net = f"  plane (w = {w}) >= {net_guarantee(w, k, x)}" if w * w == S and k * w == A else ""
            print(f"  S = {S:>6}, d = {d:>5}: random >= {random_guarantee(A, k, S, x):>3}, "
                  f"ceiling {ceiling_t(S, d, k, x):>3}{net}")
    print("share of A, large S:  floor q = 0.333 | plane k q/(1+(k-1)q) | ceiling q^(1/k)")
    for k in (2, 3, 4, 8, 16):
        print(f"  k = {k:>2}: {Q:.3f} | {k*Q/(1+(k-1)*Q):.3f} | {Q**(1/k):.3f}   ceiling/floor {Q**(1/k)/Q:.2f}")

    print("\n# 4. Fixed d, scope growing (A, S -> infinity together): random assignment, share of A")
    print(" k  ceiling | first-moment lower bound by d")
    for k in (2, 4, 8):
        row = "  ".join(f"d={d}: {random_assignment_share(d, k, Q):.3f}" for d in (2, 4, 8, 16, 64))
        print(f"{k:>2}  {Q**(1/k):.3f}   | {row}")

    print("\n# 5. PQ Gasper epoch (32 slots), 64 aggregators per slot, dispersal inside each slot")
    for S_slot, d in ((16, 1), (64, 4), (256, 16)):
        S_all = 32 * S_slot
        X = need(S_all)
        full, rest = divmod(X, S_slot)
        print(f"  {S_slot:>3} subnets/slot, d = {d:>2}: redundant {redundant_t(S_all, d, 4, X)} floods/epoch; "
              f"any per-slot assignment <= {full * 64 + (64 if rest else 0)} "
              f"({full} whole slots + one partial)")

    print("\n# 6. Random failures (each aggregator fails w.p. p): P(>= 6 of 16 subnets lost)")
    S, d, k = 16, 4, 4
    x = need(S)
    rng = random.Random(2)
    for p in (0.4, 0.5, 0.6, 0.7):
        print(f"p = {p}: redundant {p_break_redundant(S, d, k, p, x):.4f}, "
              f"plane {p_break_mc(affine_plane(4, 4), S, p, x, 200_000, rng):.4f}  "
              f"(expected lost share p^k = {p**k:.3f} for both)")

    # Added by the oversight thread on integration. With V votes in the scope, first-level
    # proving is k*V signatures, each aggregator proves k*V/A of them, and there are A proofs.
    print("\n# 7. Fewer aggregators or less replication, against redundant k = 4 with A = 64")
    base_A, base_k = 64, 4
    G = base_A // base_k
    print(f"baseline: t = {redundant_t(G, 1, base_k, need(G))}, per-vote tolerance {base_k}; "
          f"load per aggregator, first-level proving and proofs below are relative to it")
    for A, k in ((48, 3), (32, 2), (32, 4), (64, 2)):
        w = A // k
        S = w * w
        x = need(S)
        print(f"  plane A = {A}, k = {k} (w = {w}, S = {S}): t >= {net_guarantee(w, k, x)}, "
              f"ceiling {ceiling_t(S, w, k, x)}; load per aggregator x{k * base_A / (A * base_k):.2f}, "
              f"proving x{k / base_k:.2f}, proofs x{A / base_A:.2f}, per-vote tolerance {k}, "
              f"full merge of {A // k} children (baseline {base_A // base_k})")

    # Added by the oversight thread on integration. Sections 1 and 5 count failures over the
    # whole scope. Here the attacker is limited in how many aggregators it fails at the same
    # time, and each instance (slot) is on duty at a different time: at most c failures in each.
    print("\n# 8. Failures counted at one time: at most c failed aggregators in each instance")
    S = 16
    caps = (4, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16)
    show = lambda v: "   -" if v is None else f"{v:>4}"
    for I in (8, 32):
        X = need(S * I)
        print(f"scope of {I} instances of the example (x = {X}): fewest failures over the scope, by c")
        print("  c        ", " ".join(f"{c:>4}" for c in caps))
        print("  redundant", " ".join(show(scope_t_capped(g_red, S, I, X, c)) for c in caps))
        print("  plane    ", " ".join(show(scope_t_capped(g_pl, S, I, X, c)) for c in caps))
    print("PQ Gasper epoch (32 slots), 64 aggregators per slot, k = 4: floods per epoch, by c")
    g_d1 = [4 * y for y in range(17)]           # d = 1: y lost subnets take 4 y failures
    X = need(32 * 16)
    caps = (20, 23, 24, 42, 43, 48, 56, 64)
    print("  c                                  ", " ".join(f"{c:>5}" for c in caps))
    print("  redundant, 16 subnets/slot         ",
          " ".join(f"{show(scope_t_capped(g_d1, 16, 32, X, c)):>5}" for c in caps))
    X = need(32 * 256)
    print("  plane, 256 subnets/slot, at least  ",
          " ".join(f"{show(capped_floor_plane(16, 4, 32, X, c)):>5}" for c in caps))
    print(f"  one slot of that plane: t >= {net_guarantee(16, 4, need(256))}, "
          f"ceiling {ceiling_t(256, 16, 4, need(256))}; whole slots: <= 704 (section 5)")

    # Added by the oversight thread on 2026-11-25, when Yann set today's p2p stack as the baseline:
    # 64 subnets per slot and 16 aggregators on each. A committee has about 390 validators at
    # 800,000. A subnet's topic has about 400 to 500 nodes, which is another number (Yann, same
    # day): default nodes are on 2 of the 64 subnets, and a node can run many validators.
    # Figures count aggregators; they are machines when every aggregator runs on its own.
    # Finality: more than a third of a slot's votes.
    print("\n# 9. Against today's p2p stack: 64 subnets per slot, 16 aggregators per subnet")
    S0, k0 = 64, 16
    A0, n0, x0 = S0 * k0, 800_000 // (32 * S0), need(S0)
    base = redundant_t(S0, 1, k0, x0)
    print(f"committee {n0} validators, {A0} aggregators per slot; finality is lost with {x0} of {S0} subnets")
    print(f"aggregators known, exactly {k0} per subnet: one committee {k0} aggregators; finality {base} aggregators per slot")
    mod = n0 // k0                                   # today's lottery: aggregate if hash mod (n // 16) == 0
    pmf = [comb(n0, j) * (1 / mod) ** j * (1 - 1 / mod) ** (n0 - j) for j in range(n0 + 1)]
    cum, run = [], 0.0
    for v in pmf:
        run += v
        cum.append(run)
    rng = random.Random(4)
    draws = sorted(sum(sorted(min(bisect_left(cum, rng.random()), n0) for _ in range(S0))[:x0])
                   for _ in range(20_000))
    print(f"aggregators known, today's lottery (Binomial({n0}, 1/{mod}) per subnet, mean {n0 / mod:.2f}): "
          f"finality at the {x0} thinnest subnets, mean {sum(draws) / len(draws):.0f} aggregators per slot, "
          f"5 % to 95 % of slots {draws[len(draws) // 20]} to {draws[-len(draws) // 20]}")
    # Aggregators secret, a blind attacker that sees the nodes on a subnet's topic and not which of
    # them aggregate (Yann: 16 out of about 400). A default node backs 2 neighbouring subnets
    # (compute_subscribed_subnet in phase0/p2p-interface.md), so the nodes on a run of x subnets
    # are those of x + 1 starting points out of 64.
    for nodes in (400, 500):
        spared = max(j for j in range(nodes) if comb(nodes - j, k0) >= 0.9 * comb(nodes, k0))
        print(f"aggregators secret, the attacker sees the {nodes} nodes on a subnet and not which {k0} of them "
              f"aggregate: {nodes - spared} of them for a 90 % chance; finality: every node on {x0} neighbouring "
              f"subnets, {(x0 + 1) * nodes // 2} of the {S0 * nodes // 2} default nodes")
    # The other blind attacker (aggregator-selection.md): it has a map from validators to machines
    # and floods the machines of the committee's members, most-loaded first.
    spare = floor(log(0.9) / log(1 - 1 / mod))
    print(f"aggregators secret, the attacker has a map from validators to machines: the machines of all but "
          f"{spare} of the committee's {n0} members for a 90 % chance")
    print("machines, by how validators sit on them (medians over random draws; validators are not spread evenly):")
    for label, sizes in hosting_scenarios():
        f = hosting_figures(sizes, n0, spare, x0, k0, S0)
        print(f"  {label}: a third of the validators on {f['third']} machines | secret, with the "
              f"map: one committee {f['one']}, the members of {x0} committees {f['many']} | known: the "
              f"{x0 * k0} aggregators of {x0} subnets on {f['known']} or fewer | a slot's 64 pq aggregators on {f['pq']}")

    # A committee is captured by a share b of stake when no aggregator of it is outside the share
    # (the model of aggregator-selection.md). Withholding halts finality once under 2/3 still votes.
    capt = lambda b: (1 - (1 - b) / mod) ** n0
    b_lo, b_hi = 0.0, 1 / 3
    for _ in range(60):
        b_mid = (b_lo + b_hi) / 2
        b_lo, b_hi = (b_lo, b_mid) if (1 - b_mid) * (1 - capt(b_mid)) < 2 / 3 else (b_mid, b_hi)
    print(f"a share of stake censoring or withholding (today's lottery): at 1/3 a committee has no aggregator "
          f"outside it with probability {100 * capt(1 / 3):.4f} %; withholding alone halts finality from "
          f"{100 * b_hi:.1f} % of stake")

    # Added by the oversight thread on 2026-11-25 for the design Yann described that day: the
    # baseline's 64 subnets stay, and an aggregator proves d = 4 whole subnets of them, chosen at
    # random or round robin. 4 x 390 signatures is what one aggregator proves in the pq spec.
    # An earlier end of section 9 cut every committee into 64 slices. Yann rejected it, because
    # an aggregator would have to be in many more subnets, and it is removed.
    print("\n# 10. Aggregators on d = 4 whole subnets of the baseline's 64 (the pq spec's load)")
    S, d = 64, 4
    x = need(S)
    print(f"load: {d} of {S} subnets is a {S // d}th of the slot's voters, {d * 800_000 / 32 / S:,.1f} signatures at "
          f"800,000 validators, the same as one of the pq spec's 16 committees; finality is lost with {x} of {S} subnets")
    rng = random.Random(9)
    designs = [("pq layout: the same deal in every layer", redundant(S, d, 4)),
               ("sliding windows: the deal shifted by one per layer", sliding_windows(S, d)),
               ("cube: another direction of lines per layer", cube_layers(4))]
    designs += [(f"shuffled layers, draw {i + 1}", shuffled_layers(S, d, 4, rng)) for i in range(3)]
    designs += [(f"independent picks, draw {i + 1}", independent_picks(S, d, 64, rng)) for i in range(3)]
    spec4, spec3 = cube_eigenvalues(4), cube_eigenvalues(3)
    lower = {0: f"= {redundant_t(S, d, 4, x)} (groups)", 1: f"= {x + d - 1} (x + d - 1: a run of x subnets on the ring)",
             2: f">= {tanner(S, d, 4, x, 8)} (Tanner, eigenvalues {spec4}); exact in exact.py"}
    print("64 aggregators, k = 4, in 4 layers of 16 (the last three rows have no layers):")
    print("  aggregators per subnet, min..max | most subnets two aggregators share | best attack found, t <= | t")
    for i, (name, b) in enumerate(designs):
        per = [0] * S
        for blk in b:
            assert len(set(blk)) == d
            for s in blk:
                per[s] += 1
        share = max(len(set(b[i_]) & set(b[j_])) for i_ in range(len(b)) for j_ in range(i_))
        hit, _ = attack(b, S, x, random.Random(1))
        note = lower.get(i, f">= {layers_guarantee(S, d, 4, x, 1e-9)} except w.p. 1e-9 over the shuffles" if i < 6
                         else f"no bound computed; {per.count(0)} subnet(s) with no aggregator")
        print(f"  {name:<51} {min(per)}..{max(per)} | {share} | {hit} | {note}")
    print(f"  ceiling for any assignment of 64 aggregators on 4 subnets each: "
          f"{min(ceiling_t(S, d, 4, x), ceiling_cover(S, d, 64, x))}")
    print(f"independent picks, 64 aggregators: {S * (1 - d / S) ** 64:.2f} subnets with no aggregator on average; "
          "every subnet has one with probability "
          + ", ".join(f"{p_all_covered(S, d, A):.3f} at A = {A}" for A in (64, 128, 256)))

    print("by the number of layers k (A = 16 k aggregators on 4 subnets each):")
    print("    k     A | pq layout | shuffled layers: t >= (w.p. 1 - 1e-9) | attack on one draw, t <= | ceiling | "
          "aggregators per committee the pq layout needs for the guarantee")
    for k in (2, 3, 4, 6, 8, 16, 32, 64):
        A = 16 * k
        lo = layers_guarantee(S, d, k, x, 1e-9)
        hit, _ = attack(shuffled_layers(S, d, k, random.Random(100 + k)), S, x, random.Random(1), restarts=4, steps=30_000)
        print(f"  {k:>3} {A:>5} | {6 * k:>4} | {lo:>4} (x{lo / (6 * k):.2f}) | {hit:>4} | "
              f"{min(ceiling_t(S, d, k, x), ceiling_cover(S, d, A, x)):>4} | {-(-lo // 6)}")
    k352 = next(k for k in range(1, 65) if layers_guarantee(S, d, k, x, 1e-9) >= 352)
    print(f"today's 352 (16 known aggregators on each of 64 subnets, 1,024 in all): shuffled layers guarantee it from "
          f"k = {k352}, {16 * k352} aggregators (t >= {layers_guarantee(S, d, k352, x, 1e-9)}); the pq layout from "
          f"{-(-352 // 6)} per committee, {16 * -(-352 // 6)} aggregators")
    hit3, _ = attack(cube_layers(3), S, x, random.Random(1))
    s3 = shuffled_layers(S, d, 3, random.Random(103))
    print(f"three layers, 48 aggregators, against the pq layout's 24 with 64: cube {max(tanner(S, d, 3, x, 8), cube3_floor(x))} "
          f"<= t <= {hit3} (Loomis-Whitney {cube3_floor(x)}, Tanner {tanner(S, d, 3, x, 8)}, eigenvalues {spec3}; exact in "
          f"exact.py); shuffled {layers_guarantee(S, d, 3, x, 1e-9)} <= t (w.p. 1 - 1e-9), <= {attack(s3, S, x, random.Random(1))[0]} on one draw")

    print("what m aggregates cover, nothing failed (64 subnets):")
    print("  m of the 64 taken at random, any assignment with k = 4: expected subnets covered "
          + ", ".join(f"{m}: {S * (1 - comb(60, m) / comb(64, m)):.1f}" for m in (16, 20, 24, 32, 48)))
    r = random.Random(5)
    cube, shuf = designs[2][1], designs[3][1]
    for name, b in (("cube", cube), ("shuffled layers, draw 1", shuf)):
        row = []
        for m in (16, 24, 32, 48, 56):
            full = two = 0
            for _ in range(4000):
                cov = set()
                for a in r.sample(range(64), m):
                    cov.update(b[a])
                full += len(cov) == S
                two += len(cov) > S - x
            row.append(f"{m}: {full / 4000:.2f} / {two / 4000:.2f}")
        print(f"  {name}, m at random: P(all 64) / P(more than two thirds), " + ", ".join(row))
    print("  m independent picks: share covered on average / P(all 64), "
          + ", ".join(f"{m}: {1 - (1 - d / S) ** m:.2f} / {p_all_covered(S, d, m):.2f}" for m in (16, 18, 24, 32, 64, 100, 128)))

    print("the merge after failures at random (400 failure sets each): P(the survivors still cover all 64) / "
          "P(16 disjoint survivors cover all 64)")
    r = random.Random(7)
    for name, b in (("pq layout", designs[0][1]), ("cube", cube), ("shuffled layers, draw 1", shuf)):
        row = []
        for f in (4, 8, 16, 24):
            alls = sixteen = 0
            for _ in range(400):
                dead = set(r.sample(range(64), f))
                alive = [a for a in range(64) if a not in dead]
                if len(set().union(*(b[a] for a in alive))) == S:
                    alls += 1
                    sixteen += disjoint_cover(b, S, alive)
            row.append(f"{f} failed: {alls / 400:.2f} / {sixteen / 400:.2f}")
        print(f"  {name}: " + ", ".join(row))
    print(f"  expected subnets without a proof, any assignment with k = 4: "
          + ", ".join(f"{f} failed: {S * comb(f, 4) / comb(64, 4):.2f}" for f in (4, 8, 16, 24)))

    # Machines are what the network adversary silences. A machine that hosts several of a slot's
    # aggregators loses them together, so t in machines is at most t in aggregators.
    print("in machines: a slot's 64 roles go to validators drawn at random, and the roles on one machine are "
          "silenced together (medians over 30 draws)")
    print("  the 64 roles sit on | finality breaks at: pq layout (exact) | cube (attack found) | "
          "shuffled layers, draw 1 (attack found)")
    for label, sizes in hosting_scenarios():
        f = layouts_in_machines(sizes, S, d, x, cube, shuf)
        print(f"  {label}: {f['machines']} machines | {f['pq']} | {f['cube']} | {f['shuffled']}")
    print(f"  every role on a machine of its own: 64 machines | {redundant_t(S, d, 4, x)} | 37 (exact.py) | 30 to 35")
