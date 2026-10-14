---
extends: refactoring
when: Port one PHP API endpoint to Go and prove the Go response matches the recorded PHP baseline before traffic moves.
---

# PHP to Go endpoint

One endpoint per run. The PHP endpoint stays live until the Go endpoint passes parity and the operator moves traffic. A whole-API migration runs this playbook once per endpoint under figure-it-out or a multi-phase plan.

- **Before** "Pin the behavior contract first." Write the endpoint brief from `templates/endpoint-brief.md`. Fill every field. A field you cannot fill means the endpoint is not scoped yet, so stop and report what is missing.
- **In** "Pin the behavior contract first." The pin is a recorded baseline. Write `parity/<endpoint>/cases.jsonl` with at least the happy path, an empty result, a not-found, a validation error, an auth failure, and every edge case from the PHP-to-Go checklist in `templates/endpoint-brief.md`. Run `scripts/parity.py record` against PHP. Use synthetic accounts only. Never record real customer data. Credentials go in `${ENV_VAR}` references, never in the case file.
- **After** "Name the target shape." Run the **blast-radius** skill on the PHP endpoint. List every caller you can prove (web client, mobile app, cron, other services) and the one fact the port is safe because of. An unproven caller is an open risk in the brief, not a guess.
- **Replace** "No compatibility shims, no parallel old-and-new paths." PHP and Go run side by side for this migration. Do not delete, redirect, or disable the PHP endpoint. Traffic moves only when the operator flips the route. Removing PHP is a separate unit after the operator confirms Go served production traffic cleanly.
- **In** "Prove behavior is unchanged on the real artifact" Run `scripts/parity.py check --json` against the Go endpoint. Exit 0 is the only pass. Exit 3 means a case was unreachable, which is INCONCLUSIVE, not a pass. Every `ignore_paths` entry in `parity.json` needs a one-line reason in the brief. Never add an ignore to make a diff go away.
- **Replace** "Confirm the change is worth keeping." The success measure is parity, not reader load. Report MATCH, DIFF, and UNREACHABLE counts from the parity run. A DIFF that the Go side gets right and PHP gets wrong is still a DIFF. Record it in the brief as a deliberate behavior change for the operator to accept, and keep the PHP behavior until they do.
- **Before** "Rebase into small ordered commits." Log the run with the **show-me-your-work** skill, one row per case group and one row per accepted ignore or behavior change. Order commits as baseline cases first, then the Go handler, then the route wiring that stays disabled.

Stop at merge-ready. The operator flips traffic.
