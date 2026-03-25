# Agent-Driven Development Lifecycle (ADLC)

> This document defines the development tracks, prompt templates, and Definition of Done
> used by Claude and human contributors on this project.

---

## §1 Overview

The ADLC governs how work flows from issue → implementation → review → merge.
Two tracks exist to match the weight of the change to the overhead of the process.

---

## §2 Standard Track

Use for: new features, new modules, interface changes, schema changes, multi-file refactors.

**Steps:**
1. Read HEARTBEAT.md (remote-first) — confirm sprint is ACTIVE, issue is in scope
2. Read issue fully — list all acceptance criteria before writing code
3. Read SESSION.md or create from template
4. Confirm test suite green: `pytest tests/ -m "not integration"`
5. Implement in the issue's branch — one logical commit per concern
6. Write or update tests for changed code
7. Run `bash scripts/local_check.sh` — must exit 0
8. Update SESSION.md work log and key decisions
9. Commit with conventional commit format: `type(scope): message`
10. At session end: promote key decisions to HEARTBEAT sprint notes, push branch

---

## §2b Lightweight Track

Use for: docs-only changes, single-file private fixes (no public interface change),
config updates, minor refactors within one file that don't affect other modules.

**Steps:**
1. Read HEARTBEAT.md — confirm sprint is ACTIVE
2. Read the file(s) you will edit
3. Make the change
4. Run targeted test if one exists: `pytest tests/test_<module>.py`
5. Commit with conventional commit format

Skip: full SESSION.md setup, `local_check.sh`, full AC checklist.

---

## §3 Commit Format

```
type(scope): short imperative description

Optional body — what and why, not how.
```

**Types:** `feat` · `fix` · `test` · `docs` · `chore` · `refactor` · `ci`

**Examples:**
```
feat(scheduler): integrate APScheduler SQLite jobstore
fix(watcher): handle missing state file on first run
test(http): add responses-based HTTP-fixture integration tests
docs(secrets): add required env vars and Vault guidance
chore(heartbeat): update sprint notes after session 2026-03-23
```

---

## §4 Branch Naming

```
feat/<short-description>       — new feature
fix/<short-description>        — bug fix
chore/<short-description>      — maintenance, config, docs
ci/<short-description>         — CI/CD changes
test/<short-description>       — test-only changes
```

One issue = one branch. Do not bundle unrelated issues on the same branch.

---

## §5 Prompt Templates

### §5.1 New Agent Module

```
Implement a new role agent for <role>.
- Module: agents/skills/<role>.py
- Must follow the pattern in agents/skills/fundraising.py
- Expose a single public function: run_<role>_agent(context: dict) -> dict
- Add CLI hook in agents/agents_cli.py under `role` subcommand
- Add unit test: tests/test_<role>_agent.py
- Add example: examples/<role>_example.py
AC: `pytest tests/test_<role>_agent.py` passes; CLI `role <role> --help` works.
```

### §5.2 Feature

```
Implement <feature description> per issue #N.
AC from issue:
- [ ] <AC 1>
- [ ] <AC 2>
Constraints: no new packages; follow existing patterns in <nearest analogous module>.
```

### §5.3 Bug Fix

```
Fix: <symptom observed>.
Reproduce with: <minimal reproduction>.
Root cause hypothesis: <your hypothesis>.
Fix: <proposed change>.
Add a regression test that would have caught this.
```

### §5.4 Test Coverage

```
Add tests for <module>. Current coverage: <N>%.
Target: cover <specific scenarios>.
Use existing fixtures in tests/conftest.py.
Do not modify production code — test-only changes.
```

### §5.5 Refactor

```
Refactor <module> to <goal — e.g. "reduce duplication", "extract helper">.
Public interfaces must not change.
All existing tests must continue to pass.
No new packages.
```

---

## §6 Definition of Done (DoD)

A piece of work is Done when ALL of the following are true:

- [ ] All acceptance criteria from the issue are checked
- [ ] Tests written for changed/new code
- [ ] `pytest tests/ -m "not integration"` passes
- [ ] `bash scripts/local_check.sh` exits 0
- [ ] No new linting errors introduced
- [ ] SESSION.md handoff notes written
- [ ] HEARTBEAT.md sprint notes updated (key decisions promoted)
- [ ] Branch pushed to remote
- [ ] PR opened (human merges)
- [ ] Issue labeled `needs-review` (remove `in-progress`)

**Hard stops that block Done:** any unchecked AC item, any failing test, any skipped test with no documented reason.
