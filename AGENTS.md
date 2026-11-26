# Guidance for agents

Written 2026-11-26 by an agent, at Yann's request that the repo keep track of its
context and resources "so agents know where to look in case of questions". The
rules below are Yann's, each with his words and the date. The wording around
them is the agent's, and Yann has not reviewed it. People: change this file as
you see fit.

## Where to look

- **Open [`resources.md`](resources.md) before you answer from memory.** It lists
  the outside sources this repo rests on: the reference spec and its upstream,
  the Eth R&D Discord archive, ethresear.ch, EIPs, leanVM, write-ups and
  measurements. For each it says what it is good for, how to read it from a
  sandbox, what was last read, and what was looked for and not found.
- **The layout of the repo** is in [`README.md`](README.md).
- **The reference spec for decoupled consensus** is named in
  [`specs/README.md`](specs/README.md). Its branches move, so check the tip.
- **When you read a new source, or a new revision of one, record it** in
  `resources.md`.

## Rules Yann has set

- **Kamil's node list stays out of this repo.** "kamil's note was kept from the
  public repo on purpose" (2026-11-25). Do not add the list, or anything per
  node from it. "aggregate figures can go in the repo" (2026-11-25).
- **Properties keep their origin tags.** "keep human dictated properties with a
  specific tag" (2026-11-25). The legend is in
  [`properties/README.md`](properties/README.md#origin-tags). Do not change what
  a property tagged `human` asks for. Write a proposal next to it.

## Conventions the repo already follows

- **A file written by an agent says so:** `provenance: agent` in its front
  matter, and a note at the top that says who asked for what and what a person
  has reviewed.
- **Sources are cited so that they can be checked:** a repository with its
  commit, a web page with the date it was read, and quotes word for word.
  [`check_citations.py`](research/pq-aggregation/background/check_citations.py)
  checks quotes against the background notes and against files at a commit.
- **Commit messages** start with the path, as in `research/pq-gasper: ...`, and
  say in the body who asked for the change.
