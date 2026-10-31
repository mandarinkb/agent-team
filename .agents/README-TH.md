# ทีม Agent แบบ Zero Trust: คู่มือฉบับเต็ม

คู่มือนี้อธิบายทีม AI teammate ที่รับงาน **migration**, **เพิ่ม feature** และ **แก้บั๊ก** ตั้งแต่ตกลงทิศทางกับคุณจนถึง commit ที่ทดสอบแล้ว ครอบคลุมว่า workflow ทำงานอย่างไร ใช้หลักการอะไร ติดตั้งอย่างไร และเขียน prompt สั่งงานแต่ละแบบอย่างไร

ศัพท์ที่ใช้ในคู่มือ (Job, Spec, Task, Fix Task, Round, Claim, Verified) นิยามไว้ใน [`GLOSSARY.md`](../GLOSSARY.md)

---

## สารบัญ

1. [ภาพรวม: คุณทำอะไร ทีมทำอะไร](#1-ภาพรวม-คุณทำอะไร-ทีมทำอะไร)
2. [หลักการออกแบบ](#2-หลักการออกแบบ)
3. [โครงสร้างไฟล์](#3-โครงสร้างไฟล์)
4. [บทบาทของ teammate](#4-บทบาทของ-teammate)
5. [Workflow ทีละขั้น](#5-workflow-ทีละขั้น)
6. [สถานะของ Task และใครเปลี่ยนได้](#6-สถานะของ-task-และใครเปลี่ยนได้)
7. [ไฟล์ของแต่ละ Job](#7-ไฟล์ของแต่ละ-job)
8. [กลไกที่บังคับด้วยโค้ด](#8-กลไกที่บังคับด้วยโค้ด)
9. [การตัดสินใจและการส่งต่องาน](#9-การตัดสินใจและการส่งต่องาน)
10. [ติดตั้ง](#10-ติดตั้ง)
11. [วิธีเขียน prompt สั่งงาน](#11-วิธีเขียน-prompt-สั่งงาน)
12. [คำสั่งอ้างอิง](#12-คำสั่งอ้างอิง)
13. [ข้อจำกัดและการแก้ปัญหา](#13-ข้อจำกัดและการแก้ปัญหา)

---

## 1. ภาพรวม: คุณทำอะไร ทีมทำอะไร

```
                    ┌──────────────────────────────────────────┐
                    │  คุณ (User)                               │
                    │  ตอบ grill · อนุมัติ spec · ตัดสินใจ · อ่านผลทดสอบ │
                    └───────────────▲──────────────────────────┘
                 คำถาม/ตัวเลือก/สรุป  │  คำตอบของคุณ (บันทึกคำพูดตรงตัว)
                    ┌───────────────┴──────────────────────────┐
                    │  Lead (session หลักที่คุณคุยด้วย)           │
                    │  grill · เขียน spec และ task · ส่งต่องาน · ไม่เขียนโค้ด │
                    └──┬───────┬────────┬─────────┬────────┬───┘
                       │       │        │         │        │
                  analyst  backend/  spec-reviewer   qa      git
                  สืบสวน   frontend  ตรวจกับ spec   ทดสอบ   stage/commit
                           เขียนโค้ด                Bruno+DB  (ห้าม push)
                 └── teammate เป็น subagent: ทำทีละขั้น รายงาน lead แล้วจบ ──┘
```

**หน้าที่ของคุณมีแค่ 4 อย่าง**

| เมื่อไร | คุณทำอะไร |
|---|---|
| เริ่มงาน | บอกงาน แล้วตอบคำถามตอน grill จนเข้าใจตรงกัน |
| Gate G1 | อ่าน `spec.md` กับรายการ task แล้วพิมพ์อนุมัติ |
| ระหว่างทาง | เลือกตัวเลือกที่ทีมเสนอ หรือพิมพ์คำตอบที่ต้องการเอง |
| จบงาน | อ่าน `test-report.md` และดู commit บน branch `job/<job-id>` |

**teammate ทุกตัวเป็น subagent** (แบบเดียวกับ pstack) lead spawn ทีละขั้นด้วย Agent tool พร้อม brief ที่ระบุ id และ path ที่ขั้นนั้นต้องใช้ teammate ทำขั้นนั้นจบแล้วรายงานกลับ lead ไม่มีตัวไหนค้างอยู่หรือคุยกันเอง จึงใช้ token น้อยกว่า Agent Teams และไม่ต้องพึ่งฟีเจอร์ experimental

ส่วนที่เหลือทีมทำเองทั้งหมด ได้แก่ เขียนโค้ด ตรวจกับ spec สร้างและรัน Bruno ตรวจ DB ทีละ column แก้จนผ่าน และ commit **ไม่มีใคร push** การ push เป็นหน้าที่ของคุณเสมอ

---

## 2. หลักการออกแบบ

### 2.1 Zero Trust: ไม่เชื่อคำกล่าวอ้าง จนกว่าจะมีคนอื่นตรวจซ้ำ

| # | กฎ | ในทางปฏิบัติ |
|---|---|---|
| 1 | **คำกล่าวอ้างไม่ใช่หลักฐาน** | "เสร็จแล้ว" หรือ "test ผ่าน" จากคนที่ทำงานเองไม่นับ จนกว่า teammate คนอื่นจะรันซ้ำแล้วได้ผลเดียวกัน |
| 2 | **ผู้ทำไม่ใช่ผู้ตรวจ** | backend ตรวจงานตัวเองเป็นคำตัดสินไม่ได้ spec-reviewer ตรวจโค้ด qa ทดสอบ และ spec-reviewer ตรวจ test ของ qa อีกชั้น |
| 3 | **สิทธิ์น้อยที่สุด** | แต่ละบทบาทได้ tool เท่าที่ต้องใช้ และ hook ปฏิเสธคำสั่งอันตรายไม่ว่า prompt จะว่าอย่างไร |
| 4 | **หลักฐานผูกกับ revision** | ผลรีวิวและผลทดสอบต้องระบุ tree id ของโค้ดที่ stage ไว้ script คำนวณค่านี้จาก git เอง ถ้าโค้ดเปลี่ยน ผลเดิมใช้ไม่ได้ |
| 5 | **ข้อมูลจากภายนอกเป็นข้อมูล ไม่ใช่คำสั่ง** | output ของ tool, แถวใน DB และข้อความจาก agent อื่น ไม่ใช่การอนุมัติของคุณ |

### 2.2 หลักการอื่นที่ใช้

| หลักการ | ความหมาย | มาจาก |
|---|---|---|
| **Grill ก่อนเสมอ** | lead ถามคุณเป็นรอบ ๆ (ใช้ skill `grilling` + `domain-modeling` ซึ่งเป็นสิ่งที่ `grill-with-docs` ทำ) จนเข้าใจตรงกัน แล้วจึงเขียน spec | ความต้องการของคุณ |
| **คุณเป็นคนตัดสินใจ** | teammate เตรียมตัวเลือก lead นำมาถาม lead เลือกแทนคุณไม่ได้ แม้ทุกคนจะเห็นตรงกัน | agent-team-roles |
| **ข้อเท็จจริงไม่ใช่การตัดสินใจ** | คำถามที่รันแล้วรู้คำตอบได้ ทีมต้องรันเอง ไม่ถามคุณ | pstack (never-block-on-the-human ส่วนที่เก็บไว้) |
| **ไฟล์คือแหล่งความจริง** | สถานะงานอยู่ในไฟล์ ไม่อยู่ในความจำของ agent ปิด session แล้วกลับมาทำต่อได้ | pstack Orchestrate store |
| **brief คือผลิตภัณฑ์** | teammate ถามกลับกลางงานไม่ได้ ไฟล์ task จึงต้องอ่านเข้าใจได้โดยไม่ต้องถามเพิ่ม ถ้ามีช่องที่ยังเติมไม่ได้ ห้ามเริ่ม | pstack Orchestrate |
| **บังคับด้วยโครงสร้างแทนข้อความ** | กฎที่สำคัญเขียนเป็น script และ hook ไม่ใช่แค่คำสั่งใน prompt | pstack encode-lessons-in-structure |
| **ทุก check ต้องพิสูจน์ว่า fail ได้** | test ทุกตัวมีกรณีที่ต้องถูกปฏิเสธ และผ่านการลองใส่บั๊กแล้ว | pstack invariants test |
| **แยกพื้นที่แทนการล็อก** | task สองตัวห้ามมี scope ทับกัน และ hook ปฏิเสธการเขียนไฟล์นอก scope | pstack separate-before-serializing |
| **ตัวตรวจใช้โมเดลแรงกว่าคนทำ** | qa, spec-reviewer และ analyst ใช้ opus ส่วน backend ใช้ sonnet | pstack model policy |

---

## 3. โครงสร้างไฟล์

**`.agents/` คือต้นฉบับ** ส่วน `.claude/` แค่ "import" มาใช้ผ่าน symlink และบรรทัด `@../.agents/AGENTS.md` ใน `.claude/CLAUDE.md`

```
<repo>/
├── GLOSSARY.md                   ศัพท์ของทีม (domain-modeling เขียนเพิ่มระหว่าง grill)
├── .claude/
│   ├── CLAUDE.md                 @../.agents/AGENTS.md
│   ├── agents  -> ../.agents/agents      Claude Code อ่านนิยาม teammate จากที่นี่
│   ├── skills  -> ../.agents/skills      grilling, domain-modeling, grill-with-docs
│   ├── settings.json             hook, deny rule
│   └── statusline.sh             ส่งข้อมูล usage limit ให้ record_limits.py
└── .agents/
    ├── AGENTS.md                 กฎกลางที่ทุกตัวโหลด (สั้นโดยตั้งใจ)
    ├── README-TH.md              คู่มือนี้
    ├── agents/                   นิยาม teammate 6 บทบาท
    ├── workflows/                _run.md (ขั้นตอนร่วม) · bug-fix · feature · migration · retro
    ├── protocols/                zero-trust · tasks · decisions · messaging · database
    ├── templates/                grill-notes · spec · task · fix-task · spec-review · db-check
    │                             · decision-request · decisions · test-report · retro (ภาษาไทย)
    ├── scripts/
    │   ├── job.py                วงจรของ job: grill → spec → G1 → done → retro
    │   ├── task.py               ย้ายสถานะ task พร้อมตรวจสิทธิ์และหลักฐาน
    │   ├── teamlib.py            ส่วนกลาง: git, revision, Bruno, secret, config
    │   ├── redact.py             ลบ secret ออกจากไฟล์หลักฐาน
    │   ├── models.py             สลับโปรไฟล์โมเดลจาก models.json
    │   ├── install.py            ติดตั้งลงโปรเจกต์อื่น
    │   └── hooks/                guard_git · guard_task · guard_sql · loop_guard · limit_guard
    │                             · log_user_prompt · record_limits · probe_identity
    ├── models.json               โมเดลของแต่ละบทบาท (แหล่งเดียว)
    ├── team.json                 (ไม่บังคับ) ค่าตั้งของ gate เช่น Bruno env, limit threshold
    ├── db-mcp.json               (ต่อโปรเจกต์) MCP server ไหนต่อ DB
    ├── tests/test_team.py        test ของ script และ hook ทั้งหมด
    └── work/                     ไฟล์ของแต่ละ job (ไม่ commit)
```

**ทำไมใช้ symlink:** แก้กฎที่ repo นี้ครั้งเดียว ทุกโปรเจกต์ที่ติดตั้งได้ผลด้วย ส่วน `work/`, `GLOSSARY.md`, `team.json` และ `db-mcp.json` เป็นของแต่ละโปรเจกต์

---

## 4. บทบาทของ teammate

| บทบาท | โมเดล (balanced) | เขียนได้ | ห้าม |
|---|---|---|---|
| **lead** (session หลัก) | ตาม session | `grill-notes.md`, `spec.md`, ไฟล์ task, บันทึกการตัดสินใจ | เขียนโค้ด (hook ปฏิเสธการเขียนใน worktree), อนุมัติแทนคุณ |
| **analyst** | opus | `investigation.md`, คำขอตัดสินใจ | แก้ source code |
| **backend** / **frontend** | sonnet | ไฟล์ใน scope ของ task ที่ตัวเองถือเป็น `in_progress` | เขียนใน `bruno/`, ตัดสินงานตัวเอง, `git add`/commit |
| **spec-reviewer** | opus | `reviews/`, `fixes/` | แก้โค้ด, เขียน fix task เมื่อ spec เองผิด (ต้องส่งเป็นการตัดสินใจ) |
| **qa** | opus | `bruno/<job>/`, `evidence/`, `fixes/`, `test-report.md` | แก้ production code, เขียน DB |
| **git** | sonnet | ไม่ได้เลย (ไม่มี Edit/Write) | push, merge, `reset --hard`, `--amend`, `--no-verify` |

ทุกบทบาทใช้ MCP ของ DB ได้ แต่ทำได้แค่ `SELECT` เท่านั้น สลับโปรไฟล์โมเดลได้ด้วย `models.py --profile quality|balanced|economy` (qa ใช้ opus ทุกโปรไฟล์)

---

## 5. Workflow ทีละขั้น

### 5.1 ภาพรวม

```
 [0] job.py new
      │
 [1] GRILL ── lead ถามคุณเป็นรอบ ๆ ── คุณยืนยัน "เข้าใจตรงกัน" ──► job.py grill-done --quote
      │            (bug: qa reproduce + analyst หา root cause)
      │            (migration: analyst ทำ inventory + qa บันทึก baseline)
      ▼
 [2] SPEC + TASKS ── lead เขียน spec.md (AC-1..n, API/Data contract, seed/reset) ── job.py add-task
      │
 [3] GATE G1 ── คุณอ่านแล้วพิมพ์อนุมัติ ──► job.py approve --quote
      │
 [4] RUN (ทำขนานกันได้)
      │   git: worktree + branch job/<id>
      │   qa: เขียน Bruno collection จาก spec  ║  backend/frontend: implement ทีละ task
      │   git: stage + tree id
      │   spec-reviewer: ตรวจโค้ด + Bruno กับ spec ──ไม่ตรง──► fix task ──┐
      │   qa: รัน Bruno + ตรวจ DB ทีละ column ─────ไม่ผ่าน──► fix task ──┤
      │                                                                 ▼
      │                                              implementer แก้ (สูงสุด 3 รอบ)
      ▼
 [5] FINAL TEST ── qa reset + seed ข้อมูล รันทั้งหมดอีกครั้งบน tree สุดท้าย เขียน test-report.md
      │
 [6] COMMIT GATE ── git commit "Job: <id>" ── hook ตรวจทุกอย่าง + รัน Bruno ซ้ำเอง ── ผ่านจึง commit
      │
 [7] REPORT ── lead อ่าน diff กับรายงานเอง แล้วสรุปให้คุณ
      │
 [8] RETRO (ถ้าคุณต้องการ) ── เสนอปรับกฎ คุณอนุมัติทีละข้อ
```

### 5.2 รายละเอียดแต่ละขั้น

**[0] เริ่ม job**: lead รัน `job.py new <bug|feature|migration> "<ชื่อ>" [--api]` ได้ job id รูปแบบ `J-YYYYMMDD-<slug>` และโฟลเดอร์ `.agents/work/<job>/`

**[1] Grill**: lead ใช้ `grilling` ถามคำถามเป็นรอบ แต่ละข้อมีคำตอบที่แนะนำ คำถามที่ตอบได้ด้วยการดูไฟล์หรือรันคำสั่ง lead จะหาเอง ไม่ถามคุณ ส่วน `domain-modeling` บันทึกศัพท์ที่ตกลงกันลง `GLOSSARY.md` ทันที เมื่อไม่มีคำถามเหลือ lead จะถามว่า "เข้าใจตรงกันแล้วใช่ไหม" แล้วนำคำตอบของคุณไปใช้กับ `grill-done --quote` script จะตรวจว่าคำพูดนั้นมีอยู่จริงในสิ่งที่คุณพิมพ์หลังจากเริ่ม job แล้ว

แต่ละประเภทงานมีขั้นตอนก่อนเขียน spec ต่างกัน

| ประเภท | ก่อนเขียน spec | AC ที่ spec ต้องมี |
|---|---|---|
| **bug-fix** | qa reproduce บั๊กบน surface จริง (API ใช้ Bruno) จากนั้น analyst หา root cause ด้วยหลักฐานจากการรันจริง | AC-1 คือ "repro ผ่าน" และมีข้อที่ห้ามเปลี่ยนพฤติกรรม |
| **feature** | analyst สำรวจโค้ดที่ได้รับผลกระทบ ถ้ามีหลายแบบให้ส่งเป็นตัวเลือก | ทุกพฤติกรรมใหม่ + API/Data contract |
| **migration** | analyst ทำ inventory ทั้งหมด (route, caller, side effect, table, column) จากนั้น qa บันทึก baseline จากระบบเก่า **ก่อน** เขียนโค้ดใหม่ | "ตรงกับ baseline ในกรณี X" และทุกส่วนต่างต้องเป็นการตัดสินใจของคุณ |

**[2] Spec และ Task**: `spec.md` มี 8 หัวข้อ ได้แก่ เป้าหมาย, ขอบเขต, AC ที่มีรหัส, API contract, Data contract ระดับ column, seed/reset ของข้อมูลทดสอบ, baseline (เฉพาะ migration) และเรื่องที่รอคุณตัดสิน lead แบ่ง task ด้วย `add-task` โดยระบุ owner, AC, scope และวิธี verify (`bruno`/`db`/`test`) script ไม่ยอมให้ task สองตัวมี scope ซ้ำกัน

**[3] Gate G1**: `job.py approve` จะผ่านก็ต่อเมื่อ spec ไม่มีช่องว่าง, ทุก AC มี task รองรับ, ทุก task ไม่มีช่องว่าง, งาน API มี task ที่ verify ด้วย Bruno และคำอนุมัติของคุณมีอยู่ใน log ถ้ายังไม่ผ่าน G1 จะไม่มี task ไหนเริ่มได้

**[4] Run**: รายละเอียดทั้งหมดอยู่ใน [`workflows/_run.md`](workflows/_run.md)
- **git** สร้าง worktree แยกบน branch `job/<id>`
- **qa** เขียน Bruno collection **จาก spec ไม่ใช่จากโค้ด** ให้เสร็จก่อน review รอบแรก ทุก request ต้องใส่ AC ใน `docs { AC-1 }` ต้อง assert body หรือ header (ไม่ใช่แค่ status) และ secret ต้องมาจาก `{{process.env.X}}`
- **backend/frontend** หยิบ task (`in_progress`) แก้เฉพาะไฟล์ใน scope รัน build/unit test ของตัวเอง แล้ว mark `implemented`
- **git** stage เฉพาะไฟล์ใน scope แล้วรายงาน tree id ให้ lead ซึ่งส่งต่อใน brief ของขั้นถัดไป
- **spec-reviewer** ตรวจทีละ AC พร้อม `file:line` และตรวจ Bruno collection ว่าครอบคลุม AC จริง ถ้าไม่ตรง เขียน `fixes/F-n.md` แล้ว lead spawn implementer ตัวใหม่พร้อม fix task นั้น
- **qa** รัน Bruno (`--reporter-json`), ตรวจ DB ทีละ column ตาม Data contract, รัน `redact.py` แล้ว mark `verified` ถ้าไม่ผ่าน เขียน fix task

**การแก้วน (Round):** fix task หนึ่งครั้งเท่ากับหนึ่งรอบ task หนึ่งตัวแก้ได้ไม่เกิน 3 รอบ รอบที่ 4 ต้องให้คุณตัดสิน ถ้าล้มด้วยสาเหตุเดิม 2 รอบติดกัน ให้หยุดและส่งเป็นการตัดสินใจทันที

**[5] Final test**: เมื่อทุก task verified แล้ว qa reset และ seed ข้อมูลตาม spec แล้วรันทุกอย่างอีกครั้งบน tree สุดท้าย จากนั้นเขียน `test-report.md` ซึ่งต้องมีทุก AC พร้อม PASS/FAIL และหลักฐาน

**[6] Commit gate**: git รัน `git commit -m "..." -m "Job: <id>"` แล้ว hook ตรวจรายการต่อไปนี้ (ดูหัวข้อ 8) ถ้าผ่านครบจะ commit ได้โดยไม่ต้องถามคุณ:
- ทุก task verified
- รายงานเป็น PASS ครบทุก AC และมีบรรทัด Reset
- tree ที่ stage ตรงกับ revision ในรายงาน
- ทุกไฟล์อยู่ใน scope
- ไม่มี secret
- Bruno collection ผ่านการตรวจ และ **hook รัน Bruno ซ้ำเองแล้วผ่าน**

**[7] Report**: lead อ่าน diff และรายงานเอง ไม่ส่งต่อสรุปของ teammate ตรง ๆ แล้วสรุปให้คุณเป็นภาษาไทย

**[8] Retro**: ดูรายละเอียดใน [`workflows/retro.md`](workflows/retro.md) lead ตรวจงานที่จบแล้วผ่าน 3 มุม (judgment, tooling, divergent) แล้วเสนอปรับกฎ คุณอนุมัติทีละข้อ

---

## 6. สถานะของ Task และใครเปลี่ยนได้

```
todo ──► in_progress ──► implemented ──► spec_ok ──► verified ──► committed
  ▲                           │             │  ▲         │
  └──────── fix task ─────────┴─────────────┘  └─ qa: Bruno เปลี่ยน กลับไป review (รอบเดิม)
```

| จาก → ไป | ใครทำได้ | ต้องมีอะไร |
|---|---|---|
| todo → in_progress | owner ของ task | ผ่าน G1 แล้ว มี worktree ถ้าเป็นรอบที่ 4 ขึ้นไปต้องมี `--decision D-n` และต้องใช้ usage limit ไม่ถึง 95% |
| in_progress → implemented | owner | มีไฟล์ใน scope เปลี่ยนจริง |
| implemented → spec_ok | spec-reviewer | review มี Verdict PASS, ครอบคลุมทุก AC, Revision ตรงกับ tree ที่ stage และ task ที่ใช้ Bruno ต้องมี `Bruno coverage: PASS` และ collection ผ่านการตรวจ |
| implemented / spec_ok / verified → todo | spec-reviewer หรือ qa | `--fix fixes/F-n.md` ที่ระบุ task และ AC |
| spec_ok → implemented | qa | `--note` (แก้ Bruno หลัง review แล้ว) |
| spec_ok → verified | qa | ไฟล์ใน scope และใน Bruno ไม่เปลี่ยนตั้งแต่ review, หลักฐานครบตามวิธี verify และไม่มี secret |
| verified → committed | git | `--sha` ของ commit บน branch ของ job ที่ tree ตรงกับรายงาน |

---

## 7. ไฟล์ของแต่ละ Job

```
.agents/work/<job-id>/
├── job.json            สถานะ job (เขียนโดย job.py เท่านั้น)
├── grill-notes.md      คำถาม คำตอบ และทิศทางที่ตกลงกัน
├── investigation.md    งานของ analyst
├── spec.md             spec ที่คุณอนุมัติ
├── tasks/T-01.md       brief ของแต่ละ task
├── state/T-01.json     สถานะ task (เขียนโดย task.py เท่านั้น)
├── reviews/            ผลตรวจของ spec-reviewer
├── fixes/F-1.md        fix task
├── evidence/           ผล Bruno (.json), ตรวจ DB (.md), log test
├── decisions/D-1.md    คำขอให้ตัดสินใจ
├── decisions.md        คำตอบของคุณ พร้อมคำพูดตรงตัว
├── test-report.md      รายงานผลทดสอบ (ไฟล์ที่คุณอ่าน)
├── log.tsv             ประวัติทุกการเปลี่ยนสถานะ (เพิ่มได้อย่างเดียว)
└── retro.md            (ถ้าทำ retro)
```

---

## 8. กลไกที่บังคับด้วยโค้ด

| Hook | ทำงานตอน | ทำอะไร |
|---|---|---|
| `log_user_prompt.py` | คุณพิมพ์ข้อความ | บันทึกสิ่งที่คุณพิมพ์ลง `.user-prompts.jsonl` เพื่อใช้พิสูจน์ว่าคำอนุมัติมาจากคุณจริง ข้าม turn ที่ระบบเริ่มเอง |
| `guard_task.py` | Bash / Write / Edit | ตรวจว่า `--by` ของ `task.py` ตรงกับ agent ที่รันจริง, `job.py` แต่ละคำสั่งรันได้เฉพาะบทบาทที่กำหนด, ห้ามแก้ state/log ด้วยมือ, teammate แก้ gate ไม่ได้ และการเขียนใน worktree ต้องอยู่ใน scope ของ task ที่ถืออยู่ |
| `guard_git.py` | Bash | ห้าม push, force-push, `reset --hard`, `clean -f`, `branch -D`, `--no-verify`, `gh pr create/merge` ทุกรูปแบบ (รวมถึง `bash -c` และ `eval`) และเป็น **commit gate** |
| `guard_sql.py` | MCP tool | DB ทำได้แค่ `SELECT` ทีละคำสั่ง ตรวจตามกฎของ DB หลายชนิด เพราะแต่ละชนิดตีความ quote และ comment ต่างกัน |
| `loop_guard.py` | Bash | ปฏิเสธคำสั่งเดิมครั้งที่ 6 ใน 10 นาที ถ้าไม่มีไฟล์เปลี่ยน |
| `limit_guard.py` | Bash | ห้ามเริ่ม task ใหม่เมื่อ usage limit รอบ 5 ชั่วโมงหรือ 7 วันใช้ถึง 95% |
| `probe_identity.py` | ทุก tool (เมื่อ `TEAM_PROBE=1`) | บันทึกว่า hook ได้รับ `agent_type` จริงไหม ใช้ตอนทดสอบครั้งแรก |

นอกจาก hook แล้ว `settings.json` ยังมี deny rule สำหรับ `git push`, `reset --hard`, `clean -f` และ `gh pr` อีกชั้นหนึ่ง

**limit guard ทำงานอย่างไร:** Claude Code ส่งข้อมูล usage limit ให้เฉพาะ statusline `statusline.sh` จึงส่งข้อมูลต่อให้ `record_limits.py` บันทึกลง `.agents/work/.rate-limits.json` เมื่อถึง 95% (ปรับได้ด้วย `limit_threshold` ใน `team.json`) teammate จะเริ่ม task ใหม่ไม่ได้ แต่ทำขั้นปัจจุบันให้จบและบันทึกสถานะได้ หลัง reset ให้สั่ง "ทำ job ... ต่อ" แล้ว `job.py resume` จะเตือนถ้ามีไฟล์ที่แก้ค้างครึ่งทาง

**เมื่อ hook ปฏิเสธ:** teammate ต้องหยุดและรายงาน `BLOCKED` ให้ lead ห้ามหาทางเลี่ยง ข้อความที่ hook ส่งกลับมาจะบอกเสมอว่าขาดอะไร

---

## 9. การตัดสินใจและการส่งต่องาน

**เรื่องที่ต้องให้คุณตัดสินเสมอ:**
- เลือกระหว่าง design ที่ใช้ได้ทั้งคู่
- เปลี่ยน spec, contract, error shape หรือ data format
- ยอมรับส่วนต่างจาก baseline หรือช่องว่างในการทดสอบ
- ขยายหรือลด scope
- เพิ่ม dependency
- แตะ schema หรือข้อมูลที่ใช้ร่วมกัน
- ทำรอบที่ 4
- push, merge หรือ deploy

**วิธีที่ teammate ส่งเรื่องมา:** teammate เขียน `decisions/D-n.md` จาก template ซึ่งต้องมีตัวเลือกอย่างน้อย 2 ตัว แต่ละตัวมีข้อดี ข้อเสีย ต้นทุน และคำแนะนำ จากนั้น lead ถามคุณ โดยตัวเลือกที่แนะนำอยู่บนสุดและมีป้าย `(แนะนำ)` **คุณเลือกตัวเลือกหรือพิมพ์คำตอบเองก็ได้** แล้ว lead บันทึกด้วย `job.py decide` (ตรวจคำพูดกับ log เหมือนตอนอนุมัติ) และใส่คำพูดของคุณลงใน brief ของ teammate ที่ทำงานต่อ ตรงตัว

**ไม่มีค่าเริ่มต้นและไม่มี timeout:** ถ้าคุณยังไม่ตอบ งานที่รอคำตอบจะหยุด แต่งานอื่นที่ไม่เกี่ยวข้องเดินต่อ

**teammate ไม่คุยกันเอง** ทุกการส่งต่อผ่าน lead และไฟล์ เช่น git รายงาน tree id แล้ว lead spawn spec-reviewer พร้อม tree id นั้น หรือ qa เขียน fix task แล้ว lead spawn backend ตัวใหม่ให้อ่าน fix task ขั้นที่ไม่ขึ้นต่อกันรันขนานกันแบบ background ได้ ความเห็นที่ตรงกันของ teammate ไม่นับเป็นการตัดสินใจ รายละเอียดอยู่ใน [`protocols/messaging.md`](protocols/messaging.md)

---

## 10. ติดตั้ง

### 10.1 สิ่งที่ต้องมี

| สิ่งที่ต้องมี | ใช้ทำอะไร |
|---|---|
| Claude Code | รันทีมด้วย subagent (ไม่ต้องเปิด Agent Teams) |
| Python 3.9+ และ git | script และ hook ทั้งหมด (ใช้แค่ standard library) |
| `jq` | statusline |
| Bruno CLI | `npm i -g @usebruno/cli` |
| MCP server ของ DB ทดสอบ | qa ตรวจข้อมูลทีละ column |
| แพ็กเกจ Pro/Max (ไม่บังคับ) | limit guard ใช้ข้อมูล `rate_limits` ซึ่งไม่มีถ้าใช้ API key |

### 10.2 ติดตั้งลงโปรเจกต์

```bash
python3 /path/to/agent-team/.agents/scripts/install.py /path/to/your-project
```

`install.py` ทำสิ่งต่อไปนี้
1. symlink `AGENTS.md`, `README-TH.md`, `agents/`, `protocols/`, `scripts/`, `skills/`, `templates/` และ `workflows/` ไปไว้ที่ `<project>/.agents/`
2. สร้าง `<project>/.claude/agents` และ `.claude/skills` เป็น symlink ไปที่ `../.agents/...`
3. เพิ่มบรรทัด `@../.agents/AGENTS.md` ลงใน `<project>/.claude/CLAUDE.md`
4. สร้าง `.claude/settings.json` ถ้ายังไม่มี ถ้ามีอยู่แล้วจะพิมพ์ส่วนที่ต้องนำไปรวมเอง (ไม่แก้ทับไฟล์ของคุณ)
5. สร้าง `.agents/work/.gitignore`
6. พิมพ์บรรทัดที่ต้องเพิ่มใน statusline เพื่อเปิดใช้ limit guard

### 10.3 ตั้งค่าครั้งแรก

1. **CLAUDE.md:** ใส่คำสั่ง build, test, run, URL ของ service ตอนรัน local และโครงโฟลเดอร์ไว้เหนือบรรทัด `@../.agents/AGENTS.md` teammate ทุกตัวอ่านไฟล์นี้ ถ้าข้อมูลชัด จะประหยัด token และรายงาน BLOCKED น้อยลง
2. **DB:** ต่อ MCP server กับ **DB ทดสอบ** ด้วย user ที่มีสิทธิ์ SELECT อย่างเดียว แล้วสร้าง `.agents/db-mcp.json`
   ```json
   {"servers": ["postgres"], "sql_fields": ["sql", "query", "statement"]}
   ```
   (`postgres` คือชื่อ server ตามที่ปรากฏใน `mcp__<server>__<tool>`)
3. **`.agents/team.json`** (ไม่บังคับ ถ้าค่าเริ่มต้นใช้ได้ก็ไม่ต้องสร้าง)
   ```json
   {"bruno_env": "local", "commit_rerun_bruno": true,
    "bruno_command": ["bru", "run", "--env", "{env}", "--reporter-json", "{out}"],
    "bruno_timeout": 300, "limit_threshold": 95}
   ```
   flag ของ `bru` มาจากความรู้ของผู้เขียน ยังไม่ได้ลองรันจริง ถ้าเวอร์ชันของคุณใช้ flag ต่างไป ให้แก้ `bruno_command`
4. **statusline:** เพิ่มบรรทัดนี้ต่อจาก `input=$(cat)`
   ```bash
   echo "$input" | python3 "${CLAUDE_PROJECT_DIR:-.}/.agents/scripts/hooks/record_limits.py" 2>/dev/null
   ```

### 10.4 ทดสอบครั้งแรก (ทำก่อนใช้งานจริง)

gate ที่ตรวจบทบาทอาศัยค่า `agent_type` ที่ Claude Code ส่งให้ hook ซึ่งยังไม่ได้ยืนยันว่า subagent ส่งค่านี้มา

1. เปิด Claude Code ด้วย `TEAM_PROBE=1 claude` ที่ root ของโปรเจกต์
2. พิมพ์: `spawn subagent backend, qa, git (ไม่ต้องตั้งชื่อ) ให้แต่ละตัวรัน git status หนึ่งครั้งแล้วจบ`
3. รัน `python3 .agents/scripts/hooks/probe_identity.py --report`
4. ถ้าได้ **PASS** ใช้งานได้ ถ้าได้ **FAIL** gate จะปฏิเสธขั้นตอนของ teammate ทั้งหมด อย่าตั้ง `TEAM_IDENTITY=lenient` ถ้ายังไม่ได้ตัดสินใจรับความเสี่ยงนั้น

ตรวจตัวชุดเครื่องมือเองได้ด้วย `python3 .agents/tests/test_team.py`

---

## 11. วิธีเขียน prompt สั่งงาน

### 11.1 หลักการเขียน

prompt แรกไม่ต้องสมบูรณ์ เพราะ lead จะ grill ถามส่วนที่ขาดเอง แต่ยิ่งให้ข้อมูลต่อไปนี้ตั้งแต่ต้น grill ก็ยิ่งสั้นลง

| ใส่อะไร | ตัวอย่าง |
|---|---|
| **ประเภทงาน** | "เริ่ม job feature" / "bug" / "migration" |
| **เป้าหมายที่สังเกตได้** | "API คืนรายการที่กรองแล้ว" ดีกว่า "ปรับปรุงการกรอง" |
| **ขอบเขต** และ **สิ่งที่ห้ามแตะ** | "แก้เฉพาะ internal/orders ห้ามแตะ auth" |
| **ที่ทดสอบ** | URL ตอนรัน local, ชื่อ DB ทดสอบ, บัญชีทดสอบ |
| **ข้อมูลที่ต้องถูกเขียน** | table และ column ที่ต้องตรวจ |
| **ทีม** | `สร้างทีม: ... (ใช้ agent type ตามชื่อ)` เพื่อให้ hook รู้บทบาทของ teammate แต่ละตัว |

**สิ่งที่ prompt ข้ามไม่ได้:** คำว่า "ทำเลยไม่ต้องถาม" ไม่ได้ข้าม grill, G1 หรือ commit gate เพราะ gate เหล่านี้บังคับด้วยโค้ด ถ้าคุณต้องการให้ grill สั้น ให้ตอบว่า "ทุกข้อตามที่แนะนำ" แทน

### 11.2 เพิ่ม feature

```text
เริ่ม job feature (API): ให้ GET /orders กรองตามสถานะได้หลายค่า เช่น ?status[]=paid&status[]=shipped
- ขอบเขต: internal/orders/** และ cmd/api/routes.go ห้ามแตะ auth และ payment
- ถ้าไม่ส่ง status ให้คืนทุกสถานะเหมือนเดิม
- ค่า status ที่ไม่รู้จักให้ตอบ 422 พร้อม error shape เดิมของระบบ
- ทดสอบที่ http://localhost:8081 DB ทดสอบ orders_test
สร้างทีม: analyst, backend, spec-reviewer, qa, git (ใช้ agent type ตามชื่อ)
```

ถ้างานมีหน้าจอด้วย ให้เพิ่ม `frontend` ในทีม และบอกหน้าที่ต้องเปลี่ยน เช่น "หน้า /orders มี filter แบบเลือกได้หลายค่า"

### 11.3 แก้บั๊ก

```text
เริ่ม job bug (API): หน้า /orders แสดงรายการว่าง เมื่อผู้ใช้มีคำสั่งซื้อเกิน 100 รายการ
- เจอบน staging ตั้งแต่ deploy เมื่อวาน ผู้ใช้ทดสอบ user_id 1001 มี 150 orders
- reproduce ได้ที่ GET http://localhost:8081/orders?user_id=1001
- ต้องไม่เปลี่ยนพฤติกรรมของผู้ใช้ที่มีไม่เกิน 100 รายการ และไม่เปลี่ยน pagination format
สร้างทีม: qa, analyst, backend, spec-reviewer, git (ใช้ agent type ตามชื่อ)
```

ถ้ายังไม่รู้สาเหตุและอยากให้หลายสมมติฐานแข่งกัน ให้เพิ่มบรรทัดนี้

```text
ใช้ analyst 2 คน (ชื่อ analyst-a, analyst-b ใช้ agent type analyst) ตั้งสมมติฐานคนละข้อแล้วพยายามหักล้างกันด้วยการรันจริง
```

### 11.4 Migration (เช่น PHP → Go)

```text
เริ่ม job migration (API): ย้าย endpoint POST /orders จาก PHP (app/Http/Controllers/Api/OrderController.php)
ไป Go (internal/orders/)
- ระบบเก่า: http://localhost:8080  ระบบใหม่: http://localhost:8081  ใช้ DB ทดสอบตัวเดียวกัน orders_test
- พฤติกรรมเก่าคือ spec ทุกส่วนต่างต้องถามผมก่อน แม้แบบใหม่จะดูดีกว่า
- ห้ามแก้โค้ด PHP ห้ามลบอะไรของระบบเก่า (การปลดระบบเก่าเป็น job แยก)
- ตรวจ table orders และ order_items ทุก column ที่ endpoint เขียน
สร้างทีม: analyst, qa ก่อน แล้วเพิ่ม backend, spec-reviewer, git หลังผ่าน G1 (ใช้ agent type ตามชื่อ)
```

**การย้ายหลาย endpoint:** ให้ทำทีละ job (endpoint ละหนึ่ง job) โดยเริ่มจาก endpoint ที่อ่านอย่างเดียวและเสี่ยงต่ำเป็น pilot การมีหนึ่ง job ต่อหนึ่ง branch ต่อหนึ่ง commit ทำให้รีวิวและย้อนกลับได้ง่าย

### 11.5 ระหว่าง grill

lead จะถามเป็นรอบ แต่ละข้อมีคำแนะนำมาด้วย คุณตอบได้หลายแบบ

```text
ทุกข้อตามที่แนะนำ
```
```text
Q1 ตามแนะนำ, Q2 เอาแบบ ข, Q3 ไม่ต้องรองรับ status ว่าง
```

เมื่อ lead ถามว่าเข้าใจตรงกันหรือยัง ให้ตอบเป็นประโยคชัด ๆ เพราะ lead จะนำคำพูดนี้ไปใช้กับ `grill-done`

```text
เข้าใจตรงกันแล้ว เขียน spec ได้เลย
```

### 11.6 อนุมัติ spec (G1)

อ่าน `.agents/work/<job>/spec.md` และไฟล์ใน `tasks/` ก่อน ถ้าต้องการแก้ ให้บอกตรง ๆ เช่น `AC-3 ให้ตอบ 400 แทน 422` ถ้าพร้อมแล้ว ให้พิมพ์

```text
อนุมัติ spec และ task ทั้งหมด เริ่ม implement ได้
```

### 11.7 ตอบคำขอให้ตัดสินใจ

```text
เลือกทางเลือก A
```
```text
ไม่เอาทั้งสองแบบ ให้คืน [] แทน null แต่เฉพาะ endpoint นี้
```

### 11.8 กลับมาทำต่อ / ทบทวน / อื่น ๆ

| สถานการณ์ | พิมพ์ |
|---|---|
| ปิด session ไปแล้ว หรือ limit reset แล้ว | `ทำ job J-20261017-orders-filter ต่อ` |
| ดูสถานะ | `สถานะ job J-20261017-orders-filter เป็นอย่างไร` |
| จบงานแล้วอยากให้ทีมเรียนรู้ | `ทำ retro ของ job J-20261017-orders-filter` แล้วอนุมัติทีละข้อ เช่น `อนุมัติ R-1 และ R-3` |
| ลดค่าใช้จ่าย | `สลับโปรไฟล์โมเดลเป็น economy` (เป็นการเปลี่ยนกฎ lead จะยืนยันกับคุณก่อน) |

---

## 12. คำสั่งอ้างอิง

`S` = `python3 .agents/scripts`

| คำสั่ง | ใคร |
|---|---|
| `S/job.py new <bug\|feature\|migration> "<title>" [--api]` | lead |
| `S/job.py grill-done <job> --quote "<คำพูดผู้ใช้>"` | lead |
| `S/job.py add-task <job> --owner backend --title "..." --ac AC-1 --scope "src/**" --verify bruno,db` | lead |
| `S/job.py approve <job> --quote "<คำพูดผู้ใช้>"` | lead |
| `S/job.py decide <job> D-1 --quote "<คำพูดผู้ใช้>"` | lead |
| `S/job.py set-worktree <job> --path <dir> --branch job/<job>` | git |
| `S/job.py status <job>` / `S/job.py resume <job>` | ทุกคน |
| `S/job.py done <job>` | git |
| `S/job.py retro <job>` / `S/job.py retro-approve <job> R-1 --quote "..."` | lead |
| `S/task.py list <job>` | ทุกคน |
| `S/task.py set <job> T-01 <state> --by <role> [...]` | ตามตารางหัวข้อ 6 |
| `S/redact.py <files>` | qa |
| `S/models.py [--profile X] [--check]` | lead (หลังคุณอนุมัติ) |
| `S/install.py <project>` | คุณ |
| `python3 .agents/scripts/hooks/probe_identity.py --report` | คุณ |
| `python3 .agents/tests/test_team.py` | ทุกคน |

---

## 13. ข้อจำกัดและการแก้ปัญหา

**ข้อจำกัดที่รู้อยู่**
- **ยังไม่ได้ทดสอบกับ subagent จริง** ให้ทำการทดสอบในหัวข้อ 10.4 ก่อน
- **lead เป็นตัวกลางทุกการส่งต่อ** context ของ lead จึงโตตามจำนวนขั้น brief และรายงานควรอ้าง path แทนการแปะเนื้อหา
- **การกรองข้อความใน log ผู้ใช้:** `UserPromptSubmit` ทำงานทั้งตอนคุณพิมพ์และตอนระบบเริ่ม turn เอง hook ข้าม turn ของระบบตามรูปแบบ tag ที่ผู้เขียนอนุมานเอา ยังไม่ได้วัดจริง
- **shell writes:** agent ที่ตั้งใจเลี่ยงยังเขียนไฟล์ผ่าน shell บางรูปแบบได้ แต่ commit gate ตรวจหลักฐานใหม่จาก git และไฟล์ทั้งหมด การปลอมสถานะอย่างเดียวจึงไม่พอให้ commit ผ่าน
- **Bruno ตอน commit** ทดสอบ service ที่ env ชี้ไป ตอน commit service ต้องรันโค้ดชุดสุดท้ายอยู่ gate พิสูจน์ข้อนี้ไม่ได้
- **ตรวจ secret ด้วยรูปแบบ (pattern)** secret ที่หน้าตาแปลกไปจากรูปแบบที่รู้จักอาจหลุดได้
- **limit guard:** ข้อมูลอาจช้ากว่าความจริงไม่กี่นาที และไม่ทำงานถ้าใช้ API key
- **ต้นทุน:** แต่ละขั้นเป็น subagent ที่จบแล้วหายไป ไม่มีตัวที่ค้างอยู่ แต่บทบาทที่ใช้ opus ยังใช้ token มาก ดูได้จาก `/usage`

**เมื่อเจอข้อความปฏิเสธ**

| ข้อความ | ความหมาย / ต้องทำอะไร |
|---|---|
| `REFUSED: ... placeholders` | ไฟล์ยังมีช่อง `<fill` ที่ยังไม่ได้กรอก |
| `that quote is not in anything the user typed` | คำพูดที่ lead อ้าง ไม่ตรงกับที่คุณพิมพ์ ให้พิมพ์อนุมัติใหม่เป็นประโยคชัด ๆ |
| `the user has not approved the spec (gate G1)` | ยังไม่ได้อนุมัติ spec |
| `round 4 exceeds the budget` | แก้ครบ 3 รอบแล้ว ทีมจะส่งเรื่องมาให้คุณตัดสิน |
| `files the spec review vouched for changed` | โค้ดหรือ Bruno เปลี่ยนหลัง review ต้อง review ใหม่ |
| `Bruno collection: ... asserts only the status` | qa ต้องเพิ่ม assertion ของ body หรือ header |
| `looks like a secret` | ให้ qa รัน `redact.py` หรือย้ายค่าไปไว้ใน `.env` |
| `outside your scope` | teammate พยายามแก้ไฟล์นอก task ที่ถืออยู่ |
| `only the git teammate commits` / `task.py --by X but this agent is Y` | บทบาทไม่ตรง ถ้าเกิดกับ teammate ทุกตัว ให้กลับไปทำการทดสอบในหัวข้อ 10.4 |
| `Usage limit guard` | limit ใช้ถึง 95% แล้ว รอให้ reset แล้วสั่ง "ทำ job ... ต่อ" |
| `Loop guard` | teammate รันคำสั่งเดิมซ้ำโดยไม่มีอะไรคืบหน้า lead จะเปลี่ยนเป็น teammate ตัวใหม่หรือถามคุณ |
| `database access is SELECT only` | มีการพยายามเขียน DB ผ่าน MCP ซึ่งไม่อนุญาต |
