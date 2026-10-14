# การออกแบบ Agent Team ของ pstack และวิธีนำหลักการไปใช้กับงานของคุณ

> **ที่มาและขอบเขต:** สรุปจากการอ่านไฟล์จริงในโปรเจกต์นี้ ได้แก่ `poteto-mode/SKILL.md` (ส่วน Subagents, Autonomy, Principles, Models), `models.json`, `agents/`, `effort-agents/`, `hooks/`, `CONTEXT.md`, playbook Bug fix, Feature, Refactoring, Babysit, Orchestrate, Autopilot-full, Multi-phase plan และสกิล `swarm`, `arena`, `architect`, `interrogate`, `how`
> **ส่วนที่ยังไม่ได้อ่านเต็ม:** ท้ายของ Orchestrate และ Autopilot-full, playbook Autopilot-stack, Shipping, Eval, สคริปต์ `orch` และ `watch-pr`, และโค้ดส่วน Pi
> **การยืนยัน:** ยังไม่ได้รันระบบจริง ทุกอย่างมาจากการอ่านคำสั่ง ส่วนที่เป็นการตีความหรือข้อเสนอของผู้เขียนจะระบุว่า "ตีความ" หรือ "ข้อเสนอ"

---

## 1. ภาพรวม: pstack ออกแบบ "ทีม agent" อย่างไร

pstack ไม่มีโค้ดที่ควบคุม agent ทีมของมันคือ **ไฟล์ Markdown ที่เป็นคำสั่ง** ให้ Claude อ่านแล้วทำตาม และใช้เครื่องมือ `Agent` ของ Claude Code เป็นกลไกเดียวในการสร้างลูกทีม ความเป็นระบบเกิดจากการออกแบบ 6 อย่างต่อไปนี้

| # | แนวคิดการออกแบบ | ทำที่ไหน |
|---|---|---|
| 1 | มี **ผู้นำเพียงคนเดียว** ที่เป็นเจ้าของงานและรับผิดชอบผลลัพธ์ | `poteto-mode` และหัวของทุก playbook ("You own...") |
| 2 | ลูกทีมถูก **มอบหมายด้วยสัญญา (brief) ที่ครบในตัวเอง** | ส่วน Subagents และหัวข้อ "The brief" ใน Orchestrate |
| 3 | **เลือกโมเดลต่อบทบาท** ไม่ใช่โมเดลเดียวทั้งทีม | `models.json` และไฟล์ override `pstack-models.md` |
| 4 | ใช้ **ความหลากหลายของโมเดล** เป็นตัวสร้างการตรวจสอบ | `arena`, `architect`, `interrogate` (panel 3 โมเดล) |
| 5 | **แยกผู้เขียนออกจากกัน** (worktree หรือ branch ต่อคน) แทนการล็อก | principle `separate-before-serializing-shared-state` |
| 6 | **ผู้ตรวจต้องไม่ใช่ผู้ทำ** และต้องมีหลักฐานจากของจริง | `swarm`, Autopilot-full, `prove-it-works` |

---

## 2. สถาปัตยกรรม 4 ชั้น

```
ชั้น 0  Hook ตอนเริ่ม session
          └─ ฉีดข้อความ: "งานแตะหลายไฟล์/ออกแบบ/บั๊กไม่รู้สาเหตุ → เรียก poteto-mode"
ชั้น 1  poteto-mode  (ผู้นำ/ผู้จัดการ)
          └─ เลือก playbook → เปิด todolist คัดขั้นตอนมาตรง ๆ → สั่งงาน → รีวิว → สรุป
ชั้น 2  Playbook + สกิลเชิงกระบวนการ
          └─ Bug fix, Feature, Refactoring, Babysit, Orchestrate, Autopilot...
          └─ how, why, architect, arena, swarm, interrogate
ชั้น 3  Subagent (ลูกทีม ทำงานเบื้องหลัง)
          └─ poteto-agent, effort-<level>, general-purpose, comment-sicko
ชั้น 4  Principles (หลักคิดที่ถูกเรียกอ่านเมื่อเข้าเงื่อนไข)
          └─ principle-* ประมาณ 20 ตัว
```

### ชั้น 0: Hook
`hooks/hooks.json` ผูกกับ event `SessionStart` (ตอน startup, resume, clear, compact) แล้วรัน `session-start.sh` ซึ่งพิมพ์ไฟล์ `session-start-context.md` เข้า context จุดที่น่าสนใจ

- ใช้เกณฑ์ **เชิงโครงสร้างที่วัดได้** ว่าเมื่อไรต้องเรียกระบบ ("แตะมากกว่าหนึ่งไฟล์", "เปลี่ยน signature ที่ไฟล์อื่นเรียก") ไม่ใช่ "งานใหญ่"
- งานเล็ก (ไฟล์เดียว มี test ชัด) ถูกยกเว้นให้ทำตรง ๆ เพื่อไม่ให้ระบบหนักเกินงาน
- ผู้ใช้ปิดได้ด้วยบรรทัด `session hook: off` ในไฟล์ `pstack-models.md`
- ฉีดซ้ำหลัง `compact` ด้วย เพื่อให้กฎไม่หายเมื่อ context ถูกสรุปย่อ (ตีความ)

### ชั้น 1: ผู้นำ (`poteto-mode`)
คือ **ผู้จัดการที่ไม่ลงมือเขียนโค้ดเอง** กฎหลักที่บังคับ

