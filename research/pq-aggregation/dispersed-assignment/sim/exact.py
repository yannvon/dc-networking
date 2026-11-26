"""Exact figures that need a solver.

Needs ortools, which brings numpy:
    uv run --with ortools python3 exact.py [seconds per solve of part 1] [parts, default 123]
Prints, for ../README.md:
  1. exact t(q) for its 32-subnet rows, with CP-SAT. A solve that stops at the limit shows
     "best found / proven lower bound" instead of one number.
  2. the exact loss profile of the cube layers (section 10 of dispersal.py), by a search
     that is checked here against plain enumeration.
  3. the merge after failures at random for the same section, with CP-SAT. Each solve runs on
     one worker up to a deterministic limit, so a rerun prints the same rows; a row that is
     not proved is a bound.
"""
import random
import sys
from itertools import combinations
from math import ceil

import numpy as np
from ortools.sat.python import cp_model

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from dispersal import (CUBE_DIRECTIONS, rs_net, random_biregular, cube_layers, shuffled_layers,
                       need, floor_t, redundant_t, ceiling_t, tanner)

LIMIT = float(sys.argv[1]) if len(sys.argv) > 1 else 300
PARTS = sys.argv[2] if len(sys.argv) > 2 else "123"
MERGE_LIMIT = 4                                # deterministic time per merge solve, about 2 s here


def solver(seconds=None, deterministic=None):
    sol = cp_model.CpSolver()
    sol.parameters.num_workers = 1
    if seconds is not None:
        sol.parameters.max_time_in_seconds = seconds
    if deterministic is not None:
        sol.parameters.max_deterministic_time = deterministic
    return sol


def t_cpsat(blocks, S, x):
    m = cp_model.CpModel()
    y = [m.NewBoolVar("") for _ in blocks]
    z = [m.NewBoolVar("") for _ in range(S)]
    for a, b in enumerate(blocks):
        for s in b:
            m.AddImplication(z[s], y[a])
    m.Add(sum(z) >= x)
    m.Minimize(sum(y))
    sol = solver(seconds=LIMIT)
    st = sol.Solve(m)
    hi, lo = int(sol.ObjectiveValue()), int(sol.BestObjectiveBound())
    return str(hi) if st == cp_model.OPTIMAL else f"{hi}/{lo}"


# ---------------------------------------------------------------- cube layers: exact profile

