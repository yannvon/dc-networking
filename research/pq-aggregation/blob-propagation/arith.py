"""Byte and timing arithmetic for README.md (blob propagation). Stdlib only: python3 arith.py

Every input is a parameter below, cited to its source; the defaults are the example
values the note uses. Nothing here is simulated: times are downlink floors, i.e. the
bytes a node must receive divided by its link rate, with the link carrying nothing else.
"""

KIB = 1024
MIB = 1024 * KIB

# leanVM benchmarks.json, measured at be190e9 (read at 20a75c1, 2026-11-25)
LEAF = 204 * KIB          # aggregation, 1,400 leanXMSS
NODE = 280 * KIB          # recursion 16 -> 1
# "full" (all threads) times, seconds: NUC 14 Pro, M4 Max, AX42, EX63
PROVE = (1.267, 0.695, 0.955, 0.730)   # aggregation, 1,400 signatures
MERGE = (1.273, 0.648, 1.018, 0.775)   # recursion 16 -> 1 (upper bound for fewer children)
# leanVM README @ 20a75c1: DA proof for 32 blobs
DA_PROOF = 290 * KIB

# Copies of an object a node receives, data only (one source, 500 nodes, 16 connections).
# gossipsub: this repo's runs of Barnabe's model (research/pq/README.md).
# SEACAST: v2's Figure 6 gives about 3.2 copies at 128 KiB falling to 1.6 at 4 MiB on the
#   all-home network, most of the fall between 256 KiB and 1 MiB. 3 is our reading for
#   200-300 KiB, not a measured point.
COPIES = {"gossipsub": 4.5, "SEACAST": 3.0, "one copy": 1.0}

HEADER = 2_404 + 300      # XMSS signature + index, slot, root, descriptor, coverage bits (our estimate)

LINKS_DOWN = {"home 100/50": 100e6, "EIP-7870 attester 50/25": 50e6}
UPLINKS = (50e6, 25e6)

N_NODES = 8_000           # Barnabe's model default
C_COLS = 128              # columns per coded object
J_SUBNETS = 2             # subnets a node backs (SUBNETS_PER_NODE)
K_AGG = 4                 # aggregators per subnet (pq spec)
M_FANIN = 16              # leanVM merge fan-in


def custody_share(r=2, c=8, C=C_COLS):
    """Fraction of an object a custodian receives: expansion r, c of C columns."""
    return r * c / C


def custody_bytes(P, s, c=8, copies=3.0):
    return P * (s * custody_share(c=c) + HEADER) * copies


def baseline_bytes(s, j=J_SUBNETS, k=K_AGG, copies=4.5):
    """Merger topics: one topic per subnet carries its k proofs whole; a node backs j subnets."""
    return j * k * s * copies


def path_overhead(cell):
    return {2 * KIB: 8 * 32, 16 * KIB: 5 * 32}[cell] / cell


def merger_floor(m, s, cell, link, copies=1.0):
    return m * s * (1 + path_overhead(cell)) * copies * 8 / link