- "You own the task. Plan, review, verify." มอบการสืบสวนและการแก้ให้ลูกทีม แต่ตัวเองอยู่ในตำแหน่งนำ
- เปิด todolist โดยคัดขั้นตอนของ playbook มาแบบ **verbatim** ขั้นที่ไม่ทำต้องเขียน `skip: <เหตุผล>` กำกับ (ทำให้การข้ามขั้นตรวจสอบได้ ไม่หายไปเงียบ ๆ)
- **ต้องตั้งชื่อรูปร่างข้อมูลก่อนเขียนโค้ด**
- ต้องบอกว่าหลักการข้อไหนเปลี่ยนการตัดสินใจอะไร และอ้างเฉพาะหลักการที่ได้อ่านไฟล์จริงใน session นั้น (กันการอ้างลอย ๆ)
- รายงานต้องสั้น ทุกข้ออ้างมีป้ายว่า **วัดมา / อนุมาน / เดา** และห้ามแต่งลิงก์

### ชั้น 2: Playbook
Playbook คือ **ขั้นตอนที่แข็งตัวแล้วของงานแต่ละแบบ** (ดูหัวข้อ 6) ส่วนสกิลเชิงกระบวนการ (`arena`, `swarm` ฯลฯ) คือรูปแบบการ fan out ที่ playbook หยิบไปใช้ (ดูหัวข้อ 5)

### ชั้น 3: Subagent
ลูกทีมมี 4 ชนิดที่เห็นในไฟล์

| ชนิด | ใช้ทำอะไร |
|---|---|
| `pstack:poteto-agent` | ลูกทีมสำหรับงานใน playbook ทุกขั้น (เขียนโค้ด ช่วยงาน) ไฟล์นิยามสั้นมาก: บังคับให้ **อ่าน `poteto-mode/SKILL.md` ทั้งไฟล์ก่อนเริ่ม** เพื่อไม่ให้ลูกทีมมี "สไตล์" ต่างจากผู้นำ |
| `pstack:effort-<level>` และ `poteto-agent-<level>` | เหมือนข้างบนแต่ตั้ง reasoning effort (low ถึง max) ไฟล์เหล่านี้ตั้งแค่ `effort` ส่วนโมเดลผู้เรียกเป็นคนส่ง |
| `general-purpose` | ใช้ในสกิลที่ต้องการผู้ตรวจอิสระ (`how`, `interrogate`, `swarm`) |
| `comment-sicko` | ตัวอย่าง subagent ที่มี **บุคลิกและขอบเขตแคบ**: หาและลบ comment เท่านั้น ห้ามแตะโค้ดแอป รายงานแล้วจบ |

### ชั้น 4: Principles
ประมาณ 20 สกิลสั้น ๆ แต่ละอัน **มีเงื่อนไขกำกับว่าเมื่อไรต้องเรียกใช้** (เช่น "ใช้เมื่อมี actor หลายตัวอาจเขียน state เดียวกัน") ผู้นำและลูกทีมอ่านเฉพาะอันที่เข้าเงื่อนไข ไม่โหลดทั้งหมด (ตัวอย่างของการประหยัด context)

---

## 3. สัญญาการมอบหมายงาน (Delegation Contract)

หัวใจของการออกแบบทีมนี้คือ **วิธีมอบหมายงานให้ลูกทีม** ซึ่งอยู่ในส่วน Subagents ของ `poteto-mode`

### 3.1 ค่าเริ่มต้นของทุกการเรียก `Agent`
- `run_in_background: true` ให้ทำงานเบื้องหลัง ผู้นำไม่ต้องรอ
- ให้ **เครื่องมือครบ** (ห้ามเลือกชนิด subagent ที่ตัด MCP ออก)
- ส่ง **ตัวชี้ไฟล์ ไม่ยัดเนื้อหา** (ประหยัด context และไม่ให้ข้อมูลเพี้ยนระหว่างทาง)
- ระบุ **โมเดลชัดเจนต่อบทบาท**

### 3.2 จัดระดับงานตามความยาก
| ความยาก | ส่งให้ |
|---|---|
| ยากที่สุด (ออกแบบข้ามระบบ, concurrency ซับซ้อน, อัลกอริทึมละเอียด) | โมเดล "strongest judgment" ไม่ว่าจะเป็นงานที่ความต้องการคลุมเครือ หรือเป็นลำดับขั้นที่ต้องทำตามตัวอักษร |
| ปานกลาง | โมเดลเริ่มต้นของ role นั้น |
| งานเชิงกลไกเล็ก ๆ | โมเดลเร็วและถูก |

### 3.3 ผู้นำเป็นเจ้าของผลงานของลูกทีมเสมอ
- "Review the diff and write your own summary, don't pass through what it said." ต้องดู diff เองและเขียนสรุปเอง
- "A second opinion is the same prompt against a different model. Agreement is high-signal." ความเห็นที่สองคือโจทย์เดียวกันส่งให้โมเดลอื่น และความเห็นตรงกันคือสัญญาณที่แรง

### 3.4 ลูกทีมสดใหม่เป็นค่าเริ่มต้น (Fresh subagents)
งานใหม่ไม่ว่าจะเป็นรอบแก้ งานต่อเนื่อง หรือ retry ให้ spawn ลูกทีมใหม่ที่ได้ **scope รวม** คือ brief เดิม คำสั่งที่เพิ่มมาทุกข้อ รายงานและ branch ของตัวก่อนหน้า เหตุผลที่ระบุไว้: การปลุกลูกทีมเดิมต่อเนื่องแบบขัดจังหวะ "silently drops directives" (คำสั่งหล่นหายเงียบ ๆ)

ใช้ตัวเดิมต่อได้เมื่อ **งานใหม่ต้องการสถานะที่อยู่ในตัวมันและย้ายยาก** เท่านั้น เช่น checkout ในเครื่อง การแก้ที่ยังไม่ commit หรือ process ที่ยังรัน (dev server, simulator, babysit watcher)

บทบาท เช่น "เจ้าของ PR" อยู่เกินอายุของ agent ตัวหนึ่ง เมื่อตัวนั้นกลับมา ตัวใหม่รับบทบาทต่อ

