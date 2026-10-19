# Decisions

The user makes every decision. Teammates prepare the options. The lead carries them to the user and back.

## Fact or decision

Run it when the answer is observable: what the old endpoint returns, whether a column is nullable, which query is faster. Raise a decision only when no run can settle it.

Always a decision:
- choosing between designs or fixes that both meet the spec,
- changing the spec, a contract, an error shape, or a data format,
- accepting a difference from a migration baseline, or a gap in testing,
- widening or narrowing the scope,
- a new dependency or service,
- a schema change or anything that writes shared data,
- a fourth round on a task,
- push, merge, deploy, delete.

Not a decision, inside the approved spec and your scope: local names, internal structure, the order you write tests, retrying a flaky run once.

When unsure, treat it as a decision.

## Raising one (teammate)

1. Do the work that makes the options concrete: read, run, sketch.
2. Write `.agents/work/<job>/decisions/D-<n>.md` from `.agents/templates/decision-request.md`. At least two real options, each with its cost and risk, and your recommendation. Ask the next free number from the lead.
3. Send the path to the lead. Continue any work that does not depend on it.

## Answering one (lead)

1. Return a request that has one option, no evidence, or no recommendation.
2. Ask the user with the structured question tool. Recommended option first, marked `(แนะนำ)`. The user can always type their own answer.
3. Never pick, reword to favor an option, or proceed on silence. There is no default and no timeout.
4. Record it: `job.py decide <job> D-<n> --quote "<the user's exact words>"`.
5. Send the user's exact words to every teammate the decision affects.
