# Agent Teams ของ Claude Code เทียบกับ pstack

[← กลับไปหน้ารวม](README.md)

> **ที่มา:**
> - เอกสาร Claude Code [Agent teams](https://code.claude.com/docs/en/agent-teams), [Subagents](https://code.claude.com/docs/en/sub-agents) และ [Manage costs](https://code.claude.com/docs/en/costs) อ่านเมื่อ 2026-10-09
> - ฝั่ง pstack อ่านจากไฟล์ในโปรเจกต์นี้ เวอร์ชัน `0.9.64`
>
> **ระดับหลักฐาน:**
> - ตัวเลขที่เอกสาร Anthropic ระบุไว้ มีอยู่ข้อเดียวคือ **"approximately 7x more tokens than standard sessions when teammates run in plan mode"**
> - ตัวเลขฝั่ง pstack **มาจากการนับจำนวน agent ตามคำสั่งใน skill ไม่ได้วัดจากการรันจริง**
> - การเปรียบเทียบ token ในหัวข้อ 5 เป็น **การประเมินเชิงเหตุผล (ตีความ)** ไม่ใช่ผลการวัด ถ้าจะตัดสินใจเรื่องงบ ให้วัดตามวิธีในหัวข้อ 8
>
> **หมายเหตุ:** Agent teams ยังเป็นฟีเจอร์ experimental รายละเอียดอาจเปลี่ยนตามเวอร์ชันของ Claude Code

---

## สารบัญ

1. [สรุปสั้น](#1-สรุปสั้น)
2. [แต่ละแบบคืออะไร](#2-แต่ละแบบคืออะไร)
3. [เทียบสถาปัตยกรรมทีละด้าน](#3-เทียบสถาปัตยกรรมทีละด้าน)
4. [ข้อดีและข้อเสีย](#4-ข้อดีและข้อเสีย)
5. [แบบไหนกิน token มากกว่ากัน](#5-แบบไหนกิน-token-มากกว่ากัน)
6. [ใช้ร่วมกันได้ไหม และต้องระวังอะไร](#6-ใช้ร่วมกันได้ไหม-และต้องระวังอะไร)
7. [เลือกแบบไหนสำหรับงานแบบไหน](#7-เลือกแบบไหนสำหรับงานแบบไหน)
8. [วิธีวัด token ด้วยตัวเอง](#8-วิธีวัด-token-ด้วยตัวเอง)
9. [แหล่งอ้างอิง](#9-แหล่งอ้างอิง)

---

## 1. สรุปสั้น

| | Agent Teams | pstack |
|---|---|---|
| **คืออะไร** | ฟีเจอร์ของ Claude Code ที่ให้หลาย session ทำงานเป็นทีม คุยกันเองได้ | ชุด skill และ playbook ที่บอก session หลักให้ใช้ subagent อย่างมีระเบียบ |
| **ใครคุมงาน** | lead แจกงาน แต่ teammate หยิบงานและประสานกันเองได้ | ตัวนำคุมทุกอย่าง และ subagent ส่งผลกลับให้ตัวนำเท่านั้น |
| **จุดแข็ง** | การถกเถียง หักล้างสมมติฐาน และงานคู่ขนานที่ต้องคุยกัน | ความถูกต้องที่ตรวจได้ หลักฐาน และ workflow ที่ทำซ้ำได้ |
| **จุดอ่อน** | resume ไม่ได้ task status อาจไม่อัปเดตทันที และยัง experimental | ขั้นตอนเยอะ จำนวน agent ต่องานสูง และผูกกับ GitHub |
| **ต่อ agent หนึ่งตัว** | **แพงกว่า** เพราะ teammate คือ session เต็มตัวที่อยู่นานและรับข้อความได้ | ถูกกว่า เพราะ subagent ทำงานครั้งเดียวแล้วส่งสรุปกลับ |
| **ต่องานหนึ่งงาน** | ขึ้นกับขนาดทีมและเวลาที่ปล่อยให้ทำงาน (เอกสารแนะนำ 3-5 คน) | อาจสูงกว่า เพราะ Feature หนึ่งงานใช้ประมาณ 10-25 agent ตามที่นับจากคำสั่ง |

**คำตอบเรื่อง token แบบสั้น (ตีความ)**
- **ถ้าเทียบต่อ agent หนึ่งตัว Agent Teams กิน token มากกว่า** teammate เป็น Claude Code ครบทั้ง session อยู่จนกว่าจะถูกปิด และทุกข้อความที่ได้รับคือการเรียกโมเดลอีกรอบพร้อม context ทั้งหมด
- **ถ้าเทียบต่องานหนึ่งงาน ยังสรุปไม่ได้** pstack ใช้ agent จำนวนมากกว่า และค่าเริ่มต้นใช้โมเดลแรง (`fable`, `opus`) ส่วน Agent Teams ใช้ agent น้อยกว่าแต่อยู่นานกว่า
- **งานรีวิวแบบส่งรอบเดียว** เช่น `interrogate` ที่ใช้ reviewer 3 ตัว **pstack น่าจะถูกกว่า** ทีม 3 คนที่ถกกันหลายรอบ
- **งาน Feature เต็มรูปแบบ** pstack มีโอกาสแพงกว่า ถ้าใช้ค่าเริ่มต้นทั้งหมด

---

## 2. แต่ละแบบคืออะไร

### 2.1 Agent Teams
- **เปิดใช้:** ตั้ง `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` ใน env หรือ `settings.json` ถ้าไม่ตั้ง จะไม่มีทีมเกิดขึ้น
- **ต้องเป็น interactive session** โหมด `-p` และ Agent SDK จะไม่ spawn teammate
- **องค์ประกอบ**

| ส่วน | หน้าที่ | เก็บที่ |
|---|---|---|
| Team lead | session หลัก spawn teammate, แจกงาน และรวมผล | (session ปัจจุบัน) |
| Teammates | Claude Code แยก instance แต่ละตัวมี context ของตัวเอง | `~/.claude/teams/{team}/config.json` |
| Task list | งานที่ใช้ร่วมกัน มีสถานะ pending, in progress และ completed และกำหนดได้ว่างานไหนรองานไหน | `~/.claude/tasks/{team}/` |
| Mailbox | ข้อความระหว่าง agent | `~/.claude/teams/{team}/inboxes/{agent}.json` |

- **การหยิบงาน:** lead สั่งตรง หรือ teammate หยิบงานถัดไปที่ยังว่างและไม่ถูก block เอง โดยใช้ **file locking** กันการหยิบชนกัน
- **Hook สำหรับคุมคุณภาพ:** `TeammateIdle`, `TaskCreated` และ `TaskCompleted` ถ้าจบด้วย exit 2 จะส่ง feedback กลับและบล็อกการกระทำนั้น
- **การแสดงผล:** แบบ in-process (ค่าเริ่มต้น ใช้ได้ทุก terminal) หรือ split pane (ต้องมี tmux หรือ iTerm2 + `it2`) ตั้งได้ด้วย `teammateMode` หรือ `--teammate-mode`

### 2.2 pstack
- **ติดตั้ง:** เป็น plugin ใช้ hook `SessionStart` ใส่คำสั่งให้เรียก `poteto-mode` เมื่องานแตะมากกว่าหนึ่งไฟล์ หรือเป็นงานออกแบบ หรือเป็นบั๊กที่ไม่รู้สาเหตุ
- **โครงสร้าง:** router (`poteto-mode`) → playbook 23 ตัว → skill ที่ส่งงานให้ subagent หลายตัว (`how`, `why`, `arena`, `swarm`, `interrogate`, `reflect`) → principle 24 ตัว → script ที่บังคับกฎด้วยโค้ด
- **กลไกที่ใช้:** `Agent` tool ธรรมดาของ Claude Code (subagent) ไม่ได้ใช้ Agent Teams
- **state ระยะยาว:** สำหรับงานใหญ่ใช้ store ของ `orch` ใน `~/.claude/orchestrate/<slug>/` (units, ledger, inbox, frontier)

---

## 3. เทียบสถาปัตยกรรมทีละด้าน

| ด้าน | Agent Teams | pstack |
|---|---|---|
| **หน่วยทำงาน** | teammate คือ session เต็มตัว อยู่จนถูกปิด | subagent ทำงานครั้งเดียวแล้วส่งผล ค่าเริ่มต้นคือ "Fresh subagents by default" |
| **การสื่อสาร** | teammate คุยกันเองได้ และผู้ใช้คุยกับ teammate ตรงได้ | ผ่านตัวนำเท่านั้น ("Keep sibling communication upward only" ใน Orchestrate) |
| **การแจกงาน** | task list ร่วมที่หยิบเองได้ และ dependency ปลดล็อกอัตโนมัติ | ตัวนำเขียน brief ให้ทีละงาน แบบ "The brief is the product" |
| **การตรวจผล** | ขึ้นกับ prompt และ hook `TaskCompleted` ที่คุณเขียนเอง | มีในตัว คือผู้ตรวจต้องไม่ใช่ผู้ทำ ใช้โมเดลต่างตระกูล verdict ผูกกับ SHA และ inconclusive ไม่นับว่าผ่าน |
| **ความหลากหลายของมุมมอง** | ได้จากบทบาทใน spawn prompt และการถกกัน | ได้จากหลายโมเดล (`interrogate`, `arena`) หรือมุมที่ prompt กำหนด (`reflect`) |
| **การเลือกโมเดล** | ตาม prompt → นิยาม subagent → `CLAUDE_CODE_SUBAGENT_MODEL` → **โมเดลของ lead** | แต่ละบทบาทมีค่าเริ่มต้นใน `models.json` เช่น bug-fix ใช้ `fable` และ panel ใช้ opus, fable และ sonnet |
| **การแยกไฟล์** | เอกสารแนะนำให้แต่ละ teammate เป็นเจ้าของไฟล์คนละชุด แต่ **ไม่ได้บังคับ** | writer ทุกตัวต้องมี worktree ของตัวเอง (`isolation: "worktree"`) |
| **การซ้อนกัน** | **ไม่มีทีมซ้อน** และ teammate สร้าง teammate ไม่ได้ | subagent ซ้อนได้ 3 ชั้น (ตามข้อจำกัดของ Claude Code) |
| **งาน background** | **teammate รัน subagent แบบ background ไม่ได้** | ทุก subagent ใช้ `run_in_background: true` |
| **Permission** | teammate ได้ mode ของ lead และ prompt ขออนุญาตขึ้นที่ lead | ใช้ permission ของ session ปกติ |
| **Plan approval** | lead **อนุมัติแผนของ teammate ให้อัตโนมัติ** โดยผู้ใช้ไม่ได้ดู | Phase C ของ `architect` ไม่หยุดรอผู้ใช้ ยกเว้นผู้ใช้ขอ |
| **การ resume** | **resume teammate ไม่ได้** ต้อง spawn ใหม่ | มี Pause safely และ Session pickup ที่ใช้ `resume.mjs` และ checkpoint |
| **การกู้คืนเมื่อพัง** | ผู้ใช้หรือ lead ต้องสังเกตเองว่า teammate หยุดกลางทาง | มีกฎ retry ตามประเภทความผิดพลาด, การจัดการ agent ที่ค้าง และ stop line |
| **บันทึกการตัดสินใจ** | ไม่มีในตัว (มี transcript ของแต่ละ teammate) | `show-me-your-work` บันทึก TSV และรีวิวด้วยอีกโมเดล |
| **ความพร้อม** | experimental | ยังเป็น 0.9.x มีทั้ง test และ CI แต่ขึ้นกับต้นฉบับจาก Cursor |

### กลไกที่คล้ายกัน
pstack สร้างหลายอย่างที่ Agent Teams มีในตัวขึ้นมาเอง

| Agent Teams (ในตัว) | pstack (สร้างเอง) |
|---|---|
| task list ที่กำหนด dependency ได้ | `units.tsv` + `frontier.json` |
| mailbox เป็นไฟล์ JSON ต่อ agent | `inbox/` หนึ่ง event หนึ่งไฟล์ แล้ว drain ด้วยการ rename โฟลเดอร์ |
| file locking ตอนหยิบงาน | `.orch.lock` ที่เก็บ PID และตรวจได้ว่าเจ้าของตายแล้ว |
| hook `TaskCompleted` ที่บล็อกได้ | ledger กับ verdict 5 ระดับ ที่ผูกกับ SHA |
| idle notification ที่แนบคำตอบสุดท้าย | "Completions are queue events, not interrupts" |

ความต่างหลักคือ **Agent Teams ให้กลไกการประสานงาน แต่ไม่ได้กำหนดว่างานต้องมีคุณภาพแค่ไหน ส่วน pstack กำหนดคุณภาพละเอียด แต่ต้องสร้างกลไกประสานงานเอง**

---

## 4. ข้อดีและข้อเสีย

### 4.1 Agent Teams

**ข้อดี**
1. **teammate คุยกันได้จริง** เหมาะกับงานที่ต้องหักล้างกัน เอกสารยกตัวอย่าง debug ด้วย teammate 5 คนที่ "try to disprove each other's theories, like a scientific debate" เพื่อแก้ปัญหาที่การสืบทีละทางมักยึดติดกับทฤษฎีแรก
2. **ใช้ได้ทันทีโดยไม่ต้องติดตั้งอะไร** แค่ตั้ง env var แล้วสั่งเป็นภาษาธรรมดา
3. **ผู้ใช้คุยกับ teammate ได้ตรง** เลือกจาก agent panel ส่งคำสั่งเพิ่ม หรือหยุด teammate ที่ทำงานผิดทาง
4. **task list และ dependency มีในตัว** มี file locking และปลดล็อกงานที่รออยู่ให้อัตโนมัติ
5. **มี hook ให้คุมคุณภาพ** (`TaskCompleted` และ `TeammateIdle`)
6. **ใช้ subagent definition เดิมเป็น teammate ได้** เช่น ไฟล์ใน `.claude/agents/`
7. **ข้อความระหว่าง agent ปลอดภัย** teammate อนุมัติ permission แทนผู้ใช้ไม่ได้ และ auto mode ตรวจข้อความระหว่าง agent ด้วย

**ข้อเสีย**
1. **กิน token มาก** แต่ละ teammate เป็น instance แยก เอกสารบอกว่า "approximately 7x" ของ session ปกติเมื่อ teammate อยู่ใน plan mode
2. **ยัง experimental:** resume ไม่ได้, task status อาจไม่อัปเดต, shutdown ช้า และอาจมี tmux session ค้าง
3. **ไม่มีมาตรฐานคุณภาพในตัว** จะตรวจผลอย่างไรขึ้นกับ prompt และ hook ที่คุณเขียน
4. **lead อนุมัติแผนให้อัตโนมัติ** จึงไม่มีคนดูแผนก่อน teammate เริ่มทำ
5. **ข้อจำกัดเชิงโครงสร้าง:** มีได้ทีมเดียว, ไม่มีทีมซ้อน, teammate รัน background subagent ไม่ได้, เปลี่ยน lead ไม่ได้ และตั้ง permission ต่อ teammate ตอน spawn ไม่ได้
6. **ทีมอาจเกิดขึ้นโดยไม่ได้ตั้งใจ** เมื่อเปิดฟีเจอร์แล้ว subagent ที่ Claude ตั้งชื่อเองจะกลายเป็น teammate ทำให้ค่าใช้จ่ายสูงขึ้นโดยไม่รู้ตัว
7. **การแยกไฟล์เป็นแค่คำแนะนำ** เอกสารเตือนว่า "Two teammates editing the same file leads to overwrites"
8. **ต้องคอยดู:** "Letting a team run unattended for too long increases the risk of wasted effort" และ lead อาจลงมือทำเองแทนที่จะรอ teammate

### 4.2 pstack

**ข้อดี**
1. **มาตรฐานคุณภาพละเอียด** ต้อง reproduce ก่อนแก้, ตรวจบน surface จริง, inconclusive ไม่นับว่าผ่าน และทุกข้ออ้างติดป้าย วัดมา / อนุมาน / เดา
2. **ตรวจด้วยโมเดลต่างตระกูล** ทั้ง `interrogate`, cross-judge ของ `arena` และ verifier ใน Orchestrate
3. **มี workflow สำหรับงานแต่ละประเภท** 23 playbook ที่บันทึกการข้ามขั้นตอนไว้ได้ (`skip: <reason>`)
4. **กฎสำคัญบังคับด้วยโค้ด** ได้แก่ `check-plan`, `watch-pr`, `orch` ledger, `--match-head-commit` และ test ที่ตรึงกฎ
5. **ทำงานยาวและกู้คืนได้** มี checkpoint, Session pickup, store นอก session และกฎ retry
6. **บันทึกการตัดสินใจ** decision log ที่ตรวจกับ transcript ได้
7. **ระบบเรียนรู้จากตัวเอง** ด้วย `reflect` ที่มีเกณฑ์คัดกรองและให้คนอนุมัติทีละแถว
8. **ใช้ได้หลาย runtime** ทั้ง Claude Code, Codex และ Pi

**ข้อเสีย**
1. **จำนวน agent ต่องานสูง** Feature ใช้ประมาณ 10-25, Bug fix ประมาณ 5-20 และ Multi-phase plan อย่างน้อย 14 ต่อ PR ต่อรอบ (นับจากคำสั่ง)
2. **subagent `poteto-agent` ทุกตัวต้องอ่าน `poteto-mode/SKILL.md` (25.6 KB) ก่อนเริ่ม**
3. **ค่าเริ่มต้นใช้โมเดลแพง** bug-fix, perf และ hillclimb ใช้ `fable` ส่วน panel ใช้ 3 โมเดล
4. **subagent คุยกันไม่ได้** ทุกอย่างต้องผ่านตัวนำ ทำให้การถกเถียงแบบเรียลไทม์ทำได้ยากกว่า
5. **ขั้นตอนเยอะเกินงานเล็ก** และ hook ส่งงานที่แตะแค่ 2 ไฟล์เข้า flow เต็ม
6. **ผูกกับเครื่องมือ** ทั้ง GitHub, bun และ Graphite (สำหรับ Orchestrate)
7. **กฎส่วนใหญ่ยังเป็นข้อความ** และ model อาจไม่ทำตามครบ
8. **ความเห็นเฉพาะตัว** เช่น ห้าม shim และลบ comment หนัก (ดู [ข้อจำกัดของ pstack](PSTACK-LIMITATIONS-TH.md))

---

## 5. แบบไหนกิน token มากกว่ากัน

### 5.1 ต้นทุนมาจากอะไร
token ที่ใช้รวมโดยประมาณ **(ตีความ)**

```
ต้นทุนรวม ≈ Σ (สำหรับทุก agent) [ context เริ่มต้น + (จำนวน turn × context ที่ส่งในแต่ละ turn) ] × ราคาของโมเดลที่ใช้
```

ปัจจัยสำคัญมี 5 ข้อ

| ปัจจัย | Agent Teams | pstack | แบบไหนเสียเปรียบ |
|---|---|---|---|
| **1. จำนวน agent** | น้อย เอกสารแนะนำ 3-5 คน | มาก ประมาณ 10-25 ต่อ Feature | pstack |
| **2. อายุของ agent** | ยาว อยู่จนกว่าจะถูกปิด ("Each active teammate continues consuming tokens until it exits") | สั้น ทำงานครั้งเดียวแล้วจบ | Agent Teams |
| **3. จำนวน turn ต่อ agent** | มาก เพราะทุกข้อความจาก lead หรือ teammate อื่นปลุก teammate ให้ทำ turn ใหม่ | น้อย ส่วนใหญ่เป็นงานเดียวจบ | Agent Teams |
| **4. context เริ่มต้น** | session เต็ม คือ CLAUDE.md, MCP, skills และ spawn prompt | subagent ได้ system prompt, CLAUDE.md, git status และ brief ส่วน `poteto-agent` ต้องอ่าน 25.6 KB เพิ่ม | พอ ๆ กัน (pstack หนักกว่าถ้าเป็น poteto-agent) |
| **5. โมเดลที่ใช้** | ค่าเริ่มต้นคือ **โมเดลของ lead** ถ้า lead ใช้ Opus หรือ Fable teammate ทุกตัวก็ใช้ด้วย | ตาม `models.json` เช่น bug-fix ใช้ `fable` และ panel มี `fable` อยู่ด้วย | ขึ้นกับการตั้งค่า |

**ปัจจัยเรื่อง prompt cache**
- teammate แบบ in-process ใช้ cache TTL **5 นาที** เป็นค่าเริ่มต้น ปรับเป็น 1 ชั่วโมงได้ด้วย `subagentPromptCacheTtl` แต่ cache write แบบ 1 ชั่วโมงแพงกว่า ถ้า teammate ว่างเกิน 5 นาทีแล้วได้ข้อความใหม่ จะต้องประมวลผล context ทั้งหมดใหม่ **(ตีความ)**
- **fork** ใช้ cache ของ parent ซ้ำได้ เอกสารบอกว่า "a fork costs less than a fresh subagent for tasks that need the same context"
- pstack เลือก **subagent ตัวใหม่เป็นค่าเริ่มต้น** เพื่อให้ context สะอาดและคำสั่งไม่ตกหล่น **จึงยอมเสีย cache reuse ที่ fork จะได้** เป็นการแลก token กับความถูกต้อง **(ตีความ)**

### 5.2 ตัวเลขจากเอกสาร Anthropic
- **"Agent teams use approximately 7x more tokens than standard sessions when teammates run in plan mode"** (หน้า Manage costs) ตัวเลขนี้ใช้กับกรณีที่ teammate อยู่ใน plan mode
- "Token usage is roughly proportional to team size"
- ค่าเฉลี่ยของ Claude Code ทั่วไป: "around $13 per developer per active day and $150-250 per developer per month" ตัวเลขนี้เป็นการใช้งานทั่วไป ไม่ใช่ของ Agent Teams หรือ pstack โดยเฉพาะ
- **ไม่มีตัวเลขทางการของ pstack** และ pstack ไม่มี telemetry

### 5.3 ประเมินตามสถานการณ์ (ตีความ ไม่ได้วัด)

| สถานการณ์ | Agent Teams | pstack | น่าจะแพงกว่า | เหตุผล |
|---|---|---|---|---|
| **รีวิว PR 3 มุม** | teammate 3 คน + lead อาจถกกันหลายรอบ | `interrogate` ส่ง reviewer 3 ตัว รอบเดียว แล้วตัวนำสรุป | **Agent Teams** | จำนวน agent เท่ากัน แต่ teammate อยู่นานกว่าและมีข้อความไปมา |
| **debug ด้วยสมมติฐานหลายข้อ** | teammate 3-5 คนถกและหักล้างกัน | Bug fix: `how` + `why` (สูงสุด 8) + delegate + verify | **ไม่แน่นอน** | pstack ใช้ agent มากกว่า แต่ทีมถกกันหลายรอบ |
| **Feature ข้าม frontend, backend และ test** | teammate 3 คน คนละ layer | Feature: `how` + `architect` (`arena` 4) + delegate (`arena` อีก 4) + `interrogate` 3 + `no-comments` | **pstack** (ถ้าใช้ค่าเริ่มต้น) | 10-25 agent และใช้โมเดลแรง |
| **refactor หลาย module ขนานกัน** | 4 teammate ใช้ Sonnet (ตัวอย่างในเอกสาร) | Refactoring: delegate + equivalence check | **ใกล้เคียงกัน** | ขึ้นกับว่า pstack ใช้ `arena` หรือไม่ |
| **งานยาวข้ามคืน** | ไม่เหมาะ เพราะ resume ไม่ได้และต้องคอยดู | Autonomous run + checkpoint | **Agent Teams** ถ้า teammate ค้างไว้นาน | teammate ที่ยังไม่ถูกปิดใช้ token ต่อเมื่อมีข้อความ |
| **migration 100+ หน่วย** | ใช้ไม่ได้เต็มที่ เพราะมีทีมเดียวและไม่มีทีมซ้อน | Orchestrate ใช้ rolling window ประมาณ 10 worker | **pstack** (ในแง่ token รวม) | แต่เป็นงานที่ Agent Teams ทำไม่ได้อยู่แล้ว |
| **แก้บั๊กเล็ก 1 ไฟล์** | ไม่ควรใช้ทีม | hook ไม่ส่งเข้า flow | **เท่ากัน** ถ้าทั้งสองแบบไม่ถูกเรียกใช้ | |

### 5.4 สรุปเรื่อง token
1. **ต่อ agent หนึ่งตัว Agent Teams แพงกว่า** เพราะอยู่นาน มีหลาย turn และ cache หมดอายุใน 5 นาที
2. **ต่องานหนึ่งงาน pstack ที่ใช้ค่าเริ่มต้นมีโอกาสแพงกว่าในงานใหญ่** เพราะใช้ agent มากกว่าและโมเดลแรงกว่า
3. **ทั้งสองแบบลดต้นทุนได้มาก** ถ้าตั้งโมเดลให้เหมาะกับงาน (ดูหัวข้อ 5.5)
4. **ตัวแปรที่ควบคุมได้มากที่สุดคือโมเดล** ไม่ใช่สถาปัตยกรรม การใช้ Sonnet แทน Opus หรือ Fable มีผลต่อค่าใช้จ่ายมากกว่าการเลือกระหว่างสองแบบนี้ **(ตีความ)**

### 5.5 วิธีลดต้นทุน
**Agent Teams (จากเอกสาร)**
- ใช้ Sonnet กับ teammate (เอกสารแนะนำเอง) โดยระบุใน spawn prompt หรือใน `model:` ของ subagent definition
- ทีมเล็ก 3-5 คน และ "Three focused teammates often outperform five scattered ones"
- spawn prompt สั้นและตรงประเด็น
- **ปิด teammate ทันทีเมื่อเสร็จ** ("Ask the X teammate to shut down")
- ใช้กับงานที่เป็นอิสระต่อกันจริงเท่านั้น
- เปิดฟีเจอร์เฉพาะ session ที่ต้องการ เพื่อไม่ให้ subagent ที่ถูกตั้งชื่อกลายเป็น teammate โดยไม่ตั้งใจ

**pstack (ข้อเสนอ)**
- `/pstack:setup-pstack` ลด panel จาก 3 เป็น 2 และตั้ง `bug-fix` กับ `strongest judgment` เป็น `opus` แทน `fable`
- ตั้ง `default effort` ให้ต่ำลง แล้วเพิ่มเฉพาะบทบาทที่ต้องใช้วิจารณญาณ
- ปิด hook แล้วเรียก poteto-mode เองเฉพาะงานใหญ่
- เรียก skill เดี่ยว (`how`, `tdd`, `blast-radius`) แทน playbook เต็มเมื่อพอ

---

## 6. ใช้ร่วมกันได้ไหม และต้องระวังอะไร

### 6.1 การทำงานร่วมกันที่ควรรู้ (จากเอกสาร)
- **subagent ที่มีชื่อจะกลายเป็น teammate:** "a subagent that Claude spawns from the main conversation with a `name` launches as a teammate instead, unless the call is a fork or passes `isolation` on the call itself"
  - **ผลกับ pstack (ตีความ):** delegate ที่เขียนไฟล์ใน Feature ถูกสั่งให้ใช้ `isolation: "worktree"` จึง **ไม่น่าจะกลายเป็น teammate** แต่ reviewer ของ `how`, `why` และ `interrogate` ไม่ได้ส่ง `isolation` ถ้า Claude ตั้งชื่อให้ ตัวเหล่านี้อาจกลายเป็น teammate
- **teammate รัน background subagent ไม่ได้:** "an in-process teammate's own subagents run in the foreground" และ `run_in_background: true` จะ error หรือรันแบบ foreground
  - **ผลกับ pstack:** ถ้า teammate ตัวหนึ่งเรียก poteto-mode การ fan-out ของ pstack จะกลายเป็นทำทีละตัว ช้าลง และอาจทำงานไม่ตรงกับที่ playbook คาดไว้
- **ไม่มีทีมซ้อน:** teammate สร้าง teammate ไม่ได้ แต่ยังสร้าง subagent ได้
- **teammate โหลด CLAUDE.md และ skill ของโปรเจกต์** จึงเห็นกฎของ pstack ด้วย และอาจถูก hook ส่งเข้า poteto-mode เมื่อได้งานหลายไฟล์ ทำให้ token เพิ่มเป็นสองชั้น **(ตีความ)**
- **ช่อง `skills` ใน subagent definition ไม่ถูกนำมาใช้กับ teammate**

### 6.2 รูปแบบที่ใช้ร่วมกันได้ดี (ข้อเสนอ)
| รูปแบบ | วิธี |
|---|---|
| **A. ใช้ pstack เป็นตัวหลัก ปิด Agent Teams** | ค่าเริ่มต้นที่ปลอดภัยที่สุด ใช้กับงานแก้โค้ดทั่วไป |
| **B. ใช้ Agent Teams สำหรับการถกเถียง และ pstack สำหรับการลงมือ** | เปิดทีมเฉพาะ session ที่ต้อง debug หรือ review แบบถกกัน (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude`) แล้วนำข้อสรุปไปใช้กับ playbook ของ pstack ใน session ปกติ |
| **C. นำหลักการของ pstack ไปใส่ในทีม** | ใช้ไฟล์ใน `agent-team-roles/` ของโปรเจกต์นี้ (backend, frontend, qa และ git ทุกบทบาทใช้ `sonnet`) ซึ่งนำกฎของ pstack มาใช้แล้ว เช่น แยกไฟล์ต่อ teammate, ผู้ตรวจไม่ใช่ผู้เขียน, `PASS` / `ISSUES` / `BLOCKED` และป้าย measured / inferred / guess |
| **D. ใช้ hook ของ Agent Teams แทนกลไกตรวจของ pstack** | ตั้ง `TaskCompleted` ให้รัน script ตรวจ เช่น `parity.py check` ใน [starter kit](starter-kit-php-to-go/README.md) แล้ว exit 2 ถ้าไม่ผ่าน เพื่อบังคับว่างานจะ "completed" ได้ก็ต่อเมื่อผ่านการตรวจจริง |

รูปแบบ D น่าสนใจที่สุดในเชิงออกแบบ เพราะ **นำหลักการของ pstack ที่ว่า "กฎสำคัญต้องบังคับด้วยโค้ด" มาใช้กับกลไกในตัวของ Agent Teams** **(ข้อเสนอ ยังไม่ได้ทดสอบ)**

---

## 7. เลือกแบบไหนสำหรับงานแบบไหน

| งาน | แนะนำ | เหตุผล |
|---|---|---|
| debug บั๊กที่สาเหตุไม่ชัดและมีหลายสมมติฐาน | **Agent Teams** (3-5 คน ใช้ Sonnet) | การถกเถียงช่วยลดการยึดติดกับทฤษฎีแรก ซึ่งเป็นกรณีที่เอกสารยกตัวอย่าง |
| รีวิว PR หลายมุม ต้องการผลเร็วและถูก | **pstack `interrogate`** | รอบเดียวจบ ใช้หลายโมเดล และมีการคัดกรองผลของตัวนำ |
| รีวิว PR ที่อยากให้ reviewer ถกกันเอง | **Agent Teams** | teammate คุยกันได้ |
| research หรือสำรวจ library หรือแนวทาง | **Agent Teams** หรือ **pstack `how` / `swarm`** | ทีมเหมาะกับการแลกเปลี่ยน ส่วน `swarm` เหมาะกับการแบ่งงานให้ครอบคลุม |
| Feature ข้าม layer ที่แยกไฟล์ได้ชัด | **ทั้งสองแบบ** ทีมเร็วกว่า ส่วน pstack ตรวจละเอียดกว่า | ถ้าความถูกต้องสำคัญ ให้ใช้ pstack |
| แก้บั๊กใน production ที่ต้องมีหลักฐาน | **pstack Bug fix** | บังคับ reproduce, ใช้หลักฐาน และ commit repro ก่อน fix |
| refactor หรือ migration ที่ต้องรักษาพฤติกรรมเดิม | **pstack Refactoring + project playbook** | ตรึงพฤติกรรมก่อน และตรวจ equivalence |
| งานยาวข้ามคืนหรือหลายวัน | **pstack** (Autonomous run หรือ Orchestrate) | Agent Teams resume ไม่ได้และต้องคอยดู |
| งานที่ไฟล์ทับกันมากหรือต้องทำตามลำดับ | **session เดียวหรือ subagent** | เอกสารของ Agent Teams เองก็บอกว่าไม่เหมาะ |
| งานเล็กทั่วไป | **ไม่ใช้ทั้งสองแบบ** | ต้นทุนไม่คุ้ม |

---

## 8. วิธีวัด token ด้วยตัวเอง

ทุกตัวเลขในหัวข้อ 5.3 เป็นการประเมิน ถ้าจะตัดสินใจจริงควรวัด **(ข้อเสนอ)**

1. **เลือกงานจริง 1 งานที่ทำได้ทั้งสองแบบ** เช่น debug บั๊กที่รู้คำตอบแล้ว หรือรีวิว PR ที่ merge ไปแล้ว ใช้งานเดียวกันทั้งสองรอบ
2. **ตั้งโมเดลให้เท่ากัน** เช่น Sonnet ทั้งสองแบบ เพื่อแยกผลของสถาปัตยกรรมออกจากผลของโมเดล
3. **รันแต่ละแบบใน session ใหม่** แล้วดู `/usage` ซึ่งเอกสารบอกว่า Session block แสดง token และค่าใช้จ่ายโดยประมาณ ส่วนแผน Pro, Max, Team และ Enterprise มี **Attribution** แยกตาม skill, subagent และ plugin
   - **ข้อควรระวัง:** บรรทัด `Prompt cache (main)` ครอบคลุมเฉพาะ conversation หลัก ไม่รวม subagent
4. **ถ้าต้องการตัวเลขต่อผู้ใช้หรือส่งเข้าระบบ monitoring** ให้ใช้ OpenTelemetry export
5. **บันทึกผลด้วย decision log** (`show-me-your-work`) คอลัมน์ evidence เป็นภาพหรือข้อความจาก `/usage` และ result เป็นจำนวน token กับผลของงาน (ถูกหรือผิด, เวลาที่ใช้)
6. **วัดคุณภาพคู่กับต้นทุนเสมอ** แบบที่ถูกกว่าแต่หาสาเหตุผิดไม่ได้ประหยัดจริง ตามหลัก `explain-the-number` ของ pstack ให้รันอย่างน้อย 2-3 รอบต่อแบบ เพราะผลจาก model มีความแปรปรวน

---

## 9. แหล่งอ้างอิง

**เอกสาร Claude Code**
- [Orchestrate teams of Claude Code sessions (Agent teams)](https://code.claude.com/docs/en/agent-teams)
- [Subagents](https://code.claude.com/docs/en/sub-agents)
- [Manage costs effectively](https://code.claude.com/docs/en/costs) (หัวข้อ Agent team token costs และ Manage agent team costs)

**ไฟล์ในโปรเจกต์นี้**
- `plugins/pstack/skills/poteto-mode/SKILL.md` (ส่วน Subagents, Autonomy และ Models)
- `plugins/pstack/models.json`
- `plugins/pstack/skills/poteto-mode/playbooks/feature.md`, `bug-fix.md` และ `orchestrate.md`
- `agent-team-roles/README-TH.md` และ `agent-team-roles/AGENTS.md` (ชุดบทบาท teammate ที่นำหลักการของ pstack มาใช้)

**เอกสารที่เกี่ยวข้องในชุดนี้**
- [หลักการออกแบบ Workflow Agent](PSTACK-WORKFLOW-DESIGN-TH.md) หัวข้อ 8 (สัญญาการมอบหมายงาน)
- [Design Patterns](PSTACK-DESIGN-PATTERNS-TH.md) หัวข้อ 4 (store) และ 5 (subagent runtime)
- [ข้อจำกัดของ pstack](PSTACK-LIMITATIONS-TH.md) หัวข้อ 2 (ต้นทุน)