### 3.5 หยุดตัวเก่าก่อนเสมอ และยืนยันว่าหยุดจริง
ในรายการ agent สถานะ `completed` หมายความว่า "ได้รับแจ้งว่าเสร็จ" ไม่ได้แปลว่า process จบ agent ที่ยังมี background child อาจรายงานเสร็จแล้วกลับมาทำงานต่อ มีแค่การสั่งหยุดอย่างชัดเจนที่ทำให้มันจบ สัญญาณที่บอกว่ายังวิ่งอยู่คือสิ่งที่มันอ้างเกี่ยวกับ working tree ขัดกับ `git status`

### 3.6 ข้อสรุปเชิงออกแบบ
ลูกทีมถูกมองเป็น **ฟังก์ชันที่ไม่มีสถานะ** (stateless worker) รับ input ครบ คืน output หนึ่งก้อน การจัดการสถานะอยู่ที่ผู้นำและไฟล์ ไม่ใช่ในความจำของลูกทีม

---

## 4. การเลือกโมเดลและ effort ต่อบทบาท (Model Policy)

### 4.1 โครงสร้างใน `models.json`
```
tiers:    default = opus, strongest = fable, panel = [opus, fable, sonnet]
efforts:  low, medium, high, xhigh, max   (ค่าเริ่มต้น = ตาม session)
roles:    ผูก role กับ tier เช่น
            feature, refactoring        → default
            bug-fix, perf-issue, hillclimb → strongest
            how explorer/explainer, why investigators/synthesizer → default
            arena runners, arena cross-judge pool,
            architect runners, interrogate reviewers → panel
            swarm workers               → default
```

### 4.2 ตรรกะการเลือก (ตีความ)
- **งานที่ต้องวินิจฉัย** (แก้บั๊ก, perf, hillclimb) ใช้โมเดลที่เก่งที่สุด เพราะราคาของการวินิจฉัยผิดสูงกว่าค่าโมเดล
- **งานที่ต้องการความหลากหลาย** (ออกแบบ, รีวิว) ใช้ panel คือหลายโมเดลต่างตระกูล
- **งานปริมาณมากที่ขนานกัน** (swarm) ใช้โมเดลกลาง

### 4.3 ผู้ใช้ปรับได้โดยไม่แก้โค้ด
ไฟล์ `pstack-models.md` (เขียนโดย `/setup-pstack`) override ได้ต่อ role เช่น

```text
arena runners: opus @xhigh, fable @max
swarm workers: inherit-parent
default effort: high
session hook: off
```

- `@level` ตั้ง reasoning effort ต่อ role
- `inherit-parent` หรือ `auto` คือไม่ส่ง `model` ให้ใช้โมเดลของ session
- ถ้า `Agent` ปฏิเสธชื่อโมเดล ให้ถอยไปใช้ค่าเริ่มต้นของตระกูลเดียวกันและ **แจ้งผู้ใช้** แทนที่จะหยุด

### 4.4 จุดออกแบบที่น่าเรียนรู้: แหล่งความจริงเดียว
ค่าเริ่มต้นของโมเดลอยู่ที่ `models.json` ที่เดียว แล้ว `tools/generate.mjs` **ประทับค่าลงในทุกสกิล** (ส่วน "Models") CI รัน `--check` และล้มทันทีถ้ามีสำเนาไหนไม่ตรง ตาม `CONTEXT.md` ทั้ง "Panel", manifest version และ prompt stub ใช้กลไกเดียวกัน

---

## 5. รูปแบบการ fan out ของทีม (Team Topologies)

pstack มีรูปแบบทีมที่ต่างกัน 5 แบบ แต่ละแบบแก้ปัญหาต่างกัน

### 5.1 `how` : ผู้สำรวจ (explorer) → ผู้อธิบาย (explainer)
- ถามง่าย: ผู้อธิบายตัวเดียวสำรวจและอธิบายในรอบเดียว
- ถามซับซ้อน: แตกคำถามเป็น 2 ถึง 4 มุม ส่ง explorer แบบ **read-only** ขนาน แล้วส่งผลให้ synthesizer รวมเป็นคำอธิบายเดียว
- "When in doubt, take the simple path." ค่าเริ่มต้นคือทางเรียบง่าย
- **บทเรียน:** แยกขั้น "เก็บข้อมูล" ออกจาก "สร้างความเข้าใจ" และใช้ read-only กับผู้สำรวจ

### 5.2 `swarm` : ฝูง worker ขนาน
สี่ระยะ: Frame → Fan out → Aggregate → Report

- เลือกรูปทรงได้ 3 แบบ: **แบ่งชิ้น** (partition), **แข่งโจทย์เดียวกัน** (race), หรือผสม สำหรับ race ต้องประกาศก่อน spawn ว่าใช้ `first pass`, `rank all` หรือ `best-of`
- N คือจำนวน worker ทั้งหมด ไม่ใช่จำนวนที่รันพร้อมกัน
- **ทุก brief ต้องอยู่ได้ด้วยตัวเอง:** เป้าหมาย ขอบเขต ชิ้นหรือคู่แข่งที่รับผิดชอบ วิธีตรวจ สิ่งที่ต้องรายงาน
- worker ที่เขียนไฟล์ต้องมี output ของตัวเอง ถ้าตรวจ commit ต้องระบุ SHA ตรง ๆ และบันทึกวิธีวัด
- รายงานมี 3 สถานะเท่านั้น: `PASS`, `ISSUES`, `BLOCKED` พร้อมหลักฐาน และ worker ที่พิสูจน์ข้อบกพร่องได้ต้องรายงานทุกข้อ ไม่ใช่แค่ข้อแรก
- ตอนรวมผล: ผลที่ไม่บันทึก SHA/วิธี ที่ brief กำหนดจะถูกทิ้งและ respawn **หนึ่งครั้ง** ถ้าพลาดอีกให้บันทึกเป็น **gap ซึ่งไม่นับว่าผ่าน**
- ห้ามแปะผลดิบของ worker ต้องสรุปเป็นตาราง
- **บทเรียน:** ช่องว่างของข้อมูลต้องมองเห็นได้ ไม่ปล่อยให้กลายเป็นผ่านโดยปริยาย

