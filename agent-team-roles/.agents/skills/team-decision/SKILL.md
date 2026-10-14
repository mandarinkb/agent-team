---
name: team-decision
description: Raise a decision to the user with two or more evidenced options and a recommendation, or, as the lead, present it to the user and record the answer. Use whenever a choice falls under the decision codes D1 to D11.
when_to_use: Required for any teammate raising a decision and for the lead presenting one. Triggers: which option, need the user to choose, approve the plan, approve the commit, accept this difference.
---

# Team decision

The user decides. Read `.agents/protocols/decisions.md` for the codes D1 to D11 and what does not count as a decision.

## As a teammate

1. Check that it is a decision. If running something can answer it, run it and report the evidence instead. Then check `.agents/standing-decisions.md`: an active entry whose codes and scope cover this case settles it. Apply it and cite its id.
2. Make the options concrete first: the evidence, the sketch, the cost to build and to verify.
3. Write the request from `.agents/templates/decision-request.md` as `decision-<n>.md` in the task directory. Two options minimum, a recommendation, and the views of other teammates.
4. Send the lead a message: `[<task-id>] decision: <D-code> <question>` with the file path.
5. Mark the dependent task blocked. Keep working on independent tasks.
6. When the lead relays the answer, act on the user's words, not on a summary.

## As the lead

1. Reject a request that has one option, no evidence, or no recommendation. Send it back with what is missing.
2. Present it to the user in Thai with the structured question tool when available:
   - the question in one sentence,
   - each option with its cost and risk in the description,
   - the recommended option first, labeled `(แนะนำ)`,
   - a link to the request file for detail.
3. Do not choose, do not reword an option to favor one, do not proceed on silence.
4. Append the answer to `decisions.md` with the user's original words, the date, and the D-code.
5. Relay the user's original words to every affected teammate and unblock the task.
6. Append a row to `log.tsv`: the decision, why, the evidence path, and the result.
7. If the same question is likely to come back, ask the user whether to make the answer standing and with what scope. Add it to `.agents/standing-decisions.md` only with the user's own words. D7, D8, D11, and dismissing a critical finding can never be standing.