def cube_lines(w, k):
    """dispersal.cube_layers for a w x w x w grid: the lines of the first k directions."""
    blocks = []
    for v in CUBE_DIRECTIONS[:k]:
        seen = set()
        for p in range(w ** 3):
            if p not in seen:
                q = (p // (w * w), p // w % w, p % w)
                line = tuple(sorted(sum((q[j] + i * v[j]) % w * w ** (2 - j) for j in range(3))
                                    for i in range(w)))
                seen.update(line)
                blocks.append(line)
    return blocks


def cube_profile(w, k):
    """g[j] = the fewest aggregators whose silence leaves at least j subnets without a proof,
    for the first k (3 or 4) layers of the w x w x w cube.

    Subnets are the points (x, y, z), coordinates mod w, and sheet z is the w x w points with
    that z. Take a set T of lost subnets and let T_z be its part in sheet z. The lines that
    touch T are the z-lines through U, the union of the T_z; the rows and columns of every
    T_z; and with k = 4 the diagonals through D, the classes (x - z, y - z) of T. So g[j] is
    the least, over pairs (U, D), of |U| + |D| plus the cheapest way to take j points from the
    sheets, where sheet z offers the points of U whose class is in D, and h[M][s] is the
    fewest rows plus columns whose crossing holds s points of the mask M. Symmetries cut the
    pairs down: moving, transposing and reflecting the sheet for U; moving along z for D; and
    the map that swaps z-lines with diagonals, which leaves only the pairs with |U| <= |D|."""
    n, N = w * w, 1 << (w * w)
    INF = 60                                   # above any real total of rows plus columns
    assert 2 * w * w < INF and w * INF < 256
    m = np.arange(N, dtype=np.uint32)
    pop = np.zeros(N, dtype=np.int64)
    for i in range(n):
        pop += (m >> i) & 1
    h = np.full((N, n + 1), INF, dtype=np.uint8)
    h[:, 0] = 0
    for R in range(1, 1 << w):
        for C in range(1, 1 << w):
            rect = sum(1 << (x * w + y) for x in range(w) if R >> x & 1 for y in range(w) if C >> y & 1)
            cnt = pop[m & rect]
            sel = cnt > 0
            h[m[sel], cnt[sel]] = np.minimum(h[m[sel], cnt[sel]], bin(R).count("1") + bin(C).count("1"))
    for s in range(n - 1, 0, -1):
        h[:, s] = np.minimum(h[:, s], h[:, s + 1])

    def moved(f):
        """Every sheet mask with its points moved by the map f of (x, y)."""
        out = np.zeros(N, dtype=np.uint32)
        for x in range(w):
            for y in range(w):
                x2, y2 = f(x, y)
                out |= ((m >> (x * w + y)) & 1) << (x2 % w * w + y2 % w)
        return out

    shift = [moved(lambda x, y, z=z: (x + z, y + z)) for z in range(w)]
    canon_u = m.copy()
    for a in range(w):
        for b in range(w):
            for sgn in (1, -1):
                canon_u = np.minimum(canon_u, moved(lambda x, y: (sgn * x + a, sgn * y + b)))
                canon_u = np.minimum(canon_u, moved(lambda x, y: (sgn * y + b, sgn * x + a)))
    reps_u = [int(U) for U in m[canon_u == m]]
    reps_d = m[np.minimum.reduce(shift) == m]

    def minplus(A, B):
        out = np.full((max(len(A), len(B)), A.shape[1] + B.shape[1] - 1), 250, dtype=np.uint8)
        for i in range(A.shape[1]):
            np.minimum(out[:, i:i + B.shape[1]], A[:, i:i + 1] + B, out=out[:, i:i + B.shape[1]])
        return out

    best = np.full(w * n + 1, 10 ** 6, dtype=np.int64)
    for U in reps_u:
        if k == 4:
            keep = reps_d[pop[reps_d] >= pop[U]]
            tabs = [h[U & shift[z][keep]] for z in range(w)]
            base = pop[U] + pop[keep]
        else:
            tabs = [h[U][None, :]] * w
            base = pop[[U]]
        conv = tabs[0]
        for t in tabs[1:]:
            conv = minplus(conv, t)
        total = conv.astype(np.int64) + base[:, None]
        total[conv >= INF] = 10 ** 6
        best = np.minimum(best, total.min(axis=0))
    return [int(v) for v in best]


def line_masks(blocks, S):
    nb = [0] * S
    for a, b in enumerate(blocks):
        for s in b:
            nb[s] |= 1 << a
    return nb


def enumerate_small(blocks, S, j):
    """Fewest aggregators touching j subnets, over every set of j that holds subnet 0. For the
    cube that is every set, because a translation moves any subnet to subnet 0."""
    nb = line_masks(blocks, S)
    best = len(blocks)
    for rest in combinations(range(1, S), j - 1):
        v = nb[0]
        for s in rest:
            v |= nb[s]
        best = min(best, bin(v).count("1"))
    return best


def enumerate_all(blocks, S):
    """g[j] for every j by enumeration of all 2^S sets of subnets (S = 27), in two halves."""
    nb = line_masks(blocks, S)
    lo_n = S // 2

    def table(points):
        t = np.zeros(1 << len(points), dtype=np.uint64)
        for i, p in enumerate(points):
            t[1 << i:1 << (i + 1)] = t[:1 << i] | np.uint64(nb[p])
        return t

    lo, hi = table(range(lo_n)), table(range(lo_n, S))
    bits = np.array([bin(v).count("1") for v in range(1 << 16)], dtype=np.int64)
    size_lo = bits[np.arange(1 << lo_n)]
    size_hi = bits[np.arange(1 << (S - lo_n))]
    by_size = [np.nonzero(size_hi == c)[0] for c in range(S - lo_n + 1)]
    best = [0] + [len(blocks)] * S
    for a in range(1 << lo_n):
        v = hi | lo[a]
        cost = sum(bits[((v >> np.uint64(16 * i)) & np.uint64(0xFFFF)).astype(np.int64)] for i in range(3))
        for c, idx in enumerate(by_size):
            best[int(size_lo[a]) + c] = min(best[int(size_lo[a]) + c], int(cost[idx].min()))
    return best


# ---------------------------------------------------------------- the merge after failures

def covered_by(blocks, children):
    return set().union(*(blocks[a] for a in children))


def fewest_children(blocks, alive):
    """The fewest alive aggregates that cover every subnet an alive one covers:
    (the children found, proved). Each child covers d subnets, so they number at least covered / d."""
    union = covered_by(blocks, alive)
    m = cp_model.CpModel()
    u = {a: m.NewBoolVar("") for a in alive}
    for s in union:
        m.AddBoolOr([u[a] for a in alive if s in blocks[a]])
    m.Minimize(sum(u.values()))
    sol = solver(deterministic=MERGE_LIMIT)
    st = sol.Solve(m)
    assert st in (cp_model.OPTIMAL, cp_model.FEASIBLE), st
    children = [a for a in alive if sol.Value(u[a])]
    low = max(ceil(sol.BestObjectiveBound() - 1e-6), -(-len(union) // len(blocks[0])))
    return children, st == cp_model.OPTIMAL or len(children) == low


def most_covered(blocks, alive, most, start):
    """The most subnets that `most` of the alive aggregates cover together: (found, proved).
    `start` is a set of children to begin from, here a smallest cover cut down to `most`."""
    union = covered_by(blocks, alive)
    m = cp_model.CpModel()
    u = {a: m.NewBoolVar("") for a in alive}
    c = {}
    for s in union:
        c[s] = m.NewBoolVar("")
        m.AddBoolOr([u[a] for a in alive if s in blocks[a]] + [c[s].Not()])
    m.Add(sum(u.values()) <= most)
    m.Maximize(sum(c.values()))
    begun = covered_by(blocks, start)
    for a in alive:
        m.AddHint(u[a], int(a in start))
    for s in union:
        m.AddHint(c[s], int(s in begun))
    sol = solver(deterministic=MERGE_LIMIT)
    st = sol.Solve(m)
    assert st in (cp_model.OPTIMAL, cp_model.FEASIBLE), st
    found = max(int(round(sol.ObjectiveValue())), len(begun))
    return found, st == cp_model.OPTIMAL or found == min(len(union), most * len(blocks[0]))


def cut_down(blocks, children, most):
    """Drop children one at a time, each time the one whose loss uncovers the fewest subnets."""
    children = list(children)
    while len(children) > most:
        children.remove(min(children, key=lambda a: len(covered_by(blocks, children)) - len(covered_by(blocks, [b for b in children if b != a]))))
    return children


if __name__ == "__main__":
    if "1" in PARTS:
        rng = random.Random(1)
        cases = [
            ("RS net d=4 w=8", 32, 4, 4, lambda: rs_net(4, 8, 4)),
            ("random biregular", 32, 4, 4, lambda: random_biregular(32, 4, 4, rng)),
        ]
        print(f"\n# 1. q = 1/3, CP-SAT limit {LIMIT:.0f} s per solve")
        print(f"{'assignment':<30} {'S':>3} {'d':>2} {'k':>2} {'A':>4} | floor red  this  ceiling")
        for name, S, d, k, make in cases:
            x = need(S)
            print(f"{name:<30} {S:>3} {d:>2} {k:>2} {S*k//d:>4} | {floor_t(S,d,k,x):>5} "
                  f"{redundant_t(S,d,k,x):>3} {t_cpsat(make(), S, x):>5} {ceiling_t(S,d,k,x):>8}", flush=True)

    S, d = 64, 4
    x = need(S)
    if "2" in PARTS:
        print("\n# 2. Cube layers (section 10 of dispersal.py): the exact loss profile")
        for k in (4, 3):
            assert cube_lines(4, k) == cube_layers(k)
            same = enumerate_all(cube_lines(3, k), 27) == cube_profile(3, k)
            print(f"check, {k} layers: the search on the 3 x 3 x 3 cube equals the enumeration of all 2^27 sets: {same}",
                  flush=True)
        for k in (4, 3):
            g = cube_profile(4, k)
            A = 16 * k
            small = [enumerate_small(cube_layers(k), S, j) for j in range(1, 6)]
            print(f"{k} layers, {A} aggregators: fewest silenced aggregators that leave j subnets without a proof, j = 1..{S}:")
            print(f"  {g[1:]}")
            print(f"  check: j = 1..5 by enumeration {small}: {small == g[1:6]}; "
                  f"at least Tanner's bound for every j: {all(g[j] >= tanner(S, d, k, j, 8) for j in range(1, S + 1))}")
            print(f"  t(1/3) = {g[x]} (pq layout with {k} aggregators per committee: {redundant_t(S, d, k, x)}; "
                  f"it reaches {g[x]} with {-(-g[x] // 6)} per committee, {16 * -(-g[x] // 6)} aggregators)")
            budgets = (4, 8, 12, 16, 20, 24, 28, 32, 36)
            print("  most subnets that f silenced aggregators leave without a proof, cube / the same deal in every layer: "
                  + ", ".join(f"{f}: {max(j for j in range(S + 1) if g[j] <= f)} / {d * (f // k)}" for f in budgets if f <= A),
                  flush=True)

    if "3" in PARTS:
        print("\n# 3. The merge after failures at random: 64 aggregators in 4 layers, 12 failure sets per row")
        designs = (("cube", cube_layers(4)), ("shuffled layers, draw 1", shuffled_layers(S, d, 4, random.Random(9))))
        for name, b in designs:
            r = random.Random(7)
            for f in (8, 16, 24):
                rows = []
                for _ in range(12):
                    dead = set(r.sample(range(64), f))
                    alive = [a for a in range(64) if a not in dead]
                    kids, kids_proved = fewest_children(b, alive)
                    if len(kids) <= 16:
                        top = (len(covered_by(b, alive)), True)
                    else:
                        top = most_covered(b, alive, 16, cut_down(b, kids, 16))
                    rows.append((len(covered_by(b, alive)), len(kids), kids_proved, top[0], top[1]))
                kids = sorted(row[1] for row in rows)
                top = [row[3] for row in rows]
                print(f"{name}, {f} failed: the survivors cover {sum(row[0] for row in rows) / 12:.1f} of 64 on average | "
                      f"fewest children for all of that: {kids[0]} to {kids[-1]}, mean {sum(kids) / 12:.1f} "
                      f"(proved in {sum(row[2] for row in rows)} of 12), 16 or fewer in {sum(v <= 16 for v in kids)} of 12 | "
                      f"the best 16 children cover at least {sum(top) / 12:.1f} on average, at least {min(top)} in every case "
                      f"(the best possible proved in {sum(row[4] for row in rows)} of 12)", flush=True)