### 5.3 `arena` : แข่งแล้วผสม
หกระยะ: Frame → Fan out → Cross-judge → Pick → Graft → Verify

- **Frame:** สร้าง rubric 3 ถึง 6 ข้อที่ตรวจได้ **ผู้แข่งไม่เห็น rubric** เห็นแต่โจทย์ (กันการเขียนให้ตรงเกณฑ์)
- **Fan out:** ทุกตัวส่งผลงานและ **เหตุผลว่าพิจารณาทางเลือกใดและปัดอะไรทิ้ง** แยกที่เก็บผลงานต่อตัว
- **Cross-judge:** กรรมการ read-only หนึ่งตัว **ต่างตระกูลโมเดลกับผู้นำ** ให้คะแนนรายเกณฑ์ ทำงานขนานกับที่ผู้นำอ่านเอง (ไม่ใช่ขนานกับผู้แข่ง)
- **Pick:** ผู้นำ **อ่านทุกตัวจนจบ** ให้คะแนนรายเกณฑ์ ไม่ใช้ความรู้สึกโดยรวม เทียบกับกรรมการ ถ้าไม่ตรงกัน แปลว่าฝ่ายใดฝ่ายหนึ่งลำเอียงหรือ rubric กำกวม ให้อ่านเหตุผลทั้งสองก่อนตัดสิน เลือกตัวที่ผู้ดูแลในอนาคต **ต่อยอดได้ง่ายที่สุด** ถ้าเสมอให้เลือกขอบเขตที่สะอาดกว่าหรือ API เล็กกว่า
- **Graft:** หยิบ "หนึ่งถึงสองอย่าง" จากตัวที่แพ้ใส่ฐาน **ด้วยมือ** ไม่วางแบบกลไก ผลต้องยังเป็นแบบจำลองความคิดเดียว
- บันทึกว่าหยิบอะไรจากใคร และปัดอะไรเพราะอะไร
- **บทเรียน:** ใช้เมื่อ "การลองครั้งเดียวจะล็อกรูปทรงที่ผิด" เท่านั้น ไม่ใช่ใช้ทุกงาน

### 5.4 `architect` : arena ที่เฉพาะทางกับงานออกแบบ
ห้าระยะ: Ground → Sketch → Agree → Implement → Scrap

- Ground ด้วย `how` (และ `why` ถ้าเปลี่ยนความเป็นเจ้าของ/ชั้นของโค้ด)
- Sketch ด้วย `arena` โดย **ต้องมีอย่างน้อยสองแบบที่โครงสร้างต่างกันจริง** ("design it twice") ร่างเฉพาะ type, signature และขอบเขตโมดูล เนื้อเป็น `not implemented`
- ทุกร่างผ่านรายการ red flag: โมดูลตื้น (shallow), ข้อมูลรั่ว, การแตกตามเวลา (temporal decomposition), เมธอดที่แค่ส่งต่อ
- เปรียบเทียบที่ **ความลึกของ interface** เลือกตัวที่ซ่อนความซับซ้อนไว้หลัง API ที่เล็กกว่า
- Scrap: ถ้าลงมือแล้วร่างผิด **ทิ้งแล้วออกแบบใหม่** ไม่ปะ
- **บทเรียน:** ออกแบบ "ผิวสัมผัส" ก่อน ค่อยลงเนื้อ และมีทางทิ้งแบบที่เป็นขั้นตอนที่ได้รับอนุญาต

### 5.5 `interrogate` : ผู้รีวิวหลายโมเดล
- ส่งผู้รีวิว **หนึ่งตัวต่อหนึ่งโมเดล** ด้วย prompt และ rubric เดียวกัน (ค่าเริ่มต้น opus, fable, sonnet) **ไม่กำหนดบุคลิกให้** ความขัดแย้งมาจากความต่างของโมเดล
- ก่อนส่งต้องเขียน **เจตนาของการเปลี่ยนแปลง** หนึ่งย่อหน้า ถ้าไม่แน่ใจให้ถามผู้ใช้
- ผู้นำสังเคราะห์: ข้อที่ 2 โมเดลขึ้นไปพบเองคือสัญญาณแรงสุด ข้อที่โมเดลเดียวพบอ่านแต่ให้น้ำหนักน้อยกว่า รวมข้อซ้ำ และจดข้อที่โมเดลเห็นต่างกัน
- ผู้นำเป็น **หัวหน้ารีวิวที่ตัดสินใจ ไม่ใช่ผู้รวบรวมกลาง** จัดทุกข้อลง 4 ถัง: **Act on / Consider / Noted / Dismissed** พร้อมเหตุผลบรรทัดเดียวและโมเดลที่พบ
- ผลคือคำตัดสิน **ไม่แก้โค้ดให้เอง**
- **บทเรียน:** แยก "รวบรวมความเห็น" ออกจาก "การตัดสิน" และให้มนุษย์เป็นผู้อนุมัติการแก้

---

## 6. Playbook = ขั้นตอนของทีมที่ถูกแช่แข็ง

