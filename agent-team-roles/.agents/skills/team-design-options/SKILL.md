---
name: team-design-options
description: Produce two or more structurally different designs or fix options, with caller usage, type sketches, costs, and risks, for the user to choose from. Use before implementing a feature, a non-trivial fix, or a port plan.
when_to_use: Used by analyst before a feature, a non-trivial fix, or a port plan. Triggers: how should we build this, which approach, options for the fix, port plan.
---

# Team design options

Adapted from pstack's architect skill and its design red flags. The user chooses. Your job is to make the choice clear and well-founded.

## Steps

1. **Ground it.** Start from `investigation.md`. Name the data shape the change is built around and the structure that should hold it: a state machine instead of scattered booleans, a table or map instead of branching, a typed model instead of loose fields.
2. **Write the caller's usage first.** Show two or three realistic call sites or requests and responses as the consumer would write them. Derive the types from the usage, not the reverse.
3. **Design at least two whole shapes.** The second option must differ in structure, not just in naming or a small detail. "Keep the current structure and patch it" is a valid option when it is real.
4. **Sketch each option.** Types, function signatures, module boundaries, and where validation happens. Bodies stay unimplemented.
5. **Screen each option against the red flags:**
   - **Shallow module.** Callers must coordinate several calls for one operation.
   - **Information leakage.** The same internal decision appears in several places.
   - **Ordering by execution step.** Separate load, validate, and save modules repeat the same rules.
   - **Pass-through method.** A layer that forwards the same arguments without adding anything.
6. **Collect costs.** Ask backend, frontend, and qa what each option costs to build and to verify. Record their answers with their names.
7. **Recommend one** and state why, including what the recommendation gives up.

## Output

Write `design.md` in the task directory with the usage, each option's sketch, the red-flag screen, the costs, and the recommendation. Then raise the decision with `team-decision`, linking `design.md`.

## After the decision

The chosen sketch is the contract. During implementation, a needed change to a signature, type, or behavior in the sketch is a new decision (D2). Raise it. Do not absorb it silently.