def show():
    links = list(LINKS_DOWN.values())

    print("Per-node receive, all intermediate proofs of a slot (s = 204 KiB)")
    print(f"{'P':>4} {'mode':<34} {'MiB/slot':>9} {'Mbit/s avg':>11} " +
          " ".join(f"{'t@' + k.split()[0] + ' (s)':>12}" for k in LINKS_DOWN))
    for P in (16, 64, 128):
        rows = [(f"whole, {k} ({g} copies)", P * LEAF * g) for k, g in COPIES.items()]
        for c in (4, 8):
            rows.append((f"custody {c}/128, 3 copies", custody_bytes(P, LEAF, c)))
        for name, b in rows:
            bits = b * 8
            ts = " ".join(f"{bits / v:12.2f}" for v in links)
            print(f"{P:>4} {name:<34} {b / MIB:9.2f} {bits / 12 / 1e6:11.1f} {ts}")
        print()

    print(f"Baseline: merger topics, node backs j={J_SUBNETS} subnets of k={K_AGG} proofs, whole (any P)")
    for name, g in COPIES.items():
        b = baseline_bytes(LEAF, copies=g)
        ts = ", ".join(f"{b * 8 / v:.2f} s @{k.split()[0]}" for k, v in LINKS_DOWN.items())
        print(f"  {name:<10} {b / MIB:5.2f} MiB, {ts}")
    print("  node on no subnet topic: 0 MiB")
    for c in (4, 8):
        # custody = S*k*s*2c/C*copies vs baseline j*k*s*copies at equal copies -> S* = j*C/(2c)
        print(f"  equal per-node bytes (same copies, header aside) at S = j*C/(2c) = "
              f"{J_SUBNETS * C_COLS // (2 * c)} subnets for custody {c}; above it the baseline is cheaper")
    print(f"  holders of one proof: baseline N*j/S = {N_NODES}*{J_SUBNETS}/S nodes, whole "
          f"({N_NODES * J_SUBNETS // 16} at S=16, {N_NODES * J_SUBNETS // 64} at S=64); "
          f"custody: all {N_NODES} nodes, a share 2c/C each")
    print()

    print("Largest P whose whole-object delivery fits a budget T on a downlink (s = 204 KiB)")
    for T in (1.0, 2.0):
        for link, v in LINKS_DOWN.items():
            for k, g in COPIES.items():
                print(f"  T={T} s {link:<24} {k:<10} P <= {int(v * T / (LEAF * 8 * g))}")
            pc = int(v * T / (8 * custody_bytes(1, LEAF)))
            print(f"  T={T} s {link:<24} custody 8 P <= {pc}")
    print()

    print("Custodians per column: N*c/C")
    for c in (4, 8):
        print(f"  N={N_NODES}, c={c}: {N_NODES * c // C_COLS}")
    print()

    print("Merger floor: m children received whole, coded, with Merkle paths")
    for m in (4, 16):
        for name, s in (("leaf", LEAF), ("node", NODE)):
            for cell in (2 * KIB, 16 * KIB):
                for g in (1.0, 3.0):
                    b = m * s * (1 + path_overhead(cell)) * g
                    ts = ", ".join(f"{b * 8 / v:.2f} s @{k.split()[0]}" for k, v in LINKS_DOWN.items())
                    print(f"  m={m:>2} {name} cells {cell // KIB:>2} KiB, {g:.0f} copies: {b / MIB:5.2f} MiB, {ts}")
    print(f"  baseline merger joins m=16 subnet topics and gets all k={K_AGG} proofs of each:")
    for name, g in COPIES.items():
        print(f"    {name:<10} {M_FANIN * K_AGG * LEAF * g / MIB:6.1f} MiB "
              f"(1 proof per subnet if the later aggregators stay silent: {M_FANIN * LEAF * g / MIB:.1f} MiB)")
    print()

    print("Interest ALL (proposer or builder fetching every leaf proof), P = 64")
    for g in (1.0, 3.0):
        print(f"  {g:.0f} copies: {64 * LEAF * g / MIB:.1f} MiB")
    print()

    print("Aggregator upload of one coded object (2x), once")
    up = {name: tuple(2 * s * 8 / u for u in UPLINKS) for name, s in (("leaf", LEAF), ("node", NODE))}
    for name, (a, b) in up.items():
        print(f"  {name}: {a * 1e3:.0f} ms at 50 Mbit/s up, {b * 1e3:.0f} ms at 25")
    print()

    # The tree is counted in children of the merge: one proof per subnet, so S children when an
    # aggregator covers one subnet. The k proofs of a subnet are alternatives, so this is not P = S*k.
    print("Latency from the vote deadline (floors, one copy; best machine and 16 KiB cells @100 down,")
    print("slowest machine and 2 KiB cells @50 down; 16 -> 1 merge time used for every merge)")
    d1 = (merger_floor(M_FANIN, LEAF, 16 * KIB, links[0]), merger_floor(M_FANIN, LEAF, 2 * KIB, links[1]))
    lvl1 = (min(PROVE) + d1[0] + min(MERGE), max(PROVE) + d1[1] + max(MERGE))
    print(f"  one merge level (<= m = {M_FANIN} children):      {lvl1[0]:.2f}-{lvl1[1]:.2f} s"
          f"   (+ leaf upload: {lvl1[0] + up['leaf'][0]:.2f}-{lvl1[1] + up['leaf'][1]:.2f} s)")
    for children in (64, 128):
        m2 = -(-children // M_FANIN)
        d2 = (merger_floor(m2, NODE, 16 * KIB, links[0]), merger_floor(m2, NODE, 2 * KIB, links[1]))
        lvl2 = (lvl1[0] + d2[0] + min(MERGE), lvl1[1] + d2[1] + max(MERGE))
        upl = (up["leaf"][0] + up["node"][0], up["leaf"][1] + up["node"][1])
        print(f"  two levels, {children:>3} children ({M_FANIN} -> {m2} -> 1): {lvl2[0]:.2f}-{lvl2[1]:.2f} s"
              f"   (+ uploads: {lvl2[0] + upl[0]:.2f}-{lvl2[1] + upl[1]:.2f} s)")
    print()

    print("Block with LeanDA: separate DA and vote proofs vs one merged proof (merged size assumed = recursion)")
    print(f"  {DA_PROOF // KIB} + {NODE // KIB} KiB -> {NODE // KIB} KiB: saves {(DA_PROOF + NODE - NODE) // KIB} KiB per block")
    print()

    print("Blob capacity: proofs as EIP-4844 blobs of 126,976 usable bytes (4096 x 31 B)")
    usable = 4096 * 31
    for name, s in (("leaf", LEAF), ("node", NODE)):
        n = -(-s // usable)
        print(f"  {name} {s // KIB} KiB -> {n} blobs ({s / (n * usable):.0%} filled); "
              f"LeanDA rows of 128 KiB: {-(-s // (128 * KIB))}")
    for P in (4, 16, 64):
        print(f"  P={P} leaf proofs: {P * -(-LEAF // usable)} blobs vs max 21 per block")


if __name__ == "__main__":
    show()