| Playbook | ใครเป็นเจ้าของอะไร | ทีมที่ใช้ |
|---|---|---|
| **Bug fix** | ผู้นำเป็นเจ้าของงาน, repro เอง | `how`+`why` หาสมมติฐาน → `architect` ถ้าข้ามฟังก์ชัน → subagent โมเดล strongest แก้ → ตรวจบนหน้าจอเดิม |
| **Feature** | ผู้นำเป็นเจ้าของ **การออกแบบ** | `how` → `architect` → **throughput checkpoint** → มอบ subagent เขียน (ใช้ `arena` ถ้ามีหลายรูปทรงที่ถูกต้อง) → `interrogate` ถ้าถกเถียงได้ |
| **Refactoring** | ผู้นำเป็นเจ้าของ **สัญญาพฤติกรรม** | pin พฤติกรรมก่อน → ลบก่อนเพิ่ม → ย้ายเป็นก้าวเล็กที่ pin ยังเขียว → พิสูจน์ว่าพฤติกรรมไม่เปลี่ยน |
| **Babysit** | ผู้นำเป็นเจ้าของ **merge frontier** | ประกาศโหมด (`drive`, `background`, `threads-only`, `check`) ทำเฉพาะ PR ล่างสุดที่ยังไม่ merge |
| **Multi-phase plan** | ผู้นำเป็นเจ้าของ **แผน ไม่ใช่โค้ด** | prototype แก้ข้อสงสัยก่อน → subagent สำรวจ → เขียนแผนตาม skeleton → ตรวจด้วยสคริปต์ `check-plan.mjs` → ส่งมอบแล้วหยุดรอคำสั่ง |
| **Orchestrate** | Coordinator เป็นเจ้าของ **โปรแกรม ไม่ใช่โค้ด** | coordinator → (sub-coordinator) → worker/verifier |
| **Autopilot-full** | Root เป็นเจ้าของ **คำตัดสิน ไม่ใช่ PR** | หนึ่ง owner ต่อ PR + ทีม swarm ตรวจก่อนทุก merge |

### Throughput checkpoint (ใน Feature ขั้น 3)
เขียนเป็น 4 todo ก่อนมอบงาน ไม่ข้ามได้ ถ้าไม่เกี่ยวให้เขียน `n/a: <เหตุผล>`

1. **Blocking first steps:** ด่านที่ต้องผ่านก่อน fan out
2. **Independent workstreams:** ไฟล์/service/ชั้นที่แยกกัน ขนานได้ ส่วนที่เขียนร่วมกันต้องเรียงลำดับ
3. **Shared mutable state:** ค่าเริ่มต้นคือแยกเป้าหมายการเขียน
4. **Smallest safe decomposition:** ถ้า worker คนเดียวดีที่สุด ต้องบอกเหตุผล

ข้อสังเกต: **งานที่ผูกกันแน่น (หนึ่งฟีเจอร์ หนึ่ง migration) ให้เจ้าของคนเดียว** ที่ fan out เองภายในหลังเฟส blocking ส่วนการ fan out ระดับผู้นำสงวนไว้สำหรับชิ้นงานที่ผลิต artifact อิสระ (audit, สืบสวนข้ามระบบ, ทดลองแข่ง)

---

## 7. ทีมระดับโปรแกรม: Orchestrate และ Autopilot-full

### 7.1 Orchestrate (โปรเจกต์ที่ใช้หลายวัน มี PR ซ้อนกันหลายชั้น)
กฎสามข้อที่รับน้ำหนักทั้งหมด
1. **Completions are queue events, not interrupts.** งานที่เสร็จคือเหตุการณ์เข้าคิว ไม่ใช่การขัดจังหวะ
2. **Every spawn and every resume carries the standing orders verbatim.** ทุกการ spawn และ resume พก "คำสั่งประจำ" ไปแบบคำต่อคำ
3. **The brief is the product.** brief คือผลิตภัณฑ์ เพราะ worker ถามกลับไม่ได้

บทบาท 3 ชั้น (ความลึกจำกัดแค่ coordinator → track → worker)

| บทบาท | ทำ | ห้ามทำ |
|---|---|---|
| **Coordinator** | ตั้งกรอบ เขียน brief ระบายคิว ตัดสิน รายงานคน | **ไม่เขียนหรือแก้โค้ดเอง** (conflict, restack, แก้โค้ดเป็น "งาน" เสมอ) |
| **Sub-coordinator** | ดูแล track หนึ่ง เขียน brief ให้ worker สรุปรายงานตอนจบ wave | ส่งต่อรายงานดิบของลูก และเป็นชั้นกลางโดยไม่จำเป็น |
| **Worker / Verifier** | ทำงานเบื้องหลัง ตรวจ | worker ของหน่วยเดียวกันห้ามเป็นตัวตรวจ ต้อง **ต่างตระกูลโมเดล** |

เหตุผลที่ระบุ: ทุกชั้นที่ซ้อนต้องจ่ายค่า orientation ใหม่ sub-coordinator ที่ block จะซ่อนลูกจาก parent ให้จำกัดลูกที่ทำงานพร้อมกันราว 10 แบบ **หน้าต่างเลื่อน** ไม่ใช่เป็นชุดที่ต้องรอตัวช้าสุด

**Store นอก repo และนอก session:** `~/.claude/orchestrate/<slug>/` เพราะโปรแกรมรันหลายวันและ session restart เป็นเรื่องปกติ **ทุกไฟล์มีผู้เขียนเดียว**

| ไฟล์ | เนื้อหา |
|---|---|
| `preferences.md` | ทะเบียนคำสั่งประจำ เป็นบรรทัดเลขที่ ข้อละหนึ่งข้อจำกัด วางลงในทุก spawn/resume เพราะ "directives decay across resumes" |
| `overview.md` | ฐานข้อมูล PR/issue แบบ append |
| `units.tsv` | หนึ่งแถวต่อหน่วยงาน (id, track, state, branch, PR, head SHA, brief path) |
| `frontier.json` | merge frontier ที่คำนวณได้ |
| `ledger.tsv` | บัญชีการตรวจสอบ |
| `inbox/`, `gates.md` | ตัวชี้ผลที่เสร็จ / ด่านที่รอมนุษย์ (คำถาม ตัวเลือก ค่าเริ่มต้นถ้าไม่ตอบ) |
| `decisions.tsv` | เส้นทางการตัดสินใจ (ผ่านสกิล `show-me-your-work`) |
| `status.md` | **คำนวณจากตาราง** ทุกครั้งที่ระบายคิว ไม่เขียนมือ |

