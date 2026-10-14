# pstack เจาะลึก: Reference, Prompt Template, Script และ Generator

[← กลับไปหน้ารวม](README.md)

> **ที่มา:** ไฟล์นี้เก็บส่วนที่สองไฟล์ก่อนหน้า ([`PSTACK-WORKFLOW-DESIGN-TH.md`](PSTACK-WORKFLOW-DESIGN-TH.md) และ [`PSTACK-SKILLS-CATALOG-TH.md`](PSTACK-SKILLS-CATALOG-TH.md)) ยังไม่ได้ลงรายละเอียด ได้แก่
> - ส่วนที่เหลือของ `orchestrate.md` และ `multi-phase-plan.md`
> - ไฟล์ใน `references/` ที่ skill ส่งให้ subagent อ่าน
> - script ใน `poteto-mode/scripts/`
> - เครื่องมือใน `tools/` ของ repo
>
> **ระดับการอ่าน:**
> - **อ่านครบ:** playbook และ reference ทุกไฟล์ที่เป็น Markdown
> - **อ่านเฉพาะโครงสร้าง:** script ขนาดใหญ่อย่าง `orch/store.ts` (1,636 บรรทัด), `watch-pr/policy.ts` และ `github.ts` อ่านหัวไฟล์, type, คำสั่ง CLI และ logic หลัก ไม่ได้อ่านทุกบรรทัด
> - **ไม่ได้อ่าน:** โค้ด Pi extension (`plugins/pstack/pi/*.ts`), ไฟล์ mapping `codex-tools.md` และ `pi-tools.md`, playbook ของ why แต่ละแหล่ง (ยกเว้น `incident-postmortem.md`) และไฟล์ test ทั้งหมด เพราะเป็นตัวแปลงให้รันบน runtime อื่นหรือเป็น test ไม่เกี่ยวกับหลักการออกแบบ workflow
>
> **การยืนยัน:** ยังไม่ได้รัน script ใดจริง

---

## สารบัญ

