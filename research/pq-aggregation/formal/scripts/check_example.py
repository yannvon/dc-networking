# Independent brute-force check of Yann's example (16 subnets, 16 aggregators, d = k = 4).
# It rebuilds both assignments of PQAggregation/Examples.lean without Lean and reports, for each:
# the fewest failures that lose at least l subnets (via the duality theorem tolerance_eq_min_nbhd,
# cross-checked against a brute force over all 2^16 failure sets), the most subnets f failures can
# lose (the coverage profile), and the loss unit. Run: python3 scripts/check_example.py
from itertools import combinations
mul = [[0,0,0,0],[0,1,2,3],[0,2,3,1],[0,3,1,2]]
def affine_cover(a):
    c, b = divmod(a, 4)
    pts = set()
    for s in range(16):
        x, y = divmod(s, 4)
        if (x == b) if c == 3 else (y == (mul[c][x] ^ b)): pts.add(s)
    return pts
def redundant_cover(a): return {s for s in range(16) if s // 4 == a // 4}
def analyse(name, cover):
    C = [frozenset(cover(a)) for a in range(16)]
    aggs = [{a for a in range(16) if s in C[a]} for s in range(16)]
    nb = lambda L: {a for a in range(16) if C[a] & L}
    # minimal number of failures to lose >= l subnets, via the duality theorem
    tol = {}
    for l in range(1, 17):
        tol[l] = min(len(nb(set(L))) for L in combinations(range(16), l))
    # coverage profile by brute force over all failure sets (2^16)
    best = [0]*17
    for mask in range(1 << 16):
        F = {a for a in range(16) if mask >> a & 1}
        lost = sum(1 for s in range(16) if aggs[s] <= F)
        f = len(F)
        best[f] = max(best[f], lost)
    for f in range(1, 17): best[f] = max(best[f], best[f-1])
    # cross-check duality: least f with maxLoss(f) >= l equals tol[l]
    for l in range(1, 17):
        assert min(f for f in range(17) if best[f] >= l) == tol[l], (name, l)
    unit = min(sum(1 for t in range(16) if aggs[t] <= aggs[s]) for s in range(16))
    print(name, "t(lose>=6) =", tol[6], "| tol by l:", [tol[l] for l in range(1,17)])
    print("  maxLoss(f), f=0..16:", best, "| loss unit:", unit)
analyse("redundant", redundant_cover)
analyse("affine", affine_cover)
# a 6-set with 12 lines meeting it, and its lines (aggregator indices 4c+b)
C = [frozenset(affine_cover(a)) for a in range(16)]
for L in combinations(range(16), 6):
    N = [a for a in range(16) if C[a] & set(L)]
    if len(N) == 12:
        lost = [s for s in range(16) if all(a in N for a in range(16) if s in C[a])]
        print("L =", L, "N =", N, "lost by failing N:", lost); break