**รูปแบบของ brief** (ทุก spawn ต้องมี "ช่องที่กรอกไม่ได้ = หน่วยที่ยังไม่ได้ scope"): `GOAL` (หนึ่งประโยค คนแปลกหน้าทำได้) · `SCOPE` (path ที่เขียนได้/ห้าม, worktree เฉพาะ) · `CONTEXT` (ตัวชี้ไฟล์ และรายงานต้นทางแปะเต็มเมื่อพึ่งพากัน เพราะ worker มองไม่เห็นพี่น้อง) · `ACCEPTANCE` (เกณฑ์ที่ตรวจได้ บรรทัดละข้อ) และต่อจากนั้นตามไฟล์ต้นฉบับ (ผมอ่านถึงช่อง ACCEPTANCE ช่องถัดไปยังไม่ได้อ่าน)

CLI `orch` มีไว้ทำบัญชี **ไม่เคย spawn, wait หรือปลุก agent** ส่วนนั้นเป็นหน้าที่ของ `Agent` เท่านั้น

### 7.2 Autopilot-full (คิวของ PR อิสระ ใช้ autonomy เต็ม)
- **หนึ่ง owner ต่อ PR** (subagent เบื้องหลัง ใน worktree ของตัวเอง) ทำตั้งแต่ build, push แรก, PR ready, พิสูจน์ตัวเองบนของจริง, คัดกรองคอมเมนต์ review-bot อย่างสงสัย, `deslop`, `no-comments`, rebase, babysit จนเขียว
- ภายในราว 15 นาที ทุก owner ต้องเริ่ม `decisions.tsv` (เส้นทางการตัดสินใจ)
- **Root** ถือแค่คำตัดสิน: ทุกรอบก่อน merge ต้องมี **swarm ผู้ตรวจอิสระขนาน** ที่ SHA ของ PR (รันด่านซ้ำ, พิสูจน์พฤติกรรมสำคัญบนพื้นผิวจริง, ตรวจ diff โดย **ไม่เชื่อ PR body**, regression lane เทียบกับ trunk)
- **ต้องมีทั้งคำตัดสิน swarm สะอาด และมนุษย์กด merge เอง**
- เมื่อผ่านแล้ว owner ส่งต่อ แล้ว **owner ใหม่รับคิวถัดไป**
- Root ตรวจ owner ทุกชั่วโมงด้วย `/loop` แบบ dynamic (ห้ามพึ่งความจำหรือการแจ้งที่หายได้) และอ่าน playbook ซ้ำจากดิสก์ทุกครั้ง (กัน directive หาย)
- เมื่อมนุษย์สั่งหยุด ทุก owner หยุดเขียนทันที
- PR อิสระ **ไม่ stack** ให้แตกจาก main ตรง ๆ และรันขนานจริง งานที่ซ้อนกันจริงเท่านั้นที่เรียงลำดับ

### 7.3 Babysit: กฎของ "ผู้เฝ้า"
- ประกาศโหมดก่อนทุกครั้ง (`drive` / `background` / `threads-only` / `check`)
- ทำเฉพาะ **PR ล่างสุดที่ยังไม่ merge** (frontier) ถ้าเผลอไปแก้ชั้นบนขณะ frontier แดง ให้หยุดและกลับลงมา
- **หนึ่ง babysitter ต่อหนึ่ง stack** และ **ห้ามเปลี่ยนโทโพโลยีของ stack** (ห้าม retarget, rebase, force-push) ให้รายงานขึ้นไปให้ owner
- ลำดับ: conflict → review threads → CI และรวมการแก้เป็น push wave เดียว
- เชื่อ **คำตัดสินของ forge** ไม่ใช่รายการเช็คสีเขียว
- watcher ที่ re-arm ไม่ได้ให้สิทธิ์ merge การ merge ต้องมีมนุษย์สั่งชัด

---

## 8. หลักออกแบบ 10 ข้อที่ดึงออกมาได้

| # | หลักการ | หลักฐานในไฟล์ |
|---|---|---|
| 1 | **ผู้นำไม่ทำงานฝีมือ** ผู้นำวางแผน รีวิว ตัดสิน | "You own the program, never the code" |
| 2 | **แยกตัวทำออกจากตัวตรวจ** และตัวตรวจควรต่างตระกูลโมเดล | Orchestrate: verifier ต่างตระกูล, arena cross-judge |
| 3 | **ความหลากหลายสร้างสัญญาณ** ไม่ต้องกำหนดบุคลิกให้ reviewer | interrogate |
| 4 | **brief ที่ครบในตัวเองคือผลิตภัณฑ์** worker ถามกลับไม่ได้ | Orchestrate, swarm Phase B |
| 5 | **แยกผู้เขียน ไม่ใช่ล็อกผู้เขียน** (worktree/branch ต่อคน) | principle `separate-before-serializing-shared-state` ("Instructions and conventions are not concurrency control") |
| 6 | **ลูกทีมสด ไม่ใช่ลูกทีมเดิมที่ถูกขัดจังหวะ** | Subagents: fresh by default |
| 7 | **ช่องว่างต้องมองเห็น** ผลที่ขาดคือ gap ไม่ใช่ผ่าน | swarm Phase C |
| 8 | **ย้ายความรู้ออกจากความจำ ไปไว้ที่ไฟล์** | store, `preferences.md`, `status.md` ที่คำนวณจากตาราง |
| 9 | **เมื่อสั่งซ้ำเป็นครั้งที่สอง ให้เข้ารหัสเป็นโครงสร้าง** | principle `encode-lessons-in-structure`, `check-plan.mjs`, `generate.mjs --check` |
| 10 | **หน่วงการทำสิ่งที่ย้อนกลับไม่ได้ไว้ให้มนุษย์** | Autonomy: always pause (force-push, deploy, ลบข้อมูล, ข้อความถึงลูกค้า) |

