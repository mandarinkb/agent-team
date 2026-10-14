# Decision protocol

The user makes every decision. Teammates prepare the options. The lead carries them to the user and back. This protocol defines what counts as a decision, so the team neither guesses on the user's behalf nor blocks on every small choice.

## What is a decision

Raise a decision request for any of these. The code in brackets goes in the request title.

| Code | Decision |
|---|---|
| D1 | Choosing between two or more viable designs, fixes, or approaches |
| D2 | Changing observable behavior, an API contract, an error shape, or a data format |
| D3 | Accepting a known difference, such as a parity DIFF, a new ignored path, or a skipped check |
| D4 | Widening or narrowing the scope of the task |
| D5 | Adding a dependency, a service, or infrastructure |
| D6 | A schema change, a data migration, or anything that touches shared data |
| D7 | Any irreversible action: push, merge, deploy, delete, force-push, route flip |
| D8 | Approving the plan before implementation and the commit after verification (the two standing gates in every workflow) |
| D9 | Stopping, abandoning, or restarting the task after a dead end |
| D10 | Spending extra review effort, such as a second reviewer on another model for a high-risk change |
| D11 | Changing the team's own rules, skills, workflows, or standing decisions |

## What is not a decision

Decide these yourself, inside the approved plan and your file scope, and log the choice in `log.tsv`:

- Names of local variables, private functions, and test cases.
- The internal structure of code inside an approved design.
- Which test to write first, how to run a command, retries after a flaky run.
- Fixing a defect that qa found in your own change, when the fix stays inside the approved design.

**A fact is not a decision.** When the answer is observable, such as "does the old endpoint return null or an empty list?" or "is approach A faster?", run something and report the evidence. Raise a decision only when no experiment can settle the question.

When you are unsure whether something is a decision, treat it as one.

## Standing decisions

`.agents/standing-decisions.md` holds rulings the user made once for every case of the same kind, within a stated scope. Adapted from pstack's Orchestrate standing orders and its rule to keep the user's original words with their scope.

- **Check it first.** Before raising a decision, read the file. An entry applies when its status is `active`, its codes include this decision's code, and the case is inside its scope. Then act on it, cite its id (for example `SD-3`) in `log.tsv` and in your report, and do not raise the decision.
- **When in doubt, raise it.** If an entry might apply but the scope or wording is unclear, raise the decision and name the entry you considered. Never stretch an entry beyond its scope: "keep string IDs during this migration" does not cover a new API.
- **Never standing.** D7 (irreversible actions), D8 (approving a plan or a commit), D11 (changing the team), and dismissing a critical review finding are asked every time.
- **Who writes it.** The user owns the file. The lead adds an entry only when the user says the answer applies to future cases, copies the user's words exactly, and records the scope and the source decision. Nobody edits or deletes an entry. Revoking changes its status to `revoked <date>` with the user's words.
- **Offer it.** After recording a decision that is likely to recur, the lead asks the user whether to make it standing, and with what scope. That question is itself the user's call.

## How a teammate raises a decision

1. Check `.agents/standing-decisions.md`. If an active entry covers this case, apply it and stop here.
2. Do the work that makes the options concrete. Read the code, run the experiment, sketch both designs. Options without evidence waste the user's time.
3. Talk to the teammates the decision affects if their input changes the options. For example, backend and qa agree on what each option would cost to verify. Do not settle it.
4. Write the request from `.agents/templates/decision-request.md` and send it to the lead. Give at least two real options. "Do nothing" counts when it is real.
5. Mark the dependent task as blocked in the task list, and keep working on anything independent.

## How the lead handles a decision

1. Check the request. Return it to the teammate if it has one option, no evidence, or no recommendation.
2. Merge requests that ask the same question.
3. Present it to the user with the structured question tool when it is available. Put the recommended option first and mark it `(แนะนำ)`. Put each option's cost and risk in its description. Otherwise ask in plain Thai with the same content.
4. Do not pick an option, rephrase an option to favor one, or proceed on "the obvious choice".
5. Record the user's answer in the task's `decisions.md` with the user's original words, the date, and the request code. An agent's summary of the answer is labeled as a summary.
6. Relay the user's original words to every affected teammate, and unblock the task.

## Under time pressure

There is no default answer and no timeout. If the user is away, the dependent work stays blocked and the lead reports what is waiting. Never treat silence as approval.
