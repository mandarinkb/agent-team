---
name: team-root-cause
description: Find the root cause of a bug with runtime evidence by eliminating hypotheses, including a debate between analysts. Use after a bug is reproduced and before any fix is planned.
when_to_use: Used by analyst after qa reproduces a bug. Triggers: why does this fail, find the cause, it fails after restart, two fixes did not work, competing hypotheses.
---

# Team root cause

Adapted from pstack's Bug fix playbook and the principles fix-root-causes and attack-the-premise.

## Rules

- Reproduce first. Without a failing reproduction from qa, stop and ask the lead for one.
- Every conclusion rests on runtime evidence: a log line, a debugger value, a request and response, a reverted line that removes the bug. Reading code produces hypotheses, not causes.
- A guard that hides a crash, such as a nil check, is a symptom fix. Ask why the value was nil.
- When a bug appears after a restart, suspect stale state first: config, cache, lock files, serialized data.

## Method

1. **List hypotheses.** Write every plausible cause with the observation that would prove or disprove it.
2. **Split the problem.** Pick the check that removes the most remaining possibilities, such as a log at the midpoint of the flow, a known-good input, or the last good commit (`git bisect`). Run it and eliminate.
3. **Instrument when state is unclear.** Add temporary logging and read it while the code runs. Remove it afterwards.
4. **Attack the premise.** If two fixes based on the same assumption already failed, write that assumption down and test it before trying a third. If the test cannot settle it, raise D9 (`.agents/protocols/loops.md`).
5. **Confirm the mechanism.** The surviving cause must explain every symptom, including ones that seemed unrelated.

## Debate mode

When the lead runs two or three analysts, each owns one hypothesis.

- Message the other analysts with the evidence that would disprove their hypothesis, and ask them to run it.
- Report only hypotheses that survived another analyst's attempt to disprove them.
- Agreement between analysts is not proof. The proof is the runtime evidence.

## Output

Add a `## Root cause` section to `investigation.md`:

- **Mechanism.** What happens, step by step, with `file:line`.
- **Evidence.** The commands and outputs that prove it, labeled measured.
- **Eliminated hypotheses.** Each one with the evidence that ruled it out.
- **Fix direction.** If more than one fix is viable or the fix changes behavior, continue with `team-design-options`.