หลักการเสริมที่เกี่ยวกับทีมโดยตรง
- **Guard the Context Window:** ส่งของใหญ่ให้ subagent ผู้นำถือแต่สรุป
- **Never Block on the Human:** งานที่ย้อนกลับได้ให้เดินหน้า แสดงผล แล้วให้มนุษย์แก้ทีหลัง
- **No is an acceptable answer:** "A recommendation is a judgment, not a validation." ผู้นำต้องกล้าปฏิเสธและแย้ง

---

## 9. นำไปประยุกต์กับงานของคุณ

บริบท: คุณเป็น dev ทำฟีเจอร์ใหม่ แก้บั๊ก และย้าย API จาก PHP เป็น Go ข้อเสนอด้านล่างเป็น **การตีความของผู้เขียน** ไม่ใช่สิ่งที่ pstack กำหนด

### 9.1 ปรับใช้ได้ทันที: ออกแบบการมอบหมายงาน (ไม่ต้องสร้างทีมใหญ่)

1. **ใช้โมเดลตามความยาก** แก้บั๊กและออกแบบให้โมเดลแรงสุด งานแปลโค้ดเชิงกลไกให้โมเดลถูก
2. **เขียน brief 4 ช่อง** (GOAL, SCOPE, CONTEXT, ACCEPTANCE) ทุกครั้งที่ส่งงานให้ subagent
3. **ตัวตรวจต่างจากตัวทำ** เช่นให้โมเดลหนึ่งแปล อีกโมเดล (ต่างตระกูล) รีวิวหรือรัน harness
4. **ส่งตัวชี้ไฟล์ ไม่ยัดเนื้อหา**
5. **สั่งให้ขนานเฉพาะงานที่ไม่เขียนไฟล์ร่วมกัน** เช่น แปลคนละ endpoint คนละ branch

### 9.2 ทีมสำหรับงานย้าย PHP → Go (ข้อเสนอ)

```
Coordinator (คุณ + session หลัก)
  │   เป็นเจ้าของแผน, preferences.md, ลำดับ endpoint, การตัดสินใจ
  │
  ├─ Mapper (read-only, หลายตัวขนาน)
  │     ต่อ endpoint: อ่านโค้ด PHP สรุปสัญญาจริง + ผู้เรียกใช้ (how + blast-radius)
  │
  ├─ Baseline builder (ตัวเดียว)
  │     สร้าง harness บันทึก/เล่นซ้ำ request เทียบ PHP กับ Go
  │
  ├─ Translators (หนึ่งตัวต่อ endpoint, worktree/branch ของตัวเอง)
  │     ได้ brief: PHP path, Go path ที่เขียนได้, สัญญา, harness, เกณฑ์ผ่าน
  │
  ├─ Verifiers (โมเดลต่างตระกูลจาก translator)
  │     รัน harness ที่ SHA ของ branch, รายงาน PASS / ISSUES / BLOCKED
  │
  └─ Reviewers (interrogate เฉพาะ endpoint เสี่ยง: เงิน, auth, transaction)
```

ตัวอย่าง brief ของ Translator

```text
GOAL        แปล endpoint POST /orders จาก PHP เป็น Go ให้พฤติกรรมเทียบ baseline ตรงกันทุกเคส
SCOPE       เขียนได้: internal/orders/**, cmd/api/routes_orders.go
            ห้ามแตะ: โค้ด PHP, endpoint อื่น, ไฟล์ migration
            branch/worktree: migrate/orders
CONTEXT     สรุปสัญญาของ endpoint: docs/migration/orders-contract.md
            baseline: testdata/baseline/orders/*.json
            harness: scripts/replay-compare.sh
ACCEPTANCE  - replay-compare.sh ผ่านทุกเคสที่ HEAD
            - status code, error body, header สำคัญตรงกับ baseline
            - ไม่เพิ่ม dependency ใหม่ถ้าไม่จำเป็น
            รายงาน: PASS/ISSUES/BLOCKED พร้อม SHA และผลรัน
```

### 9.3 `preferences.md` ของโปรเจกต์คุณ (ข้อเสนอ)
สร้างทะเบียนคำสั่งประจำ แล้ววางลงใน **ทุก** brief ตัวอย่าง

```text
1. PHP endpoint ต้องยังใช้งานได้จนกว่า Go endpoint ผ่าน baseline และมนุษย์สั่งตัดการเชื่อมต่อ
2. ห้าม force-push, ห้าม deploy, ห้ามลบข้อมูล โดยไม่ถามผม
3. หนึ่ง endpoint ต่อหนึ่ง PR ต่อหนึ่ง branch
4. baseline ห้ามมีข้อมูลจริงของผู้ใช้ ใช้ข้อมูลสังเคราะห์หรือปกปิดแล้ว
5. endpoint ที่เกี่ยวกับเงินหรือ auth ต้องผ่าน interrogate ก่อนเปิด PR
6. ตัวตรวจต้องใช้โมเดลต่างตระกูลจากตัวแปล
```

เหตุผลตามที่ pstack ระบุ: คำสั่งจะ "decay across resumes" ถ้าไม่ถูกพกไปทุกครั้ง

### 9.4 ตัวอย่างแผนผังไฟล์ (ข้อเสนอ ดัดแปลงจาก store ของ Orchestrate)