1. [สิ่งที่ได้เรียนรู้เพิ่มจากรอบนี้](#1-สิ่งที่ได้เรียนรู้เพิ่มจากรอบนี้)
2. [Orchestrate: ส่วนที่เหลือ](#2-orchestrate-ส่วนที่เหลือ)
3. [Multi-phase plan: skeleton และ check-plan](#3-multi-phase-plan-skeleton-และ-check-plan)
4. [Reference ของ poteto-mode](#4-reference-ของ-poteto-mode)
5. [Prompt template ของ subagent](#5-prompt-template-ของ-subagent)
6. [Scripts: กลไกที่บังคับแทนคำสั่ง](#6-scripts-กลไกที่บังคับแทนคำสั่ง)
7. [Tools ระดับ repo: generator และ sync](#7-tools-ระดับ-repo-generator-และ-sync)
8. [บทเรียนสำหรับนำไปออกแบบเอง](#8-บทเรียนสำหรับนำไปออกแบบเอง)

---

## 1. สิ่งที่ได้เรียนรู้เพิ่มจากรอบนี้

การอ่านรอบนี้ทำให้เห็นสิ่งที่สองไฟล์ก่อนยังไม่ได้แสดง คือ **pstack ใช้โค้ดบังคับกฎสำคัญที่เขียนไว้ใน playbook ด้วย** ตัวอย่าง:

| กฎใน playbook (ข้อความ) | กลไกที่บังคับจริง (โค้ด) |
|---|---|
| "Verdict ผูกกับ head SHA" | `orch ledger` ใช้ PR + SHA เป็น key และ verdict เป็น union type 5 ค่า |
| "ห้าม merge ถ้า head เปลี่ยน" | `ship-pr` + `gh pr merge --match-head-commit` |
| "ทุกไฟล์ใน store มี writer คนเดียว" | `orch` มี lockfile `.orch.lock` ที่ตรวจ PID ค้างได้ |
| "แผนต้องมีโครงตามนี้" | `check-plan.mjs` ตรวจหัวข้อ, ลำดับ, 10 lanes และ perf 4 ช่อง |
| "project playbook ต้องอ้างข้อความจริง" | `check-playbooks.mjs` |
| "ห้ามลบ worktree ที่ยังใช้อยู่" | `worktree-audit.mjs` ตีเป็น `safe` ได้ก็ต่อเมื่อรู้ข้อเท็จจริงครบทุกข้อ |
| "checkpoint ต้องอ่านกลับได้" | `resume.mjs` ตรวจ hash และลิงก์ก่อน publish แบบ atomic |
| "ชื่อโมเดลมาจากแหล่งเดียว" | `generate.mjs --check` ทำให้ CI fail ถ้ามีสำเนาไม่ตรง |
| "verdict ของ watcher มีชุดคำตายตัว" | `watch-pr/types.ts` กำหนด exit code ต่อ verdict |

นี่คือ principle `encode-lessons-in-structure` ที่ pstack ใช้กับตัวเอง **ส่วนที่ต้องใช้วิจารณญาณเขียนเป็น Markdown ส่วนที่ต้องถูกทุกครั้งเขียนเป็นโค้ด**

---

## 2. Orchestrate: ส่วนที่เหลือ

หัวข้อที่ [`PSTACK-WORKFLOW-DESIGN-TH.md`](PSTACK-WORKFLOW-DESIGN-TH.md) ยังไม่ได้ลงรายละเอียด

### 2.1 Queue and drain (วินัยของการจัดคิว)
- **เมื่อมี agent ทำงานเสร็จ** ให้รัน `orch inbox push <agent> <unit> <status> [--report PATH]` แล้วกลับไปทำงานเดิม **ห้ามรีวิวทันที** ถ้างานนั้นต้องรีวิว ให้สร้างเป็น verifier unit แยก
- **drain เป็นชุดเท่านั้น** ที่ 4 จุด คือ จบ critical section, ตอน rollup ของ track, ตอน watcher ของ frontier ปลุก และก่อนรายงานผู้ใช้ เริ่มทุกชุดด้วย `orch inbox drain` งานที่เข้ามาระหว่าง drain ต้องรอชุดถัดไป
- **critical section ที่ต้องทำให้จบก่อน:** เขียน brief, ทำ stack operation, ตัดสิน conflict, เขียน gate และอัปเดต ledger หรือ frontier
- **ในแต่ละ drain:** จัด pointer เป็น landed, needs-verify, failed, zombie หรือ noise แล้วเขียนผ่าน `orch unit add/set` และ `orch ledger record` → รัน `orch status` → spawn รอบถัดไปใน message เดียว
- **ต้องบันทึกสถานะของ child ทุกตัว** ว่ากลับมาแล้ว, spawn ใหม่ หรือมีงานอื่นรับขอบเขตไปแล้ว ถ้าแอบทำงานของ child ที่หายไปซ้ำเองโดยไม่บันทึก จะซ่อนทั้งค่าใช้จ่ายที่เสียไปและช่องว่างของ coverage
- **จบ drain ด้วย 3 บรรทัดจาก `orch status`:** จำนวนแยกตามสถานะ, สิ่งที่เปลี่ยน และ gate ที่เปิดอยู่

**หลักออกแบบ:** การแจ้งว่างานเสร็จเป็น event ในคิว ไม่ใช่การขัดจังหวะ ตัวนำจึงไม่ถูกดึงออกจากงานที่ทำอยู่ทุกครั้งที่ลูกทีมส่งงาน

### 2.2 Stack safety
- **frontier เป็นค่าที่คำนวณ ไม่ใช่สิ่งที่เล่าเอง** ต้องคำนวณ `frontier.json` ใหม่จาก `gt` (Graphite) หลังทุก merge หรือการเปลี่ยน stack เพราะ base ref บน GitHub อาจเลื่อนระหว่าง restack
- **stack หนึ่งมี stacker ได้คนเดียว** ที่รัน `gt` ได้ และชื่อคนนั้นต้องบันทึกไว้ใน standing orders
- **worker ห้าม rebase และห้ามรัน `gt`** babysitter ทำงานกับ frontier generation เดียว ถ้าเจอ conflict ให้รายงาน stacker
- **การปิดหรือ retarget PR ทำได้ผ่าน stacker เท่านั้น** เพราะการปิด base PR ทำให้ chain ข้างบนทั้งหมดไม่มีฐาน
- **มี retro watcher หนึ่งตัว** คอยดู revert, CI ที่พังหลัง merge และ follow-up ที่ถูกทิ้งไว้

### 2.3 Verification ใน Orchestrate
- ปรับระดับการ verify ให้เท่ากับงาน ถ้า VERIFY เป็นคำสั่งเดียวที่ถูก ให้ worker รันแล้วรายงาน ส่วนตัวนำสุ่มตรวจ
- verifier แยก (ใช้โมเดลต่างตระกูล) ใช้กับงานที่ตรวจยาก ต้องใช้วิจารณญาณ หรือผลกระทบกว้าง
- **verdict 5 ระดับ** (บังคับด้วย type ใน `orch/store.ts`)

| Verdict | ความหมาย |
|---|---|
| `live-ui-verified` | ทดสอบบน UI จริงแล้ว |
| `unit-test-verified` | ผ่าน unit test |
| `type-check-only` | ผ่านแค่ type check (ไม่พอสำหรับงานที่เปลี่ยนพฤติกรรม) |
| `verifier-blocked` | ตรวจไม่ได้เพราะสภาพแวดล้อม (ไม่นับว่าผ่าน) |
| `verifier-failed` | ตรวจแล้วไม่ผ่าน (ต้องสร้าง fix unit ไม่ใช่ตรวจซ้ำ) |

- worker รายงานผลเองได้ แต่ verifier มีน้ำหนักเหนือกว่าบน key เดียวกัน และ **SHA ใหม่ทำให้ verdict เดิมใช้ไม่ได้**
- งานนับว่าเสร็จเมื่อผลถูกบันทึกไว้นอก session แล้ว เช่น push branch และเขียน ledger งานที่อยู่บนเครื่องเดียวแล้วเครื่องนั้นตาย ถือว่าไม่เคยเสร็จ

---

## 3. Multi-phase plan: skeleton และ check-plan

### 3.1 ส่วนท้ายของ skeleton
ต่อจาก section ของแต่ละ PR (ที่สรุปไว้ในไฟล์ catalog):
- **Merge:** มี verdict สะอาดที่ head SHA ตรงกัน, ทำ bugbot triage แล้ว และ base กับ verdict ยังเป็นปัจจุบันตามกฎ patch-id
- **Close the program:** ทุกช่องติ๊กแล้วพร้อมหลักฐาน และรายงานผู้ใช้ตามรูปแบบของ playbook ที่ใช้ทำงาน
- **Appendix A. Prototype evidence:** คำถามที่ prototype ตอบแล้ว พร้อม branch, SHA และลิงก์ รวมถึงคำถามที่ยังพิสูจน์ไม่ได้
- **Appendix B. Alternatives rejected:** ทางเลือกที่พิจารณาแล้วตัดทิ้ง
- **Appendix C. Risks:** ความเสี่ยงแต่ละข้อ อยู่ใน PR ไหน และเจ้าของต้องเฝ้าดูอะไร
- **Appendix D. Links and reading list:** เอกสารที่ต้องอ่าน และ PR ไหนต้องผ่าน `how` หรือ `interrogate`

### 3.2 `check-plan.mjs` ตรวจอะไร (อ่านโค้ดแล้ว)
script นี้คือ **linter ของไฟล์แผน** มันข้าม code fence แล้วตรวจกฎต่อไปนี้ ทุกกฎที่ fail จะพิมพ์ `file:line: ข้อความ`

**กฎด้านภาษา (ทั้งไฟล์ ยกเว้นใน code block)**
- ห้ามมี long dash (– —)
- ห้ามมี curly quote
- ห้ามมี colon กลางประโยค (`: ` ตามด้วยตัวอักษร)

**กฎด้านโครงสร้าง**
- ต้องมี H1 และ intro สั้นกว่า 10 บรรทัด
- ต้องมี `## How to read this` ที่มีวลีบังคับครบ เช่น "One box is one unit of work", "Check a box only when its evidence exists" และกฎ verification
- ต้องมี `## Program checklist` ที่มี H3 ครบ 5 หัวตามลำดับ (Arm the program, Spawn owners, PR mechanics, Verdict and merge, Boot recipe) แต่ละหัวต้องมีช่อง checkbox และต้องพูดถึง standing orders, installed plugin, hourly tick และ status message
- ต้องมี `## Close the program` ที่มีช่อง checkbox
- ต้องมี section ของ PR อย่างน้อยหนึ่งอัน

**กฎต่อ PR**
- sub-block ต้องเรียงตรงตามนี้: Depends on, Files, Build, You see, Verify unit, Verify live, Verify perf, Review gate, Merge
- Depends on ต้องระบุอะไรสักอย่าง (หรือ None)
- block ของ Verify ทั้งสามต้องขึ้นต้นด้วยประโยคกฎ "Tests alone are not sufficient verification..."
- Verify live ต้องมี **lane ครบ 1-10** และทุก lane ต้องมี `Save \`...\`` (screenshot) และ "Pass when"
- Verify perf ต้องมีช่องเรียงตรง: Metric, Probe, Baseline, Rule
- Review gate ถ้าเขียนว่า None ต้องไม่มีช่อง ถ้ามี ต้องพูดถึง screenshot และ video

**กฎด้านท้ายไฟล์:** หลัง Close ต้องเป็น Appendix เท่านั้น และต้องมี Appendix ที่ชื่อมีคำว่า Prototype evidence

**ข้อสังเกต:** กฎเรื่องภาษา (long dash, colon) ที่ `unslop` เขียนเป็นข้อความ ถูกบังคับด้วยโค้ดใน `check-plan.mjs` ด้วย

---

## 4. Reference ของ poteto-mode

### 4.1 `merge-safety.md`: ความปลอดภัยของการ merge และ restack
ใช้คู่กับ Shipping และก่อนเปลี่ยน topology ใน Autopilot-stack **เอกสารนี้ไม่ได้ให้สิทธิ์ merge** แต่เพิ่มการตรวจ revision และปลายทาง

**ก่อนแก้ chain ต้องยกเลิก merge ที่ค้างอยู่**
```sh
ship-pr inspect --repo "$owner/$repo" --pr "$pr" > "$record_file"
ship-pr cancel-pending --record "$record_file"
```
- `inspect` คืน landing record (repo, PR, head OID, base branch, base OID, กลไกที่ค้าง และ merge commit)
- `cancel-pending` อ่านสถานะใหม่ ปิด auto-merge แล้วเอาออกจาก queue
- **ต้องได้ exit 0 และ `kind: cancelled` เท่านั้นจึงทำต่อได้** ถ้าได้ `changed`, `not-open`, `still-pending` หรือ `unavailable` ให้ reconcile ก่อน **field ที่หายไปหรือ API ที่ไม่รองรับ ไม่ได้แปลว่าไม่มี request ค้าง**
- การยกเลิกเป็นแค่สภาพที่สังเกตได้ ไม่ใช่ lock คนอื่นยังตั้ง merge ใหม่ได้

**rebase ลูกหลัง parent ถูก squash**
```sh
git merge-base --is-ancestor "$old_parent_tip" "$child"
git rebase --onto "$trunk_tip" "$old_parent_tip" "$child"
git push --force-with-lease="refs/heads/$child:$captured_remote_head" origin "HEAD:refs/heads/$child"
```
- เก็บ SHA ของ remote ก่อน rewrite ด้วย `git ls-remote` เพราะ background fetch อาจทำให้ tracking ref เลื่อน
- ถ้า lease ปฏิเสธ ให้ fetch แล้ว reconcile **ห้าม refresh lease แล้ว push ทับ**

**สิ่งที่ service รับประกันได้และไม่ได้**
- GitHub รับประกัน head ได้ด้วย `--match-head-commit`, `expectedHeadOid` หรือ `sha` แต่ **ไม่มีตัวไหนรับประกัน base branch**
- หลัง merge ต้องยืนยันว่าสถานะเป็น `MERGED`, head ตรง, base ตรง, merge commit ไม่เป็น null และ `git merge-base --is-ancestor <merge_commit> <destination_tip>` ผ่าน

### 4.2 `resume-storage.md`: ที่เก็บ checkpoint
- ใช้ `resume.mjs` เก็บไว้ใน **Git common directory** ใต้ `pstack/resume/` ทุก worktree ของ repo เดียวกันจึงใช้ที่เดียวกัน และ Git ไม่ commit ไฟล์เหล่านี้
- `latest.json` ชี้ไปที่ checkpoint ล่าสุดที่สมบูรณ์ เก็บ worktree, branch, เวลา, note และ hash ของ artifact
- **ขั้นตอนการเขียน:** `begin` (จองโฟลเดอร์ใหม่) → เขียน `resume.md` และ artifact → `publish` (ตรวจลิงก์, ความเป็นเจ้าของ และเนื้อหา แล้วแทนที่ `latest.json` แบบ atomic) → `read` เพื่อยืนยัน
- checkpoint ที่ publish แล้วแก้ไม่ได้ ครั้งถัดไปต้องใช้โฟลเดอร์ใหม่
- **ผลของ `read`:** exit 0 `checkpoint` = ใช้ได้, exit 2 `missing` = ไม่มี ให้ไปดู transcript แทน, exit 1 `unavailable` = เสียหาย ต้องวินิจฉัย ห้ามข้ามแบบเงียบ ๆ
- pointer นี้เป็นแค่ตัวบอกตำแหน่ง ไม่ใช่ scheduler หรือ lock

### 4.3 `bugbot-triage.md`: จัดการ comment จาก bot รีวิว
**เป้าหมายคือ** ไม่มองว่าทุก comment ต้องแก้โค้ด และก็ไม่ข้ามทุก comment เช่นกัน

**3 หมวด**
| หมวด | เมื่อไร | ทำอะไร |
|---|---|---|
| `fix` | ปัญหาที่น่าเชื่อเรื่อง correctness, security, privacy, data loss, auth, billing, migration, idempotency หรือ race | แก้ใน PR ล่างสุดที่เป็นเจ้าของโค้ด แล้วตอบพร้อม SHA |
| `dismiss` | ตรงกับรูปแบบ noise ที่บันทึกไว้ และโค้ดปัจจุบันพิสูจน์ได้ว่าไม่ต้องแก้ | ตอบเหตุผลสั้น ๆ แล้ว resolve |
| `ask` | เรื่องใหม่, รุนแรง, เกี่ยวกับ security หรือข้อมูล หรือกำกวม | ถามผู้ใช้ |

**ถ้าไม่แน่ใจให้ถาม:** ข้าม comment ที่เป็น noise มีต้นทุนต่ำ แต่ข้ามบั๊กจริงด้านข้อมูลหรือ security มีต้นทุนสูง

**รูปแบบการบันทึกบทเรียน (pattern)**
```markdown
### <ชื่อ pattern>
- Confidence: candidate | recurring | strong
- Skip when: <เงื่อนไข>
- Do not skip when: <ขอบเขตความเสี่ยง>
- Example signal: <วลีหรือบริบท>
- Source: <PR/comment>
```
ระดับความเชื่อมั่น: `candidate` = 1-2 ตัวอย่าง, `recurring` = dismiss มาแล้วหลายครั้ง, `strong` = แคบ ยืนยันซ้ำ และความเสี่ยงต่ำ

**ตัวอย่าง pattern ที่บันทึกไว้:** การเปลี่ยน UI ที่ตั้งใจ, export ที่ PR ข้างบนใน stack ใช้, โค้ดซ้ำชั่วคราวระหว่างย้าย path, invariant ที่ framework รับประกันแล้ว, follow-up ที่เจ้าของประกาศไว้ และ comment ที่ bot ถอนเอง

**ห้ามข้ามโดยอัตโนมัติ:** security, privacy, auth, billing, data retention, permission, ปัญหาที่รุนแรง, migration, schema, idempotency, concurrency และกรณีที่แก้นิดเดียวแต่ลดความเสี่ยงได้ชัด

**บทเรียนที่น่าสนใจ**
- **การเขียนพฤติกรรมของ browser ขึ้นใหม่เอง** (sticky, scroll, clip-path): finding ของ bot มักถูกเกือบทุกครั้ง ใน PR หนึ่งมี 18 finding และต้องแก้ทั้งหมด
- **คำกล่าวว่า contract test ไม่ตรงกับเอกสาร:** ให้รัน test ก่อนเสมอ เพราะการแก้รอบก่อน ๆ ทำให้ข้อความเปลี่ยนจนไม่ตรงจริง
- **finding ด้าน security ที่ล้าสมัย** เพราะถูกแก้แล้วใน commit หลังของ PR เดียวกัน
- **คำขอให้ทำ error condition ที่แคบให้กว้างขึ้น** เช่น `ENOENT` → ทุก error: ความแคบนั้นมักมีความหมาย การทำให้กว้างจะกลบ error จริง

**หลักออกแบบ:** เอกสารนี้ถูกเขียนให้ **เติมได้เรื่อย ๆ** และมีระดับความเชื่อมั่นกำกับ เป็นตัวอย่างของ "หน่วยความจำของทีม" ที่ agent อ่านและเขียนเพิ่มได้

---

## 5. Prompt template ของ subagent

ทุก skill ที่ fan-out แยก prompt ไว้ใน `references/` มีรูปแบบเดียวกัน คือ **บทบาท → ข้อมูลที่เติมเข้าไป (placeholder) → วิธีทำงาน → รูปแบบ output ตายตัว → สิ่งที่ห้ามทำ**

### 5.1 `how`: explorer และ explainer
**Explorer** (`{QUESTION}`, `{EXPLORATION_ANGLE}`)
- บอกให้รู้ว่ามี explorer อื่นทำงานขนานอยู่ ให้เจาะลึกเฉพาะมุมของตัวเอง
- วิธีทำงาน 5 ขั้น: หา entry point → ไล่ flow → map abstraction หลัก → หา boundary → หาสิ่งที่ไม่ชัด
- "Don't guess from names. Read the code." และ "I couldn't determine X ดีกว่าแต่งขึ้นมา"
- **Output:** Components Found / Flow / Files Read / Boundaries / Non-Obvious Things / Open Questions

**Explainer** (`{QUESTION}`, `{EXPLORER_FINDINGS_ALL}`)
- รวมผลของ explorer ถ้าขัดกัน ให้เปิดโค้ดตรวจเอง แต่ไม่ต้องสำรวจใหม่ทั้งหมด
- กลุ่มเป้าหมายคือวิศวกรอาวุโสที่ยังไม่รู้จักส่วนนี้
- ใช้ mermaid หรือ ASCII เมื่อ flow มีหลาย component
- **สไตล์:** เขียนชื่อจริงอย่าง "`UserService` เรียก `AuthClient.refresh()`" แทน "service ส่งงานต่อให้ client"

### 5.2 `why`: investigator และ synthesizer
**Investigator**
- **ท่าทีในการทำงาน:** ยกคำพูดมาตรง ๆ ไม่ถอดความ, ค้นกว้างก่อนลึก, **บันทึกสิ่งที่ค้นไม่ใช่แค่สิ่งที่เจอ**, อย่าเชื่อเรื่องเล่าที่ลงตัวเกินไป (หลักฐานที่ขัดแย้งน่าสนใจที่สุด), ถามว่าถ้าข้อสรุปผิดจะยังเห็นหลักฐานนี้ไหม และห้ามแต่ง
- **วินัยด้านหลักฐาน:** อย่าสับสนกลไกกับแรงจูงใจ (การเปลี่ยน `limit=50` เป็น `100` บอกแค่ว่าเปลี่ยน ไม่ได้บอกว่าทำไม), อย่าอนุมานเจตนาจากสไตล์โค้ด และอย่าเอาหลักฐานของ feature Y มาตอบคำถามเรื่อง X
- **Output:** Source / What I Searched / Direct Evidence / Indirect Evidence (พร้อมการตีความทางอื่น) / Contradictions / Gaps / Additional Leads

**Synthesizer:** ติดป้าย `[Direct]`, `[Supported]` และ `[Inferred]` ทุกข้อ แยก Competing Hypotheses เป็น for/against และ Sources Consulted ต้องครบทั้ง 7 ประเภท แม้ประเภทที่ไม่ได้ค้น

**`incident-postmortem.md`:** ใช้เมื่อโค้ดดูเป็นแบบป้องกัน (retry, timeout, null check, rate limit) เพราะโค้ดลักษณะนี้มักเกิดหลัง incident ให้ค้น postmortem, ticket ที่ติด label `sev-*` และช่อง `#incident-*` ช่วงที่โค้ดถูกเพิ่มเข้ามา

### 5.3 `epistemics.md`: กรอบระดับความมั่นใจ
เป็นเอกสารที่ควรอ่านมากที่สุดถ้าจะออกแบบ agent ที่ต้องรายงานข้อเท็จจริง

**5 ระดับความมั่นใจ**
| ระดับ | ความหมาย | ถ้อยคำ |
|---|---|---|
| **Direct** | มีคนเขียนเหตุผลไว้ตรง ๆ (PR, ticket, comment, doc) | "This exists because X" + อ้างอิง |
| **Supported** | หลักฐานทางอ้อมหลายชิ้นชี้ไปทางเดียวกัน | "The evidence points strongly to X: [หลักฐาน]" |
| **Inferred** | ตีความจากบริบท ไม่มีหลักฐานตรง | "appears", "likely", "suggests" + ห่วงโซ่การอนุมาน |
| **Speculative** | สมมติฐานที่หลักฐานบาง | "One possibility is X, but no direct evidence" |
| **Unknown** | ค้นแล้วไม่เจอ | "We searched X, Y, Z and found nothing" ระบุว่าค้นอะไร |

**กฎด้านถ้อยคำ**
- คำอย่าง "because", "was designed to", "fixes" และ "the team decided" ต้องมีแหล่งอ้างอิงอยู่ติดกัน
- **คำที่ห้ามใช้:** obviously, clearly, of course, just และ "I think"

**กับดักที่ต้องระวัง**
- **Rationalization:** อย่าสร้างเหตุผลสวย ๆ ให้ประวัติที่ยุ่ง, อย่าคิดว่า pattern ที่สม่ำเสมอต้องตั้งใจ (อาจแค่ copy-paste) และ "ไม่มีหลักฐานว่ามี" ไม่เท่ากับ "มีหลักฐานว่าไม่มี"
- **Sycophancy:** ถ้าผู้ใช้ถามว่า "ทำแบบนี้เพราะ performance ใช่ไหม" ให้มองเป็นสมมติฐานหนึ่ง แล้วตรวจอย่างอิสระ
- **หลักฐานขัดกัน:** แสดงทั้งสองฝั่ง ไม่เลือกฝั่งที่เล่าง่ายกว่า

**คำกล่าวอ้างเกี่ยวกับการตัดสินใจของคน:** ต้องหาคำพูดต้นฉบับที่ระบุตัวผู้พูดได้ เช่น "avoid that endpoint during this migration" ต่างจากที่ agent สรุปว่า "the user permanently forbids that endpoint" และสำเนาของข้อสรุปเดียวกันหลายแห่งนับเป็นหลักฐานสายเดียว

**Calibration check ก่อนส่ง:** ทุกข้ออ้างมีแหล่งอ้างอิงไหม, ถ้อยคำตรงกับระดับไหม, กำลังใช้ตัวโค้ดเป็นหลักฐานเจตนาของตัวเองหรือเปล่า และ **ถ้าไม่มีส่วน "What We Don't Know" เลย ให้สงสัย**

### 5.4 `architect`: runner prompt, red flags และ rationale template
**Runner prompt** (ส่งให้ runner ทุกตัวใน Phase B)
- **เขียนการใช้งานจากมุมผู้เรียกก่อน** คือ README และตัวอย่างการเรียก 2-3 จุด แล้วค่อยสร้าง type ตามนั้น ถ้าสองอย่างไม่ตรงกัน ให้แก้ type ให้ตรงกับการใช้งาน
- Data structure ก่อน ถ้าคำตอบคือ "เดี๋ยวค่อยเพิ่ม index หรือ cache" แปลว่าโครงสร้างผิด
- interface ต้องเล็กแต่ซ่อนความซับซ้อนได้มาก และห้ามใช้ wire type ใน public API
- ใช้ `not implemented` ใน body และ `// TODO` ใน pseudocode ให้คนอ่านไล่ data ได้จาก type อย่างเดียว
- **"Don't hedge against the others"** ความต่างระหว่าง candidate คือสัญญาณที่ใช้เลือก ถ้าทุกตัวเลือกทางกลาง ๆ ที่ดูปลอดภัย การสำรวจก็ไม่มีประโยชน์

**Design red flags (4 ข้อ)**
| Red flag | สัญญาณ | ทางแก้ |
|---|---|---|
| **Shallow module** | ผู้เรียกต้องประสานหลาย method เพื่องานเดียว และ option เปิดเผยขั้นตอนภายใน | interface เล็ก แต่มีพฤติกรรมข้างในมาก |
| **Information leakage** | การตัดสินใจภายในเดียวกันปรากฏหลายที่ และ wire type ถูก re-export | parse เป็น domain type ไว้หลัง interface |
| **Temporal decomposition** | แบ่ง module ตามลำดับการทำงาน (load/validate/save) | แบ่งตามความรู้และความเป็นเจ้าของ |
| **Pass-through method** | method ที่ส่ง argument เดิมต่อไปโดยไม่เพิ่มอะไร | ลบทิ้ง หรือย้ายความรับผิดชอบไปที่ module ที่ทำงานนั้นจริง |

ระวังอย่าสับสน **deep module** (ดี: ความสามารถรวมอยู่หลัง interface เดียว) กับ **deep call chain** (ไม่ดี: ความเข้าใจกระจายไปหลายชั้น)

**Rationale template (หน้าเดียว)**
Problem → **Usage (caller's view, เขียนก่อน)** → Shape → Synthesis decision → Tradeoffs accepted ("we accept X in exchange for Y") → **Alternatives considered (บังคับ อย่างน้อย 1 แบบ)** → Implementation reconciliation → Open questions (เขียนเป็นคำถาม) → Next implementation step (ประโยคเดียว)

### 5.5 `interrogate`: rubric, code-quality lens และ lead judgment
**Rubric (6 มุมมอง ใช้เฉพาะมุมที่เกี่ยวข้อง)**
1. **Correctness:** edge case, error handling, race, idempotency และ concurrency ถ้าเจอบั๊ก ต้องไล่ call chain ให้เห็น ไม่ใช่แค่บอกว่า "อาจเป็น nil"
2. **Root causes vs symptoms:** guard ที่บัง invariant, retry ที่ซ่อน contract ที่พัง, cast ที่ปิด modeling error และ comment "อย่าทำ X" ที่ควรเป็น type หรือ lint
3. **Structural integrity:** boundary, ระดับ abstraction, coupling, ความเหมาะของ data model, เพิ่มเข้าไปแบบแปะหรือกลมกลืน และการมี API เก่ากับใหม่คู่กัน
4. **Verification:** มี test ไหม test พฤติกรรมหรือ implementation และตรวจของจริงหรือตัวแทน
5. **Complexity budget:** abstraction ที่ใช้ที่เดียว, config สำหรับกรณีที่ยังไม่มี และ compat path ที่หมดหน้าที่แล้ว
6. **Security:** ไล่ input ไปถึงจุดอันตรายให้เห็นจริง

**Code-quality lens (8 มิติ):** ทะเยอทะยานเรื่องการลดโครงสร้าง ("code judo"), ไฟล์ห้ามโตเกิน 1,000 บรรทัด, ห้ามมี if กระจาย, เอียงไปทางทำ design ให้สะอาด, โค้ดตรงไปตรงมาดีกว่าโค้ดที่ทำงานแบบมีมนตร์, type และ boundary ต้องสะอาด, logic ต้องอยู่ใน layer ที่ถูกและใช้ helper ที่มีอยู่ และระวังการทำงานแบบลำดับที่ไม่จำเป็นกับการ update ที่ไม่ atomic **เกณฑ์อนุมัติ:** ห้ามอนุมัติเพียงเพราะพฤติกรรมดูถูกต้อง

**Lead judgment (การกรองของตัวนำ)**
- **Nitpick gravity:** reviewer ที่หาปัญหาจริงไม่เจอ มักขยายเรื่องเล็กให้ดูใหญ่ ถ้ามีแต่ nit แปลว่าโค้ดน่าจะดีแล้ว
- **สมมติฐานกับของจริง:** "ถ้าส่ง null มาจะเป็นอย่างไร" นับเป็นปัญหาก็ต่อเมื่อผู้เรียกส่ง null มาได้จริง
- **คำเตือนเรื่อง abstraction ที่เร็วเกินไป:** ถามว่าโค้ดนี้จะต้องเปลี่ยนแบบที่สองไหม
- **"ผมคงทำต่างไป":** false positive ที่พบบ่อยที่สุด ให้ dismiss
- **สัญญาณว่าขาดบริบท:** reviewer แนะนำให้แก้โค้ดที่ไม่ได้อยู่ใน diff หรือชี้รูปแบบที่สอดคล้องกับส่วนอื่นของ codebase
- **เมื่อ reviewer ถูก:** หลายโมเดลเจอตรงกัน, มี execution path ชัดเจน หรือคุณอ่านแล้วคิดว่า "...ใช่จริง"
- **Calibration:** ถ้า Act On มีเกิน 5 ข้อ แปลว่ายังกรองไม่พอ ส่วน Dismissed เป็นกลไกสร้างความไว้ใจ เพราะผู้ใช้เห็นว่าอะไรถูกตัดทิ้งและเพราะอะไร

---

## 6. Scripts: กลไกที่บังคับแทนคำสั่ง

ทุก script ใน `poteto-mode/scripts/` ที่เขียนด้วย TypeScript ต้องรันด้วย **bun** ส่วนไฟล์ `.mjs` รันด้วย node ได้

| Script | ภาษา | ใช้ใน | หน้าที่ |
|---|---|---|---|
| `check-plan.mjs` | node | Multi-phase plan | linter ของไฟล์แผน (หัวข้อ 3.2) |
| `check-playbooks.mjs` | node | poteto-mode | ตรวจ project playbook |
| `resume.mjs` | node | Pause / Pickup | checkpoint |
| `worktree-audit.mjs` | node | Worktree cleanup | จัดกลุ่ม worktree |
| `orch/orch.ts` + `store.ts` | bun | Orchestrate | ระบบบันทึกสถานะ |
| `watch-pr/watch-pr` | bun | Babysit, Shipping | เฝ้า PR และให้ verdict |
| `watch-pr/ship-pr` | bun | Shipping | inspect และยกเลิก merge ที่ค้าง |
| `bootstrap.ts` | bun | ทุก script ที่เป็น bun | ติดตั้ง dependency อัตโนมัติ |

### 6.1 `check-playbooks.mjs`
- อ่าน `.agents/playbooks/*.md` ของโปรเจกต์
- **ตรวจ 3 เรื่อง:**
  1. frontmatter ต้องมี `when:`
  2. ทุกชื่อใน `extends:` ต้องมี playbook นั้นอยู่จริงใน pstack
  3. ทุกบรรทัดที่ขึ้นต้นด้วย `**After**`, `**Before**`, `**Replace**` หรือ `**In**` ต้องมีข้อความในเครื่องหมายคำพูด และข้อความนั้นต้องปรากฏใน playbook ที่ extend จริง (เทียบแบบไม่สนช่องว่าง)
- ผ่านแล้วพิมพ์ "Every project playbook matches this pstack's playbooks."
- **หลักออกแบบ:** project playbook ไม่ใช้เลขขั้นตอนเป็นตัวอ้างอิง แต่ยกข้อความของขั้นตอนมาตรง ๆ เมื่อ pstack อัปเกรดแล้วเปลี่ยนข้อความ script จะจับได้ทันที

### 6.2 `resume.mjs`
- คำสั่ง: `begin | publish | read --project <dir> [--note <file> --artifact <file> ...]`
- output เป็น JSON ที่มี `kind`: `directory`, `checkpoint`, `missing` หรือ `unavailable`
- รายละเอียดอยู่ในหัวข้อ 4.2

### 6.3 `worktree-audit.mjs`
- **อ่านอย่างเดียว ไม่ลบอะไรเลย** การลบยังต้องให้คนตัดสินตาม playbook
- คอลัมน์: SIZE, AGE, MERGED, DIRTY, REMOTE, PR, LAST_CHAT, BUCKET, WORKTREE
- ทุกข้อมูลที่ตรวจเป็น `Fact` ซึ่งมีสองแบบ คือ `{ known: true, value }` หรือ `{ known: false }`
- **ตรรกะการจัดกลุ่ม (อ่านจากโค้ด)**
```js
if (dirty.known && dirty.value.wip > 0) return "hold-wip";
if (pr.known && pr.value?.state === "OPEN") return "hold-open-pr";
if (recent.known && recent.value) return "verify-recent-chat";   // แชตภายใน 4 วัน
if (Object.values(facts).some((fact) => !fact.known)) return "review";
if (ancestry.value) return "safe";
if (pr.value?.state === "MERGED" && pr.value.headRefOid === head.value) return "safe";
return "review";
```
- **หลักออกแบบ:** การจัดเป็นกลุ่ม "เก็บไว้" ใช้ข้อเท็จจริงข้อเดียวก็พอ แต่ **การจัดเป็น `safe` ต้องรู้ข้อเท็จจริงครบทุกข้อ** ถ้ามีข้อไหนตรวจไม่ได้ จะตกไปอยู่ `review` ไม่มีทางเป็น safe โดยไม่ตั้งใจ
- อ่าน transcript ทั้งของ Claude Code (`~/.claude/projects`) และของ Pi เพื่อหาว่าแชตล่าสุดที่ใช้ worktree นั้นคือเมื่อไร

### 6.4 `orch` (Orchestrate bookkeeping)
- CLI ที่สร้างด้วย commander (`bun orch.ts [--store <dir>] [--json] [--force] <command>`) และรับ path ของ store จาก `--store` หรือ `ORCH_STORE`
- **คำสั่ง**

| กลุ่ม | คำสั่ง |
|---|---|
| ระดับบนสุด | `init`, `status` (สร้าง `status.md` และพิมพ์สรุป) |
| `unit` | `add`, `set` (state, branch, PR, SHA), `get`, `list`, `counts` |
| `ledger` | `record` (บันทึก verdict + evidence), `check`, `summary` |
| `inbox` | `push <agent> <unit> <status>`, `drain`, `count` |
| `gate` | `park`, `resolve`, `list` |
| `frontier` | `set --repo` (อ่าน stack จาก Graphite), `show` |
| `standing` | `add`, `show` |

- **verdict ถูกบังคับด้วย type:** `parseVerdict` ยอมรับเฉพาะ 5 ค่าในหัวข้อ 2.3 ค่าอื่นจะ error
- **lock:** `.orch.lock` เก็บ PID ของเจ้าของ ถ้า PID นั้นไม่อยู่แล้ว จะรับ lock มาแทน (ตรงกับ principle `make-operations-idempotent` ที่พูดถึง self-healing lock)
- ไฟล์ข้อมูลเป็น TSV หรือ JSON ธรรมดาที่อ่านได้โดยไม่ต้องใช้ CLI ส่วน CLI ใช้แค่เพื่อให้เขียนถูกรูปแบบเสมอ

### 6.5 `watch-pr` และ `ship-pr`
- ทั้งคู่เป็น wrapper 6 บรรทัด ที่เรียก `bootstrap.ts` แล้ว import `cli.ts` หรือ `shipping-cli.ts`
- **option ของ `watch-pr`:** `--owner`, `--repo`, `--pr`, `--stack`, `--queued-stack`, `--stack-prs <n,...>`, `--interval` (ค่าเริ่มต้น 60 วินาที), `--sweep-interval`, `--timeout`, `--max-query-errors`, `--status-only`, `--allow-draft` และ `--pretty`
- **3 โหมด:** `single`, `stack` และ `queued-stack`
- **verdict และ exit code (จาก `types.ts`)**

| Verdict | ประเภท | Exit | ความหมาย |
|---|---|---|---|
| `QUEUE`, `STATUS`, `WAITING`, `ADVANCE`, `RETRY` | ยังไม่จบ | ไม่มี | กำลังรอ, frontier เลื่อนแล้ว หรือ query ล้มแล้ว retry |
| `STATUS` (status-only) | จบ | 0 | พิมพ์ตารางครั้งเดียว |
| `READY` | จบ | 0 | PR หรือ stack พร้อม merge |
| `COMPLETE` | จบ | 0 | queue merge ครบแล้ว |
| `BLOCKER` merge-conflicts | จบ | 2 | มี conflict |
| `BLOCKER` review-threads | จบ | 3 | มี thread ค้าง |
| `BLOCKER` failing-checks | จบ | 4 | CI fail |
| `TIMEOUT` | จบ | 5 | หมดเวลา |
| `BLOCKER` merge-gate | จบ | 6 | draft, changes-requested หรือ review-required |
| `BLOCKER` status-query | จบ | 7 | query สถานะล้มเหลวซ้ำ |

- `WAITING` มีสองเหตุผล คือ `pending-checks` และ `merge-queue`
- **หลักออกแบบที่น่าเรียนรู้:**
  - **ใช้ type บังคับความถูกต้อง** เช่น `PrNumber` เป็น branded type และ `NonEmpty<T>` บังคับว่า list ไม่ว่าง (ตรงกับ `type-system-discipline`)
  - **exit code แยกตามประเภท blocker** script หรือ agent ที่เรียกใช้จึงแตกแขนงได้โดยไม่ต้อง parse ข้อความ
  - ผล query ที่ล้ม (`unavailable`) ไม่เคยถูกตีความว่าผ่าน

### 6.6 `bootstrap.ts`
- ตรวจว่ารันบน bun ถ้าไม่ใช่ จะแสดงข้อความชัดเจนแทนการ crash แบบอ่านไม่ออก
- คำนวณ hash ของ `package.json` + `bun.lock` แล้วเทียบกับ install key ใน `node_modules` ถ้าไม่ตรง จะติดตั้ง dependency ใหม่
- **หลักออกแบบ:** script ติดตั้งตัวเองได้ agent ไม่ต้องจำว่าต้องรัน `bun install` ก่อน

---

## 7. Tools ระดับ repo: generator และ sync

### 7.1 `tools/generate.mjs`: ทำให้ "แหล่งความจริงเดียว" เป็นจริง
- **ทำงานซ้ำได้ผลเหมือนเดิม** ถ้ารัน `--check` จะไม่เขียนอะไร แต่จะ fail ถ้ามีสำเนาที่ไม่ตรง (ใช้ใน CI)
- **แหล่งความจริงและสิ่งที่ถูก stamp ออกไป**

| แหล่งความจริง | stamp ไปที่ |
|---|---|
| `VERSION` | version ใน plugin manifest ทุกตัวและ Pi `package.json` (และ `CHANGES.md` ต้องมีหัวข้อของเวอร์ชันนี้) |
| frontmatter ของแต่ละ skill | ขอบเขต Agent Skills ที่ Codex, Prime, opencode และ Gemini อ่าน |
| ตาราง Slash commands ใน `docs/reference.md` | prompt stub ของ Codex (จำนวนแถวต้องเท่ากับจำนวน public skill พอดี) |
| `models.json` | ส่วน `## Models` และ `## Reasoning effort` ของทุก skill, ตารางใน interrogate, setup-pstack, mapping ของ Codex/Pi และ effort agent ทุกระดับ |
| ตาราง Per-skill notes ใน `codex-tools.md` | preamble ของ Codex ในแต่ละ skill |
| `DRIVER_PLAYBOOKS` | บรรทัด "Resolve the driver skill" ใต้หัวของ playbook |
| `agents/*.md` | รายการ agents ใน `plugin.json` |
| `comment-sicko.md`, LICENSE | สำเนาใน `poteto-mode/references/` |

- **กฎพิเศษ:** **ห้ามมีชื่อโมเดล** (ID แบบ claude-* หรือชื่อตระกูลใน backtick) ในเนื้อหา skill นอกส่วนที่ generator stamp ถ้ามีจะ fail
- ตรวจด้วยว่า marketplace.json ชี้ไปที่ plugin ที่มีอยู่จริง และ path ใน Pi package มีอยู่จริง

**หลักออกแบบ:** ทุกค่าที่ต้องเหมือนกันหลายที่ มีเจ้าของไฟล์เดียว ส่วนที่เหลือเป็นสำเนาที่ generator เขียนให้ ถ้ามีคนแก้สำเนาเอง CI จะจับได้

### 7.2 `tools/sync.mjs` และ `forks.json`: ตามต้นฉบับโดยไม่ทิ้งการแก้ของตัวเอง
- `bun tools/sync.mjs <component> <new-sha> [--dry-run]` ดึงต้นฉบับ (Cursor pstack) เวอร์ชันใหม่
- **ทำงานเป็น 3-way merge** ระหว่าง ต้นฉบับเก่า / ต้นฉบับใหม่ / ฉบับ port
  - ฉบับ port ตรงกับต้นฉบับเก่า → อัปเดตเป็นฉบับใหม่
  - ต้นฉบับไม่ได้แตะ แต่ฉบับ port ต่างออกไป → ถือว่า fork และไม่แตะ
  - ต่างกันทั้งสามทาง → `git merge-file` ถ้า conflict จะเขียน marker ลงไฟล์ ซึ่ง generator จะไม่ยอมให้ผ่าน
  - ไฟล์ binary ที่ต่างกันทั้งสามทาง → fail เลย
- `substitutions.json` แปลงคำของ Cursor เป็นของ Claude Code แบบกลไก และมี denylist ของคำที่ต้องให้คนเขียนประโยคใหม่
- **`forks.json`** ประกาศทุกไฟล์ที่ port ตั้งใจแก้ต่างจากต้นฉบับ แต่ละรายการมี `kind` (policy / port-feature), `why`, `since` (เวอร์ชัน) และ `upstream` (เสนอกลับต้นฉบับแล้วหรือยัง) **ถ้ามี fork ที่ไม่ได้ประกาศ sync จะ fail**
- ตัวอย่างใน forks.json: `architect/SKILL.md` ถูกแก้ให้ต้องเทียบส่วนที่เบี่ยงกับ sketch ก่อนปิดแต่ละหน่วย และ `create-verification-skill` ถูกแก้ให้ตั้งชื่อ skill ที่สร้างว่า `verify` เพื่อแทน `/verify` ของ Claude Code

**หลักออกแบบ:** เมื่อดัดแปลงชุดคำสั่งของคนอื่นมาใช้ ให้ **ประกาศทุกจุดที่ fork พร้อมเหตุผล** แล้วให้เครื่องมือแยกสิ่งที่ต้นฉบับเปลี่ยนออกจากสิ่งที่เราเปลี่ยนเอง

---

## 8. บทเรียนสำหรับนำไปออกแบบเอง

ข้อสรุปจากการอ่านรอบนี้ ต่อจาก checklist ใน [`PSTACK-WORKFLOW-DESIGN-TH.md`](PSTACK-WORKFLOW-DESIGN-TH.md)

1. **ใช้ Markdown กับเรื่องที่ต้องใช้วิจารณญาณ และใช้โค้ดกับเรื่องที่ต้องถูกทุกครั้ง** เช่น การเลือกว่าจะแก้บั๊กอย่างไรเป็น Markdown แต่การตรวจว่า SHA ตรงก่อน merge เป็นโค้ด
2. **ทุก CLI ที่ agent เรียกควรคืน output ที่มีโครงสร้าง** (JSON ที่มี `kind` หรือ exit code แยกตามประเภท) agent จะได้แตกแขนงได้โดยไม่ต้องตีความข้อความ
3. **สถานะที่ไม่รู้ต้องไม่ถูกตีว่าปลอดภัย** ถ้าข้อมูลไม่ครบ ให้ตกไปอยู่ `review`, `unavailable` หรือ `INCONCLUSIVE` ไม่ใช่ `safe` (worktree-audit, ship-pr, resume)
4. **verdict ผูกกับ revision** (SHA หรือ patch-id) ถ้า revision เปลี่ยน verdict ก็ใช้ไม่ได้ ถ้าไม่ผูกไว้ จะมีคนใช้ verdict เก่ากับโค้ดใหม่
5. **ใช้ lint ตรวจไฟล์แผนหรือเอกสารที่ agent สร้าง** อย่าหวังให้ agent จำโครงได้เอง (`check-plan.mjs`)
6. **ส่วนต่อขยายที่อ้างถึงขั้นตอนอื่น ให้ยกข้อความมาตรง ๆ ไม่ใช้เลขขั้นตอน** แล้วใช้ script ตรวจว่าข้อความนั้นยังอยู่ (`check-playbooks.mjs`)
7. **บทเรียนจากการรีวิวต้องมีระดับความเชื่อมั่นกำกับ** (candidate → recurring → strong) และมีหมวดที่ห้ามข้ามโดยอัตโนมัติเสมอ (`bugbot-triage.md`)
8. **prompt ของ subagent ต้องมีส่วน "สิ่งที่ค้นไปแล้ว" และ "ช่องว่าง"** ไม่ใช่แค่สิ่งที่เจอ (`why` investigator)
9. **กำหนดถ้อยคำตามระดับความมั่นใจ** และกำหนดคำที่ห้ามใช้ (`epistemics.md`)
10. **ตัวนำต้องกรองผลของ reviewer** ไม่ใช่แค่รวบรวม และต้องแสดงสิ่งที่ตัดทิ้งพร้อมเหตุผลเพื่อสร้างความไว้ใจ (`lead-judgment.md`)
11. **ให้ runner ในการแข่งขันทำเต็มที่ ไม่ต้องเผื่อคนอื่น** ("Don't hedge against the others") เพราะความต่างคือสัญญาณ
12. **ค่าที่ต้องเหมือนกันหลายที่ ให้มีแหล่งความจริงเดียว** แล้วใช้ generator stamp และ CI ตรวจ
13. **ถ้าดัดแปลงชุดคำสั่งของคนอื่น ให้ประกาศทุก fork** พร้อมเหตุผลและเวอร์ชัน แล้วใช้ 3-way sync
