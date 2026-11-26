"""Check quoted fragments in a Markdown file against the sources they cite.

Written 2026-11-25 by an agent (oversight thread of the PQ aggregation workstream),
extended on 2026-11-26 for citations of a spec file at a commit.

Two kinds of citation are understood:

- An entry of the notes in this folder: [specs 12](...), [discord F12](...) or
  [ethresear.ch 12](...). The entry must exist, and the link must point at the
  right note.
- A file at a commit with a line range, as GitHub shows it:
  https://github.com/<owner>/<repo>/blob/<40 hex digits>/<path>?plain=1#L10-L20
  It is checked only against a local clone that has the commit (--clone DIR,
  which may be given several times). Without one it is counted as not checked.

For every fragment between double quotes: the citations that follow it, up to
the next quoted fragment, are its sources, and the fragment must occur word for
word in one of them (ignoring case, line breaks and Markdown marks).

It does not check that an entry's quote is in the original source (the notes
say how that was checked), nor that a paraphrase is fair. Numbers are only
searched as substrings with --numbers, which is a weak check.

usage, from the repository root:
    python3 research/pq-aggregation/background/check_citations.py \
        properties/aggregation-broadcast.md [--numbers] [--clone ../consensus-specs]

Exit code 0 when nothing is missing, 1 otherwise.
"""
import os
import re
import subprocess
import sys

FILES = {
    "specs": "consensus-specs.md",
    "discord": "eth-rnd-discord.md",
    "ethresear.ch": "ethresearch.md",
}
ENTRY_CITE = re.compile(r"\[(specs|discord|ethresear\.ch) F?(\d+)\]\(([^)]+)\)")
PINNED_CITE = re.compile(
    r"\]\(https://github\.com/([\w.-]+/[\w.-]+)/blob/([0-9a-f]{40})/([^)?#\s]+)"
    r"(?:\?plain=1)?#L(\d+)(?:-L(\d+))?\)"
)
QUOTE = re.compile(r'"([^"]{4,})"')
ENTRY = re.compile(r"(?m)^### (F?\d+)\. ")


def norm(text):
    """Lower-case, straighten quotes, drop Markdown marks, collapse whitespace."""
    for curly, straight in (("“", '"'), ("”", '"'), ("’", "'"), ("‘", "'")):
        text = text.replace(curly, straight)
    for mark in ("`", "*", "_", "\\"):
        text = text.replace(mark, "")
    return re.sub(r"\s+", " ", text).lower().strip()


def load_entries(folder):
    entries = {}
    for key, name in FILES.items():
        with open(os.path.join(folder, name)) as fh:
            parts = ENTRY.split(fh.read())
        for i in range(1, len(parts), 2):
            body = re.split(r"(?m)^## ", parts[i + 1])[0]
            entries[(key, int(parts[i].lstrip("F")))] = norm(body)
    return entries


class Clones:
    """Reads lines of a file at a commit from the first clone that has it."""

    def __init__(self, dirs):
        self.dirs = dirs
        self.cache = {}

    def lines(self, commit, path):
        key = (commit, path)
        if key not in self.cache:
            self.cache[key] = None
            for d in self.dirs:
                out = subprocess.run(
                    ["git", "-C", d, "show", f"{commit}:{path}"], capture_output=True
                )
                if out.returncode == 0:
                    self.cache[key] = out.stdout.decode("utf-8", "replace").split("\n")
                    break
        return self.cache[key]

    def text(self, commit, path, first, last):
        lines = self.lines(commit, path)
        return None if lines is None else norm(" ".join(lines[first - 1:last]))


def citations(line):
    """All citations of a line as (position, kind, label, payload), in order."""
    found = []
    for m in ENTRY_CITE.finditer(line):
        key, num = m.group(1), int(m.group(2))
        found.append((m.start(), "entry", f"{key} {num}", (key, num, m.group(3))))
    for m in PINNED_CITE.finditer(line):
        first = int(m.group(4))
        last = int(m.group(5) or first)
        label = f"{m.group(1)}@{m.group(2)[:7]}:{m.group(3)} L{first}-L{last}"
        found.append((m.start(), "pinned", label, (m.group(2), m.group(3), first, last)))
    return sorted(found)


def check(path, entries, clones, numbers):
    missing = 0
    counts = {"entry": 0, "pinned": 0, "quotes": 0, "unchecked": 0}
    with open(path) as fh:
        lines = fh.read().split("\n")
    for ln, line in enumerate(lines, 1):
        cites = citations(line)
        if not cites:
            continue
        for _, kind, label, payload in cites:
            counts[kind] += 1
            if kind == "entry":
                key, num, target = payload
                if (key, num) not in entries:
                    print(f"{path}:{ln}: no entry {label}")
                    missing += 1
                if not target.endswith(FILES[key]):
                    print(f"{path}:{ln}: link {target} is not the note for {key}")
                    missing += 1
        quotes = [(m.start(), m.end(), m.group(1)) for m in QUOTE.finditer(line)]
        for _, q_end, quote in quotes:
            later = [c for c in cites if c[0] > q_end]
            if not later:
                continue  # a quote with no citation after it is not a source quote
            # the citations up to the next quote, or all later ones if none come before it
            next_quotes = [s for s, _, _ in quotes if s > q_end]
            group = [c for c in later if not next_quotes or c[0] < next_quotes[0]] or later
            wanted = norm(quote)
            found = False
            unread = False  # a source of this quote could not be read
            for _, kind, _, payload in group:
                if kind == "entry":
                    text = entries.get(payload[:2], "")
                else:
                    text = clones.text(*payload)
                    if text is None:
                        unread = True
                        continue
                if wanted in text:
                    found = True
                    break
            if not found and unread:
                counts["unchecked"] += 1
                continue
            counts["quotes"] += 1
            if not found:
                print(f"{path}:{ln}: quote not in {[c[2] for c in group]}: \"{quote[:100]}\"")
                missing += 1
        if numbers and "`external`" in line:
            tagged = line[line.index("`external`"):]
            plain = re.sub(r"\]\([^)]*\)", "]", ENTRY_CITE.sub("", tagged))
            cited_text = " ".join(
                entries.get(p[:2], "") for _, kind, _, p in cites if kind == "entry"
            ).replace(",", "")
            for m in re.finditer(r"\d[\d,.]*\d|\d", plain):
                token = m.group(0).rstrip(".,").replace(",", "")
                if token not in cited_text:
                    print(f"{path}:{ln}: number {token} not in the cited entries:"
                          f" …{plain[max(0, m.start() - 50):m.end() + 30]}…")
    print(f"{path}: {counts['entry']} citations of entries, {counts['pinned']} of files at a commit,"
          f" {counts['quotes']} quotes checked, {counts['unchecked']} not checked (no clone has the"
          f" commit), {missing} missing")
    return missing


def main(argv):
    numbers = "--numbers" in argv
    clone_dirs, paths = [], []
    args = [a for a in argv if a != "--numbers"]
    i = 0
    while i < len(args):
        if args[i] == "--clone":
            clone_dirs.append(args[i + 1])
            i += 2
        else:
            paths.append(args[i])
            i += 1
    if not paths:
        print(__doc__)
        return 2
    entries = load_entries(os.path.dirname(os.path.abspath(__file__)))
    clones = Clones(clone_dirs)
    return 1 if sum(check(p, entries, clones, numbers) for p in paths) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