```text
docs/migration/
  preferences.md        คำสั่งประจำ
  units.tsv             endpoint | state | branch | PR | head SHA | brief path
  ledger.tsv            endpoint | SHA | ผลรัน harness | ผู้ตรวจ | วันที่
  decisions.tsv         what | why | evidence | result
  briefs/<endpoint>.md
  <endpoint>-contract.md
```

หลักคือ **หนึ่งไฟล์ต่อหนึ่งผู้เขียน** และ `status` ที่สรุปให้ตัวเองต้องคำนวณจากตาราง ไม่เขียนมือ

### 9.5 ใช้ pattern ของ pstack กับงานประจำวัน

| สถานการณ์ | ใช้ pattern |
|---|---|
| ฟีเจอร์ที่มีหลายทางออกแบบ | `architect` หรือ `arena` และต้องมีสองรูปทรงที่ต่างกันจริง |
| ฟีเจอร์ที่ผูกกันแน่น | เจ้าของคนเดียว fan out ภายในหลังเฟส blocking |
| บั๊กที่ไม่รู้สาเหตุ | สมมติฐานหลายข้อ ใช้ subagent read-only สืบทีละข้อ ตัวนำตัดสิน |
| PR เล็ก ๆ หลายตัวที่ไม่ซ้อนกัน | **ไม่ stack** แตกจาก main ขนานกัน |
| ต้องวัดความเร็ว PHP กับ Go | `benchmark-checklist` ก่อนรายงานตัวเลข |
| งานยาว ๆ ข้ามวัน | store นอก repo + `/loop` แบบ dynamic + `decisions.tsv` |

### 9.6 การเริ่มแบบค่อยเป็นค่อยไป (ข้อเสนอ)

| ระยะ | ทำ | ตรวจว่าได้ผล |
|---|---|---|
| 1 | ใช้ `poteto-mode` กับบั๊กและฟีเจอร์ปกติ 1 ถึง 2 สัปดาห์ | จำนวนรอบแก้ลดลงหรือไม่ มีหลักฐาน repro ก่อนและหลังหรือไม่ |
| 2 | ย้าย endpoint **เสี่ยงต่ำ 1 ตัว** ด้วย Refactoring + harness | harness จับความต่างจริงได้ไหม |
| 3 | ย้าย 3 ถึง 5 endpoint ขนานด้วย brief 4 ช่อง + verifier ต่างโมเดล | ผู้ตรวจพบข้อผิดพลาดที่ผู้แปลมองข้ามหรือไม่ |
| 4 | ค่อยพิจารณา `figure-it-out` / Orchestrate เมื่อมี endpoint จำนวนมาก | ค่าใช้จ่ายคุ้มกับเวลาที่ประหยัดหรือไม่ |

อย่าข้ามไประยะ 4 เลย ตัว Orchestrate เองก็เขียนว่า "Ceremony must scale with the program" และงานที่ agent เดียวทำเสร็จภายใน budget ของ session ไม่ใช่ "โปรแกรม"

---

## 10. ข้อจำกัดและความเสี่ยงที่ควรรู้

- **ค่าใช้จ่าย:** panel 3 โมเดล, arena และ swarm เรียกหลายตัวพร้อมกัน ใช้ token มาก ลดได้ด้วย role override และเลือกใช้เฉพาะงานที่ "การลองครั้งเดียวจะล็อกรูปทรงที่ผิด"
- **ข้อกำหนดของ pstack ที่ขัดกับการย้ายระบบจริง:** Refactoring ห้ามมี shim ที่ให้โค้ดเก่าและใหม่รันคู่กัน แต่การย้าย API จริงอาจต้องรันคู่กันชั่วคราว ให้ระบุข้อยกเว้นนี้ใน `preferences.md` (ข้อ 1 ด้านบน)
- **ลูกทีมคือ process ในเครื่อง:** ตามไฟล์ Orchestrate "Claude Code has no remote worker environment" การแยกความเป็นอิสระมาจาก worktree/branch ไม่ใช่เครื่องแยก
- **ความลึกของทีม:** ยิ่งซ้อนชั้นยิ่งแพง ใช้แค่ coordinator → worker ให้นานที่สุด
- **ข้อมูลสำคัญ:** โค้ดและ transcript ที่ agent อ่านถูกส่งไปที่ผู้ให้บริการโมเดล
- **เอกสารเหล่านี้เป็น "คำสั่งถึงโมเดล" ไม่ใช่กลไกบังคับ:** ความน่าเชื่อถือขึ้นกับว่าโมเดลทำตามจริงหรือไม่ จึงควรตรวจหลักฐาน (todolist, `decisions.tsv`, ผลรัน harness) แทนการเชื่อรายงาน ซึ่งตรงกับหลักของ pstack เอง
- **ยังไม่ได้ตรวจกับโปรเจกต์ของคุณ:** ข้อเสนอในหัวข้อ 9 ควรทดลองเล็กก่อนใช้จริง

---

## 11. ไฟล์ต้นฉบับที่ควรอ่านต่อ

| หัวข้อ | ไฟล์ |
|---|---|
| กติกาผู้นำ, Subagents, Autonomy, Principles | `plugins/pstack/skills/poteto-mode/SKILL.md` |
| playbook ทั้งหมด | `plugins/pstack/skills/poteto-mode/playbooks/*.md` |
| ทีมระดับโปรแกรม | `playbooks/orchestrate.md`, `playbooks/autopilot-full.md`, `playbooks/autopilot-stack.md` |
| รูปแบบ fan out | `skills/swarm`, `skills/arena`, `skills/architect`, `skills/interrogate`, `skills/how` |
| นโยบายโมเดล | `plugins/pstack/models.json`, `tools/generate.mjs` |
| ศัพท์และการแยกชั้นของระบบ | `CONTEXT.md` |
| นิยาม agent | `plugins/pstack/agents/`, `plugins/pstack/effort-agents/` |
