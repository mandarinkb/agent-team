# Agent Team

A team of AI teammates that takes a job from an agreed spec to a verified commit, while the user only approves the spec, makes decisions, and reads the test report.

## People and roles

**User**:
The human who approves the spec, makes every decision, and reads the test report.
_Avoid_: Owner, customer

**Lead**:
The main session. It grills the user, writes the spec and tasks, routes work, and carries decisions to the user. It never writes code.
_Avoid_: Team lead, coordinator, orchestrator

**Teammate**:
A subagent the Lead spawns for one step of a Job. It holds one role, works only inside its task's scope, reports to the Lead, and ends.
_Avoid_: Worker, Agent Teams teammate (the team does not use Agent Teams)

**Brief**:
The prompt the Lead spawns a Teammate with: the job, task, round, workflow step, and the ids and paths the step needs.
_Avoid_: Message, handoff note

**Implementer**:
The teammate that writes the code for a task: backend or frontend.
_Avoid_: Developer, coder

**Spec Reviewer**:
The teammate that checks whether implemented code matches the spec, and writes a Fix Task when it does not.
_Avoid_: Code reviewer, reviewer

**QA**:
The teammate that tests the code against the spec on the real surface and writes the Test Report.
_Avoid_: Tester, verifier

## Work

**Job**:
One unit of work the user asks for: a migration, a feature, or a bug fix. A Job has one Spec and many Tasks.
_Avoid_: Ticket, project, task (a task is smaller)

**Grill**:
The interview the Lead runs with the user before any Spec exists, until both agree on the direction.
_Avoid_: Kickoff, discovery

**Spec**:
The agreed description of what a Job must do, written after the Grill and approved by the User.
_Avoid_: Requirements, design doc, plan

**Task**:
A piece of a Job that one Teammate can pick up, finish, and hand to verification.
_Avoid_: Ticket, story, todo

**Fix Task**:
A Task written by the Spec Reviewer or QA that names how the code differs from the Spec, sent back to the Implementer.
_Avoid_: Bug report, defect, finding

**Round**:
One pass of implement, spec review, and test on the same Task. A Task has at most three Rounds before the User decides.
_Avoid_: Iteration, attempt

**Test Report**:
The document in Thai that QA writes for the User, showing what was tested, how, and the result.
_Avoid_: Test summary, QA report

## Trust

**Zero Trust**:
The team's rule that no Teammate's claim counts until a different Teammate re-checks it against the same revision with its own evidence.
_Avoid_: Verification (too narrow), double check

**Claim**:
A statement by a Teammate that something is done or passes, before another Teammate has re-checked it.
_Avoid_: Result, status

**Verified**:
The state of a Task after QA confirmed it against the Spec at the same revision the Spec Reviewer approved.
_Avoid_: Done, complete, passed

**Decision**:
A choice no experiment can settle, which only the User makes, from options a Teammate prepared.
_Avoid_: Approval (an approval is one kind of Decision), question
