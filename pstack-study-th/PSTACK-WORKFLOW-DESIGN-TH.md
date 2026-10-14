# หลักการออกแบบ Workflow Agent ของ pstack (ฉบับละเอียดทุกขั้นตอน)

[← กลับไปหน้ารวม](README.md)

> **ที่มา:** สรุปจากการอ่านไฟล์จริงในโปรเจกต์นี้ ได้แก่ `plugins/pstack/hooks/`, `models.json`, `agents/poteto-agent.md`, `skills/poteto-mode/SKILL.md`, playbook Investigation, Bug fix, Feature, Refactoring, Prototype, Autonomous run, Orchestrate, Opening a PR, Pause safely และ Session pickup รวมถึงสกิล `how`, `why`, `architect`, `arena`, `swarm`, `interrogate`, `reflect`, `figure-it-out`, `show-me-your-work` และ principle บางตัว
>
> **ขอบเขต:** เอกสารนี้เน้นวิธีเขียนและออกแบบ workflow ส่วนเรื่องโครงสร้างทีม agent และการเลือกโมเดลอยู่ใน [`PSTACK-AGENT-TEAM-DESIGN-TH.md`](../PSTACK-AGENT-TEAM-DESIGN-TH.md)
>
> **การยืนยัน:** ผมยังไม่ได้รันระบบจริง ทุกอย่างมาจากการอ่านคำสั่งในไฟล์ ส่วนที่เป็นการตีความหรือข้อเสนอของผมจะเขียนกำกับไว้ว่า **(ตีความ)** หรือ **(ข้อเสนอ)**

---

## สารบัญ

1. [แนวคิดตั้งต้น](#1-แนวคิดตั้งต้น)
2. [สถาปัตยกรรมชั้นของ workflow](#2-สถาปัตยกรรมชั้นของ-workflow)
3. [ขั้นที่ 0: การเข้าระบบด้วย Hook](#3-ขั้นที่-0-การเข้าระบบด้วย-hook)
4. [ขั้นที่ 1: Router (`poteto-mode`)](#4-ขั้นที่-1-router-poteto-mode)
5. [กายวิภาคของ Playbook](#5-กายวิภาคของ-playbook)
6. [Playbook ทีละตัวแบบละเอียด](#6-playbook-ทีละตัวแบบละเอียด)
7. [สกิล fan-out ทีละตัวแบบละเอียด](#7-สกิล-fan-out-ทีละตัวแบบละเอียด)
8. [สัญญาการมอบหมายงาน (Delegation Contract)](#8-สัญญาการมอบหมายงาน-delegation-contract)
9. [ระบบการตรวจสอบ (Verification)](#9-ระบบการตรวจสอบ-verification)
10. [ระดับอิสระในการตัดสินใจ (Autonomy)](#10-ระดับอิสระในการตัดสินใจ-autonomy)
11. [ความต่อเนื่อง: หยุด รับช่วง และ decision trail](#11-ความต่อเนื่อง-หยุด-รับช่วง-และ-decision-trail)
12. [การบังคับด้วยโครงสร้างแทนข้อความ](#12-การบังคับด้วยโครงสร้างแทนข้อความ)
13. [การเขียน prompt และ skill](#13-การเขียน-prompt-และ-skill)
14. [Checklist และ Template สำหรับออกแบบ workflow ของคุณ](#14-checklist-และ-template-สำหรับออกแบบ-workflow-ของคุณ)
15. [ลำดับการอ่านไฟล์ต้นฉบับ](#15-ลำดับการอ่านไฟล์ต้นฉบับ)

---

## 1. แนวคิดตั้งต้น

pstack แทบไม่มีโค้ดที่คุม agent workflow ทั้งหมดเป็น **ไฟล์ Markdown ที่ agent อ่านแล้วทำตาม** ส่วนโค้ดและสคริปต์ใช้กับเรื่องที่ไม่ควรให้ agent ตัดสินเอง เช่น การ stamp ค่าโมเดล การตรวจลิงก์ และการจัดเก็บสถานะงาน

แนวคิดที่ร้อยทั้งระบบเข้าด้วยกันมี 5 ข้อ

| # | แนวคิด | ความหมายในทางปฏิบัติ |
|---|---|---|
| 1 | **แบ่งชั้นความรับผิดชอบ** | แยกตัว route, ขั้นตอนงาน, รูปแบบ fan-out และหลักคิดออกจากกัน แต่ละชั้นโหลดเมื่อต้องใช้เท่านั้น |
| 2 | **ตัวนำเป็นเจ้าของงาน แต่ไม่ลงมือเอง** | ตัวนำวางแผน มอบงาน ตรวจงาน และยืนยันผล ส่วนการเขียนโค้ดส่งให้ subagent |
| 3 | **ทุกขั้นตรวจได้** | ทุก playbook มีเงื่อนไขว่าเสร็จ และผลลัพธ์มีสถานะชัดเจน คำว่า "ไม่แน่ใจ" ไม่นับว่าผ่าน |
| 4 | **ความหลากหลายสร้างการตรวจสอบ** | ใช้หลายโมเดลกับโจทย์เดียวกัน แยกผู้ทำออกจากผู้ตรวจ |
| 5 | **บทเรียนที่เจอซ้ำต้องกลายเป็นโครงสร้าง** | ถ้าต้องเขียนคำสั่งเดิมซ้ำ ให้เปลี่ยนเป็น lint, script หรือ check แทน |

---

## 2. สถาปัตยกรรมชั้นของ workflow

```
┌─────────────────────────────────────────────────────────────┐
│ ชั้น 0  Hook (SessionStart)                                  │
│         ฉีดกฎการเข้าระบบทุกครั้งที่เริ่ม/resume/clear/compact     │
├─────────────────────────────────────────────────────────────┤
│ ชั้น 1  Router: poteto-mode/SKILL.md                         │
│         Non-negotiables, Principles index, Autonomy,         │
│         Subagents, Writing the reply, รายการ playbook          │
├─────────────────────────────────────────────────────────────┤
│ ชั้น 2  Playbooks: poteto-mode/playbooks/*.md                 │
│         ขั้นตอนของงานแต่ละประเภท (Bug fix, Feature, ...)         │
├─────────────────────────────────────────────────────────────┤
│ ชั้น 3  Skills เชิงกระบวนการ: how, why, architect, arena,       │
│         swarm, interrogate, reflect, figure-it-out            │
│         + references/*.md (prompt template ของลูกทีม)           │
├─────────────────────────────────────────────────────────────┤
│ ชั้น 4  Principles: principle-*/SKILL.md (~20 ไฟล์)            │
│         หลักคิดที่เปิดอ่านเมื่อเข้าเงื่อนไข                         │
├─────────────────────────────────────────────────────────────┤
│ ชั้นรองรับ  Scripts + Generator + Tests                         │
│         generate.mjs, check-playbooks.mjs, orch, resume.mjs  │
└─────────────────────────────────────────────────────────────┘
```

**ทำไมต้องแบ่งชั้น (ตีความ)**
- **ประหยัด context** ตัว router มีแค่ดัชนีกับเงื่อนไข ส่วนเนื้อหาเต็มของ principle และ playbook โหลดเมื่อต้องใช้ (`principle-guard-the-context-window`)
- **ใช้ซ้ำได้** playbook หลายตัวเรียก `how`, `architect` และ `arena` ร่วมกัน โดยไม่ต้องเขียนซ้ำ
- **แก้ทีละจุดได้** ปรับรูปแบบ fan-out ใน `arena` ทีเดียว ทุก playbook ที่เรียกใช้ได้ผลตามไปด้วย

---

## 3. ขั้นที่ 0: การเข้าระบบด้วย Hook

**ไฟล์:** `hooks/hooks.json`, `hooks/session-start.sh`, `hooks/session-start-context.md`

### ขั้นตอนการทำงาน
1. `hooks.json` ผูกกับ event `SessionStart` ด้วย matcher `startup|resume|clear|compact`
2. `session-start.sh` รับชื่อ runtime (`claude` หรือ `codex`) แล้วหาไฟล์ `pstack-models.md` ของ runtime นั้น
3. ถ้าในไฟล์นั้นมีบรรทัด `session hook: off` สคริปต์จะจบโดยไม่ทำอะไร ผู้ใช้จึงปิดระบบได้
4. ถ้าไม่ได้ปิด สคริปต์จะพิมพ์ `session-start-context.md` เข้า context

### เนื้อหาที่ฉีดเข้าไป
- เรียก `poteto-mode` เมื่อเข้าเงื่อนไขข้อใดข้อหนึ่ง
  - งานแตะมากกว่าหนึ่งไฟล์ หรือเปลี่ยน signature ที่ไฟล์อื่นเรียกใช้
  - งานมีการตัดสินใจเชิงออกแบบหรือสถาปัตยกรรม
  - เป็นบั๊กที่ยังไม่รู้สาเหตุ หรือเป็นปัญหา performance
- **งานเล็กให้ทำตรง ๆ** เช่น แก้ไฟล์เดียวที่มี test ชัด, ตอบคำถาม หรือแก้บรรทัดเดียว
- ถ้าเจตนาของผู้ใช้ชัดอยู่แล้ว ให้เข้า skill นั้นโดยตรง เช่น `tdd`, `architect`, `how`
- คำสั่งของผู้ใช้ (CLAUDE.md, AGENTS.md, คำขอตรง ๆ) มีลำดับความสำคัญสูงกว่า

### หลักออกแบบที่ได้
- **เกณฑ์การเข้าระบบต้องวัดได้** ใช้ "แตะมากกว่าหนึ่งไฟล์" แทนคำกว้าง ๆ อย่าง "งานใหญ่"
- **ต้องกำหนดด้วยว่างานแบบไหนไม่ต้องเข้าระบบ** ถ้าไม่กำหนด ระบบจะหนักเกินงาน
- **ต้องฉีดซ้ำหลัง `compact`** เพราะกฎอาจหายไปตอนที่ context ถูกสรุปย่อ **(ตีความ)**
- **ต้องมีสวิตช์ปิด** ที่ผู้ใช้ปิดเองได้โดยไม่ต้องแก้โค้ด

---

## 4. ขั้นที่ 1: Router (`poteto-mode`)

**ไฟล์:** `skills/poteto-mode/SKILL.md`, `agents/poteto-agent.md`

### 4.1 ส่วนประกอบของ Router

| ส่วน | หน้าที่ |
|---|---|
| Platform Adaptation | แปลงชื่อเครื่องมือให้ตรงกับ runtime (Claude Code / Codex / Pi) ผ่านไฟล์ mapping |
| Non-negotiables | กฎแบบ trigger → action เช่น "เห็นโค้ดข้าม function boundary → architect" |
| Principles | ดัชนีของ principle แต่ละตัว พร้อมเงื่อนไขว่าใช้เมื่อไร |
| Autonomy | กำหนดว่างานแบบไหนทำได้เลย และงานแบบไหนต้องหยุดถาม |
| Subagents | สัญญาการมอบหมายงาน |
| Writing the reply | กฎการเขียนคำตอบ |
| Playbooks | รายการ playbook พร้อมคำอธิบายว่าใช้กับงานแบบไหน |
| Models / Reasoning effort | โมเดลต่อบทบาท (stamp มาจาก `models.json`) |

### 4.2 ขั้นตอนที่ Router ทำ
1. **จับคู่งานกับ playbook** จากรายการ ถ้าเป็นงานใหญ่หรือข้ามหลายส่วน ให้ใช้ `figure-it-out` ถ้าเป็นโปรเจกต์ที่ใช้เวลาหลายวัน ให้ใช้ Orchestrate
2. **เปิด todolist** โดยคัดขั้นตอนของ playbook มาแบบคำต่อคำเป็นรายการแรก ๆ ก่อนรายการเฉพาะของงาน
3. **ขั้นที่เลือกไม่ทำต้องอยู่ในรายการต่อ** และเขียน `skip: <เหตุผล>` กำกับ
4. ถ้าไม่มีเครื่องมือ todo ให้ใช้ไฟล์ `todo.md` ที่ไม่ commit แทน
5. ถ้าโปรเจกต์มี playbook ของตัวเองใน `.agents/playbooks/` ให้โหลดด้วย และรัน `check-playbooks.mjs` ก่อนใช้
6. ทำตาม playbook และเรียก principle ที่เกี่ยวข้อง ต้องเปิดอ่านไฟล์ของ principle นั้นจริงก่อนอ้างถึง
7. จบด้วยคำตอบตามรูปแบบใน **Writing the reply**

### 4.3 Non-negotiables: รูปแบบ trigger → action
กฎในส่วนนี้เขียนเป็นคู่ "สถานการณ์ → สิ่งที่ต้องทำ" ทั้งหมด ตัวอย่าง:

| Trigger | Action |
|---|---|
| งาน nontrivial หรือมีคนถามว่า "แน่ใจไหม" | ใช้ `how` |
| กำลังจะถามผู้ใช้ว่า "ใช้วิธีไหนดี" | แยกก่อนว่าคำถามนั้นรันดูคำตอบได้ไหม ถ้ารันได้ ให้ทำ Prototype แทนการถาม |
| ต้องเขียนโค้ด | ตั้งชื่อรูปร่างข้อมูลก่อน |
| โค้ดข้าม function boundary | ใช้ `architect` |
| ต้อง fan-out หลายงานขนานกัน | ใช้ `swarm` หรือ `arena` |
| การออกแบบยังเถียงกันอยู่ | ใช้ `interrogate` |
| ก่อน commit | ใช้ `deslop` |
| ก่อนส่งรีวิว | ใช้ `no-comments` |
| ได้ตัวเลข benchmark | ใช้ `benchmark-checklist` ก่อนรายงาน |
| bot รีวิว PR ให้ comment | อ่านอย่างสงสัยไว้ก่อน แล้วคัดแยกเป็น fix / dismiss / ask |
| เจอ skill ที่พังระหว่างทำงาน | แก้ใน PR แยก ห้ามรอ และห้ามเลี่ยงแบบเงียบ ๆ |
| งานยาวหรือผู้ใช้ไม่อยู่ | ใช้ `show-me-your-work` |

**หลักออกแบบ:** เขียนกฎเป็นคู่ trigger กับ action เพื่อให้ agent จับคู่สถานการณ์ได้ แทนการเขียนเป็นคำแนะนำทั่วไปที่ต้องตีความเอง

### 4.4 Subagent ตัวหลัก `poteto-agent`
`agents/poteto-agent.md` สั้นมาก มีคำสั่งเดียวคือ "อ่าน SKILL.md ของ poteto-mode ให้ครบก่อนทำงาน" และเตือนไว้ว่าถ้าใช้ `general-purpose` แทน agent จะข้ามการอ่านนี้แล้วทำงานคลาดไปจากแนวทาง

**หลักออกแบบ:** subagent ต้องโหลดกฎชุดเดียวกับตัวนำ และวิธีที่ทำให้มั่นใจได้คือผูกไว้กับประเภท agent ไม่ใช่หวังว่าคนเขียน brief จะใส่ไว้เอง

---

## 5. กายวิภาคของ Playbook

ทุก playbook มีโครงเดียวกัน ดังนี้

```markdown
### <ชื่อ playbook>

**You own <สิ่งที่เป็นเจ้าของ>. <หน้าที่หลัก 2-3 คำกริยา>.**

<ย่อหน้าสั้น ๆ: ขอบเขต, แยกจาก playbook อื่นอย่างไร, เมื่อไรควรย้ายไป playbook อื่น>

1. <ขั้นตอนที่ตรวจได้>
2. ...
N. Run **Opening a PR**.

**Reply:** <สิ่งที่คำตอบสุดท้ายต้องมี>
```

### องค์ประกอบ 6 ส่วน

| ส่วน | ตัวอย่าง | ประโยชน์ |
|---|---|---|
| **1. Ownership line** | Bug fix: "You own this task. Plan, review, verify." / Refactoring: "You own the contract. The structure changes. The behavior does not." / Prototype: "You own the design decision, not the code." | บอก agent ในบรรทัดเดียวว่าต้องปกป้องอะไร |
| **2. ขอบเขตและทางออก** | Refactoring: "ถ้าเจอบั๊กจริง ให้แยกออกไป" / Investigation: "ถ้าต้องแก้โค้ด ให้ย้ายไป Bug fix หรือ Feature" | กันไม่ให้งานบานปลายใน playbook ที่ไม่ใช่ของมัน |
| **3. ขั้นตอนที่มีหมายเลข** | สั้น เป็นคำกริยา ตรวจได้ | คัดลง todolist ได้ทันที |
| **4. เกณฑ์ที่ไม่ยอมผ่อน** | "Inconclusive or wrong-surface is not a pass" | กันไม่ให้ agent ประกาศว่าเสร็จก่อนเวลา |
| **5. ส่งต่อ playbook ร่วม** | ทุกตัวจบด้วย **Opening a PR** | ขั้นตอนท้ายเป็นมาตรฐานเดียวกัน |
| **6. Reply spec** | Bug fix: "what was broken, root cause, fix, how you verified. Quote the decisive failing and passing output" | กำหนดรูปแบบผลลัพธ์ไว้ล่วงหน้า |

### กฎของ todolist
- คัดขั้นตอนลงไปแบบ **คำต่อคำ** ไม่สรุปเอง
- ขั้นที่ไม่ทำต้องมี `skip: <reason>` ห้ามลบทิ้ง
- ใน Feature ขั้นที่ 3 ถ้ามิติไหนไม่เกี่ยว ให้เขียน `n/a: <reason>` ห้ามลบเช่นกัน

**ทำไมสำคัญ (ตีความ):** เมื่อการข้ามขั้นถูกบันทึกไว้ คนที่มาตรวจทีหลังก็เห็นได้ทันทีว่าข้ามอะไรและเพราะอะไร

---

## 6. Playbook ทีละตัวแบบละเอียด

### 6.1 Investigation (คำถามแบบอ่านอย่างเดียว)
**Ownership:** You own the answer. Plan, route, write.

1. ส่งเข้า `how` ถ้าเป็นคำถามเรื่องเหตุผลเบื้องหลัง ให้ใช้ `why` ด้วย
2. Throughput checkpoint เขียนบรรทัดเดียว: `n/a, read-only investigation`
3. ทำผลลัพธ์ตามรูปแบบของ `how` (Overview / Key Concepts / How It Works / Where Things Live / Gotchas) ถ้าเป็นคำถามให้เลือกระหว่างทางเลือก ให้ทำตาราง tradeoff พร้อมคำแนะนำ
4. ขัดเกลาภาษาด้วย `unslop`

**ข้อห้าม:** ไม่เปิด PR และไม่เรียก architect ถ้าพบว่าต้องแก้โค้ด ให้ส่งกลับไป route ใหม่
**Reply:** ผลการสืบสวน ถ้าคำถามคือ "แน่ใจไหม" ต้องให้ความเห็นจริงพร้อมเหตุผล และค้านได้ถ้าโจทย์ตั้งต้นผิด

---

### 6.2 Bug fix
**Ownership:** You own this task. Plan, review, verify.
**ปรัชญา:** ทำแบบวิทยาศาสตร์ โค้ดทุกบรรทัดที่ ship ต้องมีหลักฐานจาก runtime รองรับ ส่วนที่ใส่เผื่อไว้เพราะ "อาจช่วยได้" นับเป็นแค่สมมติฐาน ห้าม ship ถ้าหลักฐานหักล้างสมมติฐานไหน ให้ revert ส่วนที่ทำเพราะสมมติฐานนั้นออกด้วย

1. **Reproduce เอง** บน surface เดียวกับที่เกิดบั๊ก โดยใช้ driver skill ถามผู้ใช้ได้ก็ต่อเมื่อมีเหตุผลเฉพาะว่าเข้าถึง surface นั้นไม่ได้จริง ถ้า reproduce ไม่ได้ ให้สร้าง trigger เอง บีบเงื่อนไขให้แคบลง หรือใส่ instrumentation จนบั๊กเกิดขึ้น
2. **Binary-search หาสาเหตุ** ตั้งสมมติฐานหลายข้อแล้วตัดทิ้งไปทีละข้อ ใช้ `how` กับ `why` ช่วยตั้งสมมติฐาน แต่ละรอบเลือกจุดแบ่งที่ตัดพื้นที่ปัญหาได้มากที่สุด ถ้ายังไม่รู้ state ของโปรแกรม ให้ใส่ log แล้วอ่านขณะที่โปรแกรมรัน ห้ามเดา ต้องยืนยันกลไกที่เหลืออยู่ด้วยหลักฐานจาก runtime
3. **วางแผนการแก้** ถ้าการแก้ข้าม function boundary ให้ใช้ `architect` ก่อน แล้วส่งงานให้ subagent ที่ใช้โมเดลของบทบาท bug-fix (ค่าเริ่มต้นคือโมเดลที่ตัดสินใจเก่งที่สุด) พร้อมขอบเขตที่ชัดเจน
4. **Verify บน surface เดิม** repro เดิมต้องผ่าน ผลแบบ inconclusive หรือทดสอบผิด surface ไม่นับว่าผ่าน unit test แสดงพฤติกรรมของ branch ได้ แต่ไม่ได้พิสูจน์ว่าบั๊กหายแล้ว
5. **เรียง commit** ให้ test ที่ fail ลงก่อนตัวแก้ (TDD) ข้ามได้ถ้า test แพงเกินไป
6. Opening a PR

**Reply:** อะไรพัง, root cause, วิธีแก้ และวิธี verify พร้อมยก output ช่วงที่ fail และช่วงที่ pass มาให้ดู

**หลักออกแบบที่ได้:** ทุกขั้นมี artifact เป็นหลักฐาน (repro, log, test) และกำหนดชัดว่าอะไรไม่นับเป็นหลักฐาน

---

### 6.3 Feature
**Ownership:** You own the design. Plan, review, verify.

1. ใช้ `how` สำรวจระบบส่วนที่จะได้รับผลกระทบ
2. ใช้ `architect` เพื่อสำรวจทางเลือกการออกแบบแบบขนาน
3. **เขียน Throughput checkpoint เป็น todo 4 รายการ** (มิติไหนไม่เกี่ยวให้เขียน `n/a: <reason>`)
   - **Blocking first steps:** งานที่ต้องทำให้เสร็จก่อน fan-out
   - **Independent workstreams:** ไฟล์, service หรือ layer ที่แยกกันชัดเจนทำขนานกันได้ ส่วนที่เขียนร่วมกันต้องทำทีละงาน
   - **Shared mutable state:** ค่าเริ่มต้นคือแยกเป้าหมายออกจากกัน ทำทีละงานเฉพาะเมื่อมี invariant จริง
   - **Smallest safe decomposition:** ถ้าใช้ worker คนเดียวดีที่สุด ต้องบอกเหตุผล
4. **มอบงานเขียนโค้ด** ให้ subagent พร้อมขอบเขตที่ชัด ได้แก่ path ของไฟล์, ชื่อรูปร่างข้อมูลและโครงสร้างที่ใช้จัดมัน (เช่น state machine แทน boolean กระจาย, table/registry แทน if-else) และเกณฑ์ความสำเร็จ
   - ถ้างานทำได้หลายรูปแบบที่ถูกต้องพอกัน **บังคับให้ใช้ `arena`** ข้ามไม่ได้
   - **writer ทุกตัวต้องมี worktree ของตัวเอง** การเขียนห้ามไว้ใน brief ไม่นับว่าเป็นการล็อก
5. Verify บน surface ที่ตรงกับงาน
6. Rebase ให้เป็น commit เล็ก ๆ ที่เรียงลำดับแล้ว
7. ถ้าการออกแบบยังมีข้อโต้แย้ง ให้ใช้ `interrogate` ก่อน ship
8. Opening a PR

**กฎเพิ่มเติม:** งานที่โค้ดผูกกันแน่น (เช่น feature เดียวหรือ migration เดียว) ให้มีเจ้าของคนเดียว แล้วเจ้าของคนนั้น fan-out ภายในเอง ตัวนำจะ fan-out เองเฉพาะงานที่ให้ผลลัพธ์แยกกันได้ เช่น audit หรือการทดลองที่แข่งกัน
**Reply:** สิ่งที่สร้าง, สิ่งที่เลือกและเหตุผล, throughput checkpoint และสิ่งที่ยังต้องตัดสินใจ

---

### 6.4 Refactoring
**Ownership:** You own the contract. The structure changes. The behavior does not.

1. **ตรึงพฤติกรรมเดิมก่อน (pin)** ใช้ `how` เพื่อเข้าใจ contract แล้วเขียน characterization test, snapshot หรือ equivalence harness type check กับ lint ไม่นับว่าเป็นการตรึง
2. **ระบุโครงสร้างที่โค้ดยังขาด** (`model-the-domain`) การปรับโครงสร้างต้องลด branch หรือลด state ที่ไม่ถูกต้อง ไม่ใช่เพิ่ม indirection
3. **ระบุรูปร่างเป้าหมาย** ว่าถ้าสร้างวันนี้ควรมีหน้าตาอย่างไร ถ้าข้าม boundary ให้ใช้ `architect`
4. **ลบก่อนเพิ่ม** ลบโค้ดที่ไม่ใช้แล้ว ยุบ wrapper ที่มีผู้เรียกคนเดียว และ revert งาน cleanup ที่ทำเพราะ "อาจช่วยได้"
5. **ขยับทีละก้าวเล็ก ๆ** ให้ pin ยังผ่านทุกก้าว ถ้าเปลี่ยน API ให้ย้ายผู้เรียกทุกตัวแล้วลบ API เก่าในรอบเดียวกัน ไม่ทำ shim และตรวจทุกการ rename กับไฟล์จริง
6. **พิสูจน์ว่าพฤติกรรมไม่เปลี่ยน** บน artifact จริง เช่น เทียบ output เก่ากับใหม่ หรือ replay baseline
7. **ยืนยันว่าคุ้ม** วัดผลด้วยภาระของคนอ่านโค้ด ถ้าไม่ลดลงเลย ให้ revert
8. เรียง commit เป็น ลบ → ปรับรูป → cleanup แล้ว Opening a PR

**Reply:** โครงสร้างที่เปลี่ยน, pin ที่ใช้, หลักฐานว่าพฤติกรรมเท่าเดิม, ภาระคนอ่านที่ลดลง และสิ่งที่ถูก revert

**หลักออกแบบที่ได้:** มี **ขั้นตอนที่ตัดสินว่างานนี้ควรเก็บไว้หรือไม่** (ขั้น 7) ซึ่งทำให้การ revert เป็นผลลัพธ์ปกติของ workflow ไม่ใช่ความล้มเหลว

---

### 6.5 Prototype
**Ownership:** You own the design decision, not the code. Prototype เป็นเครื่องมือที่ใช้แล้วทิ้ง

Playbook นี้กลับเกณฑ์ปกติ คือเน้นความเร็วมากกว่าความเรียบร้อย ความเข้มงวดอยู่ที่การเลือกการออกแบบที่ถูกด้วยต้นทุนต่ำ

1. **ระบุการตัดสินใจที่ prototype จะช่วยตอบ** ถ้าไม่มีการตัดสินใจให้ตอบ ก็ไม่ต้องทำ prototype ให้ไป Feature
2. รวบรวม reference ถ้าทิศทางยังเปิดกว้าง
3. สร้างใน scratch dir แยกจาก source จริง ใช้ stack ที่เบาที่สุด ไม่ต้องมี test หรือ abstraction
4. ถ้ามีหลายทางเลือก ให้รวมไว้หลัง **switcher ตัวเดียว** และติดป้ายแต่ละ variant
5. Verify ด้วยการสังเกต เช่น screenshot, log เวลา หรือ output การสังเกตคือการทดสอบของ playbook นี้
6. นำเสนอทางเลือก, tradeoff และคำแนะนำ แล้วส่งทิศทางที่เลือกต่อให้ Feature

**จุดสำคัญ:** Prototype ใช้ร่วมกับกฎ "ห้ามถามผู้ใช้ถ้ารันดูคำตอบได้" ถ้าคำถามเป็นข้อเท็จจริงที่สังเกตได้ ให้สร้าง prototype แล้วให้ผลตัดสิน

---

### 6.6 Autonomous run
**Ownership:** You own the exit condition.

1. เขียน **exit condition เป็น predicate ที่ตรวจได้** ก่อนเริ่มรอบแรก เช่น "tests green" หรือ "pixel-diff = 0"
2. เลือกกลไกปลุก ถ้ามี event ให้เฝ้า ให้ใช้ watcher subagent ร่วมกับ heartbeat ยาว ๆ เป็นตัวสำรอง ถ้าไม่มี event ให้ใช้ heartbeat ตามรอบที่ผลลัพธ์มีโอกาสเปลี่ยน
3. แต่ละรอบทำการเปลี่ยนแปลงที่เล็กที่สุดที่หลักฐานรองรับ ตรวจกับ predicate แล้ว commit ถ้าคืบหน้า หรือทิ้งถ้าไม่ช่วย
4. ปัญหาที่เจอระหว่างทางเป็นงานของ agent เอง ให้แก้ใน PR แยก ห้ามรอผู้ใช้ แจ้งผู้ใช้เฉพาะเรื่องที่ย้อนกลับไม่ได้ เรื่องที่เป็นความชอบ หรือทางตันจริง
5. บันทึก checkpoint ทุกรอบด้วย `show-me-your-work`
6. หยุดเมื่อ predicate เป็นจริง **ผลที่ไม่ขยับ (plateau) ไม่ใช่เหตุให้หยุด** ให้เปลี่ยนวิธี และ **ห้ามลดเกณฑ์ predicate เพื่อประกาศว่าสำเร็จ**

---

### 6.7 figure-it-out (ออกแบบ playbook ใหม่สำหรับงานที่ไม่มี playbook รองรับ)
ผลลัพธ์แรกของ playbook นี้คือ **workflow** ยังไม่ใช่โค้ด

**Phase A: Frame**
- เขียน definition of done เป็น predicate ที่พิสูจน์ได้ว่าผิด
- ประเมินขอบเขตเป็นตัวเลข (จำนวนหน่วยงาน, effort, สิ่งที่ block)
- เลือกระดับความเข้มงวด โดยเอียงไปทางสูง งานที่ย้อนกลับไม่ได้ต้องเข้มงวดมากขึ้น และความเข้มงวดหมายถึง gate กับ artifact ไม่ใช่ "พยายามให้มากขึ้น"
- นำเสนอ framing ก่อนเริ่มงานยาว โดยมี checkpoint หนึ่งครั้ง

**Phase B: Design the workflow**
- แตกงานเป็นหน่วยเล็กที่ land ได้อิสระ แล้ว **เรียงจากสิ่งที่ไม่รู้และเสี่ยงที่สุดก่อน**
- **สร้าง verification harness ก่อนเริ่มงาน** และเก็บ baseline จากสภาพก่อนเปลี่ยน
- การตัดสินใจที่ย้อนกลับไม่ได้ให้ใช้ `architect` งานเชิงกลไกไม่ต้องใช้
- fan-out ตามรอยต่อของงานเท่านั้น และ writer แต่ละตัวต้องมี worktree ของตัวเอง
- เขียนรายการ phase ไว้ให้คนตรวจได้

**Phase C: Run the loop** มองทุกหน่วยงานเป็นการทดลอง คือตั้งสมมติฐาน → เปลี่ยนให้น้อยที่สุด → วัด → เก็บหรือ revert
- ตรวจจาก artifact เท่านั้น ไม่เชื่อรายงานที่ agent เขียนเอง
- ถ้าผ่านง่ายผิดปกติ ให้สงสัยวิธีสังเกตก่อน
- งานที่มอบให้คนอื่นต้องมี judge ถ้า worker โกง gate ให้รีเซ็ตแล้วทำ contract ให้แข็งขึ้น
- verdict มี 3 ค่าคือ VERIFIED / NOT VERIFIED / INCONCLUSIVE

**Phase D:** เก็บ decision trail
**Phase E:** Verify ทั้งหมดกับ predicate บนของจริง และเปลี่ยนการแก้ไขที่เกิดซ้ำให้เป็น gate

---

### 6.8 Orchestrate (โปรแกรมงานหลายวัน)
**Ownership:** You own the program, never the code. Author briefs, drain the queue, keep the frontier green, decide.

**กฎหลัก 3 ข้อ**
1. งานที่ worker ทำเสร็จเป็น event ในคิว ไม่ใช่สิ่งที่ขัดจังหวะงานอื่น
2. ทุกครั้งที่ spawn หรือ resume ต้องแนบ standing orders แบบคำต่อคำ
3. **The brief is the product** เพราะ worker ถามกลับไม่ได้ brief ที่คลุมเครือจึงพังเงียบ ๆ

**Template ของ brief**
```
GOAL         หนึ่งประโยค คนแปลกหน้าที่ไม่เห็นแชตอ่านแล้วทำได้
SCOPE        path ที่เขียนได้ / ห้ามเขียน / worktree หรือ branch ของตัวเอง
CONTEXT      pointer ไปยังไฟล์และ PR, รายงานจาก upstream แปะเต็ม
ACCEPTANCE   เกณฑ์ที่ตรวจได้ บรรทัดละข้อ
VERIFY       คำสั่งที่ต้องรันแบบตรงตัว + gotcha ที่รู้
TIMEBOX      เพดานเวลา หมดเวลาให้คืนผลบางส่วนแล้วหยุด
FORBIDDEN    ห้าม rebase, ห้าม force-push, ห้ามแก้นอก scope ฯลฯ
REPORT       status, branch, head SHA, PR, verdict, สิ่งที่รันจริง, ส่วนที่เบี่ยงจากแผน
STANDING     preferences.md แปะแบบคำต่อคำ
```
- ปรับขนาด brief ให้เท่ากับงาน งานคำสั่งเดียวใช้ย่อหน้าเดียวพอ
- **ถ้าเติมช่องไหนไม่ได้ ห้าม spawn** เพราะแปลว่ายังกำหนดขอบเขตของงานนั้นไม่เสร็จ

**ขั้นตอน**
1. **Frame:** เขียน predicate ที่นับได้ เช่น "126 units merged" ถ้า agent ตัวเดียวทำเสร็จได้ ให้เปลี่ยนไปใช้ Autonomous run และหยุดสร้างงานใหม่เมื่อใช้งบเวลาไปประมาณ 70%
2. **Install runtime:** รัน `orch init`, เขียน standing orders และ seed frontier
3. **Pilot:** ส่งงานหนึ่งหน่วยผ่านทุกขั้นก่อน เพื่อหาข้อผิดพลาดของ template ในขณะที่ยังเสียแค่ agent ตัวเดียว
4. **Scale:** ใช้หน้าต่าง worker แบบ rolling (ประมาณ 10 ตัว) ไม่ทำเป็น batch ที่ต้องรอตัวช้าที่สุด
5. **Drain:** ประมวลผลคิวทุกครั้งที่ถึงจุด drain
6. **Land:** land ต่อเนื่องไปพร้อมกับงาน ไม่รอไว้ทำตอนท้าย
7. **Close:** ตรวจว่าทุก agent อยู่ในสถานะสุดท้ายแล้ว และยืนยัน predicate บนของจริง

**Store (ไฟล์สถานะนอก session):** `preferences.md`, `overview.md`, `units.tsv`, `frontier.json`, `ledger.tsv`, `inbox/`, `gates.md`, `decisions.tsv`, `status.md` กฎสำคัญคือ **ทุกไฟล์มี writer เพียงคนเดียว** และ `status.md` ต้องสร้างจากตารางเสมอ ห้ามเขียนเอง

**ความล้มเหลวและการกู้คืน**
- ห้าม resume agent เพื่อเช็กสถานะ ให้ตรวจแบบอ่านอย่างเดียวจาก ledger, `gh` หรือ branch แทน
- retry ตามประเภทความล้มเหลว
  - งานเกินเพดานหรือ OOM → ลด scope
  - network → retry เหมือนเดิม
  - tool error → เปลี่ยนโมเดล
  - ไม่ทราบสาเหตุ → retry 1 ครั้ง
  - retry ครบ 2 ครั้งแล้วยังไม่ผ่าน → ทิ้งงานนั้น
- ถ้า agent ที่คิดว่าตายแล้วกลับมาช้า ต้องตรวจผลกับ ledger ก่อน ห้าม merge โดยไม่ตรวจ
- ถ้าทั้งระบบเริ่มให้ผลขยะ ให้เขียน stop line ไว้บนสุดของ standing orders

**เรื่องที่ต้องถึงมนุษย์:** งานที่ย้อนกลับไม่ได้, การตัดสินใจเชิงผลิตภัณฑ์, standing order ที่ขัดกับความจริง และทางตันระดับโปรแกรม
**เรื่องที่ไม่ต้องถึงมนุษย์:** retry, CI flake, format, และคำถามว่า "ทำต่อไหม"

---

### 6.9 Opening a PR (ขั้นตอนท้ายที่ใช้ร่วมกัน)
- **Worktree:** ทำงานจาก worktree ที่แตกจาก main ก่อน commit ต้องหยุด agent ทุกตัวที่ใช้ worktree นั้น แล้วรัน `git status`
- **Commits:** commit บ่อย ๆ แล้ว rebase ให้เป็น commit เล็กที่เรียงลำดับดี แต่ละ commit ควรแยกเป็น PR ได้
- **ก่อน PR:** รัน `deslop` → `no-comments` → `technical-writing` → `unslop`
- **Title:** ใช้ Conventional Commits `type(scope): subject`
- **Description:** เขียนให้ reviewer อ่านจบได้ในหนึ่งนาที แบ่งเป็นส่วน `## Why`, `## What changed`, `## Scope`, `## Tradeoffs`, `## Blast Radius`, `## Verification`
- **Size:** เลือก PR เล็ก 5 ตัวดีกว่า PR ใหญ่ 1 ตัว และใช้ stack
- เปิดเป็น ready ไม่เปิดเป็น draft และการเปิด PR ไม่ได้เริ่ม babysit อัตโนมัติ

---

## 7. สกิล fan-out ทีละตัวแบบละเอียด

ทุกสกิลมีโครงเดียวกัน คือ **เปิด todolist ตาม phase → Frame → Fan out (spawn ทุกตัวใน message เดียว, `run_in_background: true`) → รวมผลหรือตัดสิน → Verify → Output ที่มีรูปแบบตายตัว**

### 7.1 `how`: Explorer → Explainer
1. **ประเมินความซับซ้อน** ถ้าโจทย์แคบ ใช้ explainer ตัวเดียว ถ้าข้ามหลายไฟล์หรือหลาย service ใช้ explorer 2-4 ตัว ถ้าไม่แน่ใจให้เลือกแบบง่าย
2. (กรณีซับซ้อน) แบ่งโจทย์เป็น 2-4 มุมที่ไม่ทับกัน แล้ว spawn explorer แบบอ่านอย่างเดียว
3. Spawn explainer ตัวเดียวเพื่อสังเคราะห์ผล
4. นำเสนอผล แก้ภาษาได้เล็กน้อย แต่ห้ามเขียนใหม่

**รูปแบบผลลัพธ์:** Overview / Key Concepts / How It Works / Where Things Live / Gotchas

### 7.2 `why`: Investigator ต่อแหล่งหลักฐาน → Synthesizer
1. เข้าใจเป้าหมายและคำถาม ถ้ากำกวมให้เดาจากบริบทแล้วบอกผู้ใช้ว่าตีความอย่างไร
2. **ทำ code anchor** ได้แก่ path, ช่วงบรรทัด, symbol, commit และหมายเลข PR (ใช้ `git blame`, `git log --follow`, `gh pr view`)
3. **ค้นหา MCP ที่มีอยู่** แล้วจับคู่กับหลักฐาน 7 ประเภท คือ source control, ticket, docs, chat, observability, error tracking และ analytics
4. Spawn investigator **ประเภทละหนึ่งตัว** ห้ามให้ตัวเดียวดูหลายแหล่ง การข้ามประเภทไหนต้องเขียนเหตุผลไว้ใน Sources Consulted
5. Synthesizer ใช้กรอบ `epistemics.md` เพื่อแยกระดับความมั่นใจ
6. นำเสนอผล **ห้ามแก้ภาษาที่บอกระดับความมั่นใจ**

**รูปแบบผลลัพธ์:** What We Found / What We Can Reasonably Infer / Competing Hypotheses / What We Don't Know / Sources Consulted (รวมแหล่งที่ไม่พบอะไร) / Confidence Summary ถ้าคำถามนำไปสู่การแก้โค้ด ให้แปลงผลเป็น Preserve / Change / Avoid / Risk

**หลักออกแบบที่ได้:** **ผลที่ว่างเปล่าก็เป็นหลักฐาน** ต้องบันทึกว่าค้นแล้วไม่พบ ห้ามข้ามแบบเงียบ ๆ

### 7.3 `arena`: แข่ง → ตัดสินไขว้ → เลือกชิ้นหลัก → นำส่วนดีมาเสริม
1. **Frame:** กำหนด artifact, สร้าง rubric 3-6 ข้อที่ให้คะแนนได้ (candidate ไม่เห็น rubric), เลือก runner จาก panel 3 โมเดล และกำหนด output path แยกให้แต่ละตัว
2. **Fan out:** spawn N ตัวใน message เดียว แต่ละตัวต้องส่ง artifact และ rationale ที่บอกว่าพิจารณาทางเลือกอะไรและปฏิเสธอะไร ถ้ามีตัวหลุด ให้ทำต่อกับ N-1 ตัว
3. **Cross-judge:** judge หนึ่งตัวที่ใช้โมเดลต่างตระกูลจากตัวนำ ให้คะแนนตาม rubric
4. **Pick:** ตัวนำอ่านทุกชิ้นจนจบ ให้คะแนนทีละเกณฑ์ แล้วเทียบกับ judge ถ้าเลือกตรงกันถือว่ายืนยัน ถ้าไม่ตรงกันให้อ่าน rationale ของทั้งคู่ก่อนตัดสิน เกณฑ์เลือกคือชิ้นที่คนดูแลต่อขยายได้ง่ายที่สุด
5. **Graft:** นำส่วนที่ดีจากชิ้นอื่นมาเสริม (ปกติ 1-2 อย่างต่อชิ้น) ด้วยการเขียนใหม่ให้เข้ากับชิ้นหลัก ไม่ใช่วางลงไปตรง ๆ ถ้าทุกชิ้นออกมาเหมือนกัน แปลว่าเห็นตรงกัน ship ได้เลย ถ้าต่างกันมาก แปลว่าโจทย์ไม่ชัด ให้เขียนโจทย์ใหม่ ห้ามเอาผลมาเฉลี่ย
6. **Verify:** ถ้าพบปัญหา ให้กลับไปที่ Frame หรือ Graft

**Output:** artifact หนึ่งชิ้นพร้อม synthesis note ที่บอกชิ้นหลัก, ส่วนที่นำมาเสริม, สิ่งที่ปฏิเสธ, ตัวที่หลุด และผล verify

### 7.4 `architect`: ออกแบบก่อน implement
1. **Ground:** ใช้ `how` (และ `why` ถ้ากำลังเปลี่ยน ownership หรือ layering) การแค่ระบุชื่อไฟล์ไม่นับว่าเข้าใจระบบแล้ว
2. **Sketch:** ใช้ `arena` โดยให้แต่ละ runner ร่าง types, signatures และ module ที่ body ยังเป็น `not implemented`
   - ต้องมีอย่างน้อย 2 แบบที่โครงสร้างต่างกันจริง
   - คัดทิ้งด้วย `design-red-flags.md` (shallow module, information leakage, pass-through method)
   - เลือกแบบที่ interface เล็กแต่ซ่อนความซับซ้อนได้มาก
3. **Agree:** ค่าเริ่มต้นคือไม่ต้องรอผู้ใช้ จะหยุดให้ผู้ใช้ดูก็ต่อเมื่อผู้ใช้ขอเอง
4. **Implement:** ใช้ sketch เป็น contract ถ้าทำจริงแล้วต้องเบี่ยงจาก sketch ให้รายงาน ห้ามซึมซับไว้เงียบ ๆ และต้องอัปเดต sketch ก่อนส่งงานต่อให้ worker คนถัดไป
5. **Scrap:** ถ้าเจอสัญญาณซ้ำ ๆ ให้ทิ้ง sketch แล้วออกแบบใหม่ สัญญาณคือ workaround แบบเดียวกันโผล่หลายที่, type ต้องใช้ `any` หรือ cast, หรือ "ต้องมี lock" ทั้งที่ sketch บอกว่าไม่มี state ร่วม การออกแบบใหม่ต้องเล็กกว่าเดิมก่อนจะขยาย

### 7.5 `swarm`: Worker ขนาน → รายงานเดียว
1. **Frame:** กำหนด done predicate และเลือกรูปแบบระหว่างแบ่งเป็นชิ้น (partition), แข่ง (race) หรือผสม ถ้าแข่ง ต้องประกาศกฎเลือกก่อน (`first pass` / `rank all` / `best-of`) แล้วกำหนด N และโมเดล ถ้างานเป็นการวัดผล ต้องระบุ SHA และวิธีวัด
2. **Fan out:** brief แต่ละตัวต้องอ่านจบได้ในตัว ได้แก่ goal, scope, slice, วิธี verify และรูปแบบรายงาน ผลมีสถานะ `PASS` / `ISSUES` / `BLOCKED` พร้อมหลักฐาน และต้องรายงานทุกปัญหาที่พิสูจน์ได้ ไม่ใช่แค่ปัญหาแรก
3. **Aggregate:** ถ้าผลไม่มี SHA หรือวิธีวัดตามที่ brief กำหนด ให้ทิ้งแล้ว spawn ใหม่ครั้งเดียว ถ้ายังพลาดให้บันทึกเป็นช่องว่าง (gap) ซึ่ง **ไม่นับว่าผ่าน**
4. **Report:** ส่งตารางผล, ปัญหาบรรทัดละข้อ และ gap ห้ามแปะผลดิบของ worker

### 7.6 `interrogate`: รีวิวแบบหลายโมเดลที่ตั้งใจหาจุดผิด
1. กำหนดขอบเขตที่จะรีวิว (diff หรือไฟล์)
2. **เขียน intent เป็นหนึ่งย่อหน้า** ถ้าไม่แน่ใจให้ถามผู้ใช้
3. Spawn reviewer ตามจำนวนโมเดลใน panel โดยใช้ **prompt เดียวกันทุกตัว** (template + rubric + code-quality lens) ความหลากหลายมาจากการใช้หลายโมเดล ไม่ใช่ persona
4. **Synthesize:** ปัญหาที่ 2 โมเดลขึ้นไปพบตรงกันถือว่าน่าเชื่อถือที่สุด รวมปัญหาที่ซ้ำกัน และบันทึกจุดที่โมเดลเห็นต่างกัน
5. **Lead judgment:** แบ่งเป็น Act on / Consider / Noted / Dismissed พร้อมเหตุผล

**ข้อห้าม:** ห้ามแก้โค้ดอัตโนมัติ ผลลัพธ์คือ verdict
**รายละเอียดใน prompt template:** "Do NOT question the intent", "If you find nothing wrong, say no findings", "An empty review is a valid outcome" ทั้งหมดนี้ช่วยกันไม่ให้ reviewer แต่งปัญหาขึ้นมาเอง

### 7.7 `reflect`: ระบบเรียนรู้จากตัวเอง
1. หา transcript ของ session ปัจจุบันด้วยสคริปต์ `find-transcript.mjs` (ไม่ข้ามไปดู workspace อื่น)
2. Spawn reviewer 3 มุมมองคู่ขนาน ได้แก่ Judgment, Tooling และ Divergent reviewer ห้ามเขียนไฟล์ ตัวนำเป็นผู้แก้เอง
3. Synthesizer แบ่งผลเป็น Accepted / Rejected / Backlog
4. **Structural enforcement check:** ข้อไหนบังคับด้วย lint หรือ script ได้ ให้ย้ายจาก Accepted ไป Backlog เพราะควรแก้ด้วยโครงสร้าง ไม่ใช่แก้ข้อความ

---

## 8. สัญญาการมอบหมายงาน (Delegation Contract)

### 8.1 ค่าเริ่มต้นของการเรียก `Agent` ทุกครั้ง
- `run_in_background: true`
- ให้สิทธิ์เครื่องมือเต็ม ห้ามเลือก subagent type ที่ตัด MCP ทิ้ง
- **ส่ง path ของไฟล์ ไม่ยัดเนื้อหาเข้าไปใน prompt**
- กำหนดโมเดลตามบทบาท และเลือกตามความยากของงาน
  - งานยากที่สุด (ออกแบบข้ามระบบ, concurrency, อัลกอริทึมซับซ้อน) → โมเดลที่ตัดสินใจเก่งที่สุด
  - งานเชิงกลไกง่าย ๆ → โมเดลเร็ว
  - งานอื่น ๆ → โมเดลค่าเริ่มต้น

### 8.2 ความรับผิดชอบ
- **ตัวนำรับผิดชอบงานของ subagent ทั้งหมด** ต้องอ่าน diff เองและเขียนสรุปเอง
- second opinion คือการส่ง prompt เดิมให้โมเดลอื่น ถ้าผลตรงกัน ถือเป็นสัญญาณที่น่าเชื่อถือ

### 8.3 ใช้ subagent ตัวใหม่เป็นค่าเริ่มต้น
- งานใหม่ (รอบแก้, follow-up, retry หรืองานถัดไปในคิว) ให้ส่ง **agent ตัวใหม่พร้อมขอบเขตที่รวมทุกอย่างแล้ว** คือ brief เดิม, คำสั่งที่เพิ่มทีหลัง และรายงานกับ branch ของ agent ตัวก่อน
- resume agent เดิมได้เฉพาะเมื่อ state สำคัญอยู่ใน agent นั้นและย้ายออกมายาก เช่น checkout ที่ยังไม่ commit หรือ dev server ที่รันอยู่
- **เหตุผล:** การ resume agent ต่อกันหลายรอบทำให้คำสั่งตกหล่นโดยไม่มีใครรู้
- **ต้องหยุด agent เก่าและยืนยันว่าหยุดแล้ว** สถานะ `completed` แปลว่าได้รับแจ้งว่าเสร็จ ไม่ได้แปลว่า process จบแล้ว สัญญาณว่า agent ยังรันอยู่คือสิ่งที่มันอ้างถึง working tree ไม่ตรงกับ `git status`

### 8.4 การแยกพื้นที่
- writer ทุกตัวต้องมี worktree หรือ branch ของตัวเอง
- ห้ามเขียนไฟล์หรือรัน test ใน worktree ที่ subagent ยังใช้อยู่
- ลูกของ subagent ไม่ได้รับ brief ของพ่อ คำสั่งแบบ "อ่านอย่างเดียว" จึงไม่ส่งต่อไปถึง

---

## 9. ระบบการตรวจสอบ (Verification)

| กฎ | ที่มา |
|---|---|
| ตรวจกับ artifact จริง ไม่ใช่ตัวแทน และ "compile ผ่าน" ไม่นับ | `principle-prove-it-works` |
| ผลแบบ inconclusive หรือทดสอบผิด surface ไม่นับว่าผ่าน | Bug fix, Feature |
| verdict มี 3 ค่า: VERIFIED / NOT VERIFIED / INCONCLUSIVE | figure-it-out |
| ผลของ worker: PASS / ISSUES / BLOCKED พร้อมหลักฐาน | swarm |
| ledger ใช้ PR + head SHA เป็น key และ SHA ใหม่ทำให้ผลเดิมใช้ไม่ได้ | Orchestrate |
| CI เขียวเป็นข้อมูลประกอบ verdict ไม่ใช่ verdict | Orchestrate |
| ผู้ตรวจควรใช้โมเดลต่างตระกูลจากผู้ทำ | Orchestrate |
| ถ้าผ่านง่ายผิดปกติ ให้สงสัยวิธีวัดก่อน | figure-it-out |
| ตัวเลขที่วัดได้ต้องอธิบายได้ว่าอะไรจำกัดมันอยู่ | `principle-explain-the-number` |
| ปรับระดับการ verify ให้เท่ากับงาน ถ้า verifier แค่รันคำสั่งเดียวซ้ำ ถือเป็นพิธีกรรม | Orchestrate |

**กฎการเขียนคำตอบที่เกี่ยวกับการ verify**
- ทุกข้ออ้างต้องติดป้ายว่า **วัดมา / อนุมาน / เดา** ไว้ในประโยคเดียวกัน
- ห้ามแต่งลิงก์ ให้ลิงก์เฉพาะ artifact ที่ได้อ่านหรือสร้างใน session นี้
- ห้ามส่งงานตรวจที่ agent รันเองได้ไปให้ผู้ใช้ทำ

---

## 10. ระดับอิสระในการตัดสินใจ (Autonomy)

| ระดับ | สิ่งที่ครอบคลุม |
|---|---|
| **ทำได้เลย** | งานที่ย้อนกลับได้ และ external action อย่างโพสต์ในแชตทีม อัปเดต ticket หรือเริ่ม eval |
| **ต้องหยุดถามเสมอ** | การเขียนที่ย้อนกลับไม่ได้ เช่น force-push branch ที่ใช้ร่วมกัน, deploy, ลบข้อมูล หรือส่งข้อความถึงลูกค้า |
| **Session override** | ถ้าผู้ใช้บอกว่า "ไม่ต้องหยุด" หรือ "ไปนอนแล้ว" ให้ทำต่อ |

### ขั้นตอนตัดสินใจก่อนถามผู้ใช้
1. แยกก่อนว่าคำถามนั้นรันดูคำตอบได้ไหม (พฤติกรรม, เวลา, layout, output)
2. ถ้ารันได้ ให้ทำ Prototype แล้วให้ผลตัดสิน
3. ถ้าเป็นงาน Investigation ให้ตอบจากหลักฐาน
4. ถามผู้ใช้เฉพาะเรื่องที่เป็นความชอบหรือการตัดสินใจเชิงผลิตภัณฑ์จริง ๆ
5. ถ้าผู้ใช้ให้อิสระเต็มที่ ให้เลือกค่าเริ่มต้นเอง แล้วรายงานพร้อมบอกว่าผู้ใช้สั่งเปลี่ยนเป็นอย่างอื่นได้ ห้ามให้ token ย่อให้ผู้ใช้พิมพ์ตอบกลับ

**"No is an acceptable answer."** agent ต้องค้านได้เมื่อเห็นว่าไม่ควรทำ เพื่อไม่ให้กลายเป็นการเออออตามผู้ใช้

---

## 11. ความต่อเนื่อง: หยุด รับช่วง และ decision trail

### 11.1 Pause safely
1. หยุดที่ขอบเขตที่ปลอดภัย ทำขั้นที่ค้างให้จบหรือถอยออก และยกเลิก subagent ที่ซ้อนอยู่
2. ห้ามทำสิ่งที่ย้อนกลับไม่ได้เพื่อจะหยุด
3. commit งานที่ยังไม่บันทึกเป็น `wip:` หนึ่ง commit
4. เขียน resume note ไว้นอก context ได้แก่ intent, ความคืบหน้า, สิ่งที่ verify แล้ว, ขั้นถัดไป, ไฟล์สำคัญ และ gotcha
5. publish ผ่าน `resume.mjs` ซึ่งตรวจลิงก์ก่อนอัปเดต pointer แบบ atomic แล้วลองอ่านกลับเพื่อยืนยัน

### 11.2 Session pickup
1. อ่าน checkpoint ก่อน ถ้าไม่มี ค่อยไปดู transcript (ใช้ subagent อ่าน เพื่อประหยัด context)
2. สร้างสถานะการทำงานกลับขึ้นมา ได้แก่ branch, สิ่งที่ land แล้ว และ todo
3. เทียบสิ่งที่เสร็จแล้วกับสิ่งที่ยังค้าง **ห้ามทำซ้ำงานที่เสร็จแล้ว**
4. route งานที่เหลือไปยัง playbook ที่เหมาะ
5. verify สิ่งที่รับช่วงมาบนของจริง รายงานที่ agent ตัวก่อนบอกว่าผ่าน ไม่ถือเป็นหลักฐาน

### 11.3 show-me-your-work (decision trail)
ใช้ TSV ไฟล์เดียว แถวละหนึ่งการตัดสินใจ:
```
ts	phase	decision	why	evidence	result
```
- เขียนแต่ละ cell บรรทัดเดียว evidence เป็น pointer (SHA, PR, `file:line`) ไม่ใช่ข้อความยาว
- result เช่น `tests green`, `reverted`, `INCONCLUSIVE`, `open`
- เก็บไว้ในเครื่องเป็นค่าเริ่มต้น และ commit เมื่อ reviewer ต้องใช้เพื่อเชื่อผลงาน

---

## 12. การบังคับด้วยโครงสร้างแทนข้อความ

**Principle:** `principle-encode-lessons-in-structure`

### ขั้นตอน
1. ถ้ารู้ตัวว่ากำลังเขียนคำสั่งเดิมเป็นครั้งที่สอง ให้ถามว่าทำเป็น lint, metadata flag, runtime check หรือ script ได้ไหม
2. ถ้าได้ ให้ทำแล้ว **ลบคำสั่งที่เป็นข้อความทิ้ง**
3. ถ้าไม่ได้ (ต้องใช้วิจารณญาณ) ให้ทำคำสั่งให้เด่นขึ้น และใส่ตัวอย่างของความผิดพลาด

### ลำดับความแรงของกลไก (แรง → อ่อน)
```
type ที่ทำให้ state ผิดเกิดขึ้นไม่ได้
  → lint / banned API ที่ทำให้ CI fail
    → helper กลาง (canonical)
      → runtime check
        → ข้อความในคำสั่ง
```
**เหตุผล:** agent มักลอกแบบสิ่งที่มีอยู่แล้วในโค้ด ถ้าใช้กลไกที่อ่อน มันจะกลายเป็นแบบที่ถูกลอกต่อ

### ตัวอย่างใน pstack
| ปัญหา | กลไก |
|---|---|
| ชื่อโมเดลกระจายอยู่หลายไฟล์ | `models.json` เป็นแหล่งเดียว และ `generate.mjs` stamp ลงทุก skill โดย CI fail ถ้ามีสำเนาไม่ตรง |
| project playbook อ้างถึงข้อความที่ถูกแก้ไปแล้ว | `check-playbooks.mjs` |
| ไฟล์แผนผิดโครงหรือภาษาไม่ผ่าน (ตรวจหัวข้อ, 10 live lanes, perf 4 ช่อง, long dash, colon) | `check-plan.mjs` (รายละเอียดใน [`PSTACK-DEEP-DIVE-TH.md`](PSTACK-DEEP-DIVE-TH.md)) |
| สถานะ orchestrate | `orch` CLI ที่สั่งหนึ่งคำสั่งได้ผลหนึ่งบรรทัด และทุกไฟล์มี writer คนเดียว |
| checkpoint ที่ลิงก์เสีย | `resume.mjs` ตรวจก่อน publish |
| layout ของ plugin | invariants ใน `generate.mjs` ซึ่งมี test พิสูจน์ว่า fail ได้จริง |

### วงจรการเรียนรู้
- **เก็บทุกการแก้ไข** เมื่อคนเข้ามาแทรกหรือ test fail ให้ตัดสินว่าเป็นเรื่องครั้งเดียวหรือเป็นแบบแผน
- **ส่งไปยังชั้นที่ถูก** เรื่องครั้งเดียว → note / เรื่องที่เกิดซ้ำ → skill หรือ lint / ปัญหาเชิงระบบ → principle
- **ปิดวงจร** แก้ทันที หรือสร้าง todo ที่เป็นรูปธรรม คำว่า "จะจำไว้" ไม่นับ

---

## 13. การเขียน prompt และ skill

### 13.1 Frontmatter `description` คือเงื่อนไขการเรียกใช้
เขียนว่า **ใช้เมื่อไร** และใส่คำที่ผู้ใช้น่าจะพิมพ์ เช่น
> `how`: "Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions... Use why for motivation."

ควรบอกด้วยว่า **อะไรไม่ใช่งานของ skill นี้** และให้ไปใช้ skill ไหนแทน

### 13.2 แยก prompt ของลูกทีมไว้ใน `references/`
- `interrogate/references/reviewer-prompt.md` ใช้ placeholder อย่าง `{INTENT}`, `{DIFF_OR_FILES}`, `{RUBRIC_CONTENTS}`
- กำหนดรูปแบบผลลัพธ์ตายตัว (severity / finding / evidence / suggestion)
- มีส่วน "What Makes a Good Finding" และ "What to Avoid"
- **อนุญาตให้ไม่มีผลลัพธ์ได้** ("An empty review is a valid outcome")

### 13.3 กฎการเขียน skill (`playbooks/authoring-a-skill.md`)
- **"When in doubt, delete. Keep only prose that changes a decision."** คือเก็บไว้เฉพาะข้อความที่เปลี่ยนการตัดสินใจของ agent
- สั่งให้ทำโดยไม่ต้องอธิบายเหตุผล เว้นแต่กฎจะเข้าใจผิดได้ถ้าไม่มีเหตุผลกำกับ
- ปรับน้ำเสียงให้เท่ากับขอบเขตของงาน
- อ้างถึงแหล่งเชิงโครงสร้าง (types, README, config) แทนการเขียนซ้ำ
- อ้างถึง skill อื่นด้วย path ห้ามเขียนเนื้อหาซ้ำ
- ถ้าเจอ workflow เดิมซ้ำแต่ยังไม่มี skill รองรับ ให้เสนอ skill ใหม่
- ขั้นตอน: เขียน → ตรวจ frontmatter, ไฟล์ที่อ้างถึง และลิงก์ → ทำ test case ถ้า skill มีโครงสร้าง → PR

### 13.4 กฎการเขียนคำตอบ
- ประโยคสั้น หนึ่งประโยคหนึ่งความคิด
- ไม่ใช้ em-dash และไม่ใช้ colon เชื่อมกลางประโยค
- การเขียนสั้นไม่ใช่ข้ออ้างให้ตัดเนื้อหาที่ playbook กำหนด
- เริ่มจากผลกระทบต่อผู้ใช้งานและคนดูแลโค้ด ก่อนลงรายละเอียดการ implement
- comment ในโค้ดเก็บไว้เฉพาะ "ทำไม" ที่โค้ดบอกเองไม่ได้

---

## 14. Checklist และ Template สำหรับออกแบบ workflow ของคุณ

### 14.1 Checklist ออกแบบ (ข้อเสนอ)

**การเข้าระบบ**
- [ ] เกณฑ์การเข้า workflow วัดได้ (จำนวนไฟล์, ประเภทงาน)
- [ ] กำหนดไว้ว่างานแบบไหนไม่ต้องเข้า
- [ ] มีสวิตช์ปิด และฉีดกฎซ้ำหลัง compact

**Router**
- [ ] มีดัชนี playbook พร้อมเงื่อนไขว่าใช้เมื่อไร
- [ ] มีทางออกเมื่อไม่มี playbook ไหนเข้ากัน (แบบ figure-it-out)
- [ ] กฎสำคัญเขียนเป็นคู่ trigger → action

**Playbook**
- [ ] มี ownership line บรรทัดเดียว
- [ ] ระบุขอบเขตและทางออกไปยัง playbook อื่น
- [ ] ขั้นตอนมีหมายเลขและตรวจได้
- [ ] มีกฎ `skip: <reason>`
- [ ] ระบุว่าอะไรไม่นับว่าผ่าน
- [ ] มี Reply spec

**Delegation**
- [ ] brief อ่านจบได้ในตัว (GOAL / SCOPE / ACCEPTANCE / VERIFY / REPORT)
- [ ] ส่ง path ไม่ยัดเนื้อหาเข้า prompt
- [ ] ใช้ agent ตัวใหม่ทุกรอบ และหยุดตัวเก่าก่อน
- [ ] writer แต่ละตัวมีพื้นที่ของตัวเอง
- [ ] เลือกโมเดลตามบทบาทและความยาก

**Fan-out**
- [ ] spawn ทุกตัวใน message เดียว และรันเบื้องหลัง
- [ ] มี rubric หรือกฎการเลือกก่อน fan-out
- [ ] รองรับกรณีมีตัวหลุด (N-1)
- [ ] ผลต่างกันมาก → เขียนโจทย์ใหม่ ห้ามเฉลี่ย

**Verification**
- [ ] สถานะผลลัพธ์มีชุดคำชัดเจน และ inconclusive ไม่นับว่าผ่าน
- [ ] ผู้ตรวจแยกจากผู้ทำ และใช้โมเดลต่างตระกูลถ้าทำได้
- [ ] ข้ออ้างติดป้าย วัดมา / อนุมาน / เดา

**Autonomy และความต่อเนื่อง**
- [ ] แยกงานที่ย้อนกลับได้กับงานที่ย้อนกลับไม่ได้ชัดเจน
- [ ] มีขั้นตอนตัดสินใจก่อนถามผู้ใช้
- [ ] มี decision trail, pause และ pickup

**การพัฒนาตัวเอง**
- [ ] ค่าที่ใช้หลายที่มาจากแหล่งเดียว และมี generator หรือ CI ตรวจ
- [ ] มีวงจรเปลี่ยนความผิดพลาดซ้ำให้เป็น lint หรือ script (แบบ reflect)

### 14.2 Template: Playbook (ข้อเสนอ)
```markdown
### <ชื่องาน>

**You own <สิ่งที่ต้องปกป้อง>. <กริยา 2-3 คำ>.**

ใช้เมื่อ <เงื่อนไข> ไม่ใช่ <งานที่คล้ายแต่ไม่ใช่> (ไปใช้ <playbook อื่น>)

1. <Ground: ทำความเข้าใจระบบ / reproduce / ตรึงพฤติกรรม>
2. <Design: ระบุรูปร่างข้อมูล / ออกแบบทางเลือก>
3. <Plan: throughput checkpoint หรือ n/a: <reason>>
4. <Delegate: ส่งให้ subagent พร้อม brief>
5. <Verify: บน surface จริง; inconclusive ไม่นับ>
6. <Keep-or-revert: งานนี้คุ้มที่จะเก็บไหม>
7. <Deliver: ขั้นตอนท้ายมาตรฐาน>

**Reply:** <รายการสิ่งที่ต้องมีในคำตอบ>
```

### 14.3 Template: Brief สำหรับ subagent (ดัดแปลงจาก Orchestrate)
```
GOAL         <หนึ่งประโยค>
SCOPE        เขียนได้: <paths> / ห้ามแตะ: <paths> / worktree: <path>
CONTEXT      อ่าน: <file paths>  ผลจากงานก่อนหน้า: <แปะเต็ม>
ACCEPTANCE   - <เกณฑ์ 1>
             - <เกณฑ์ 2>
VERIFY       <คำสั่งที่ต้องรันแบบตรงตัว>
TIMEBOX      <เวลา>; หมดเวลาให้คืนผลบางส่วนแล้วหยุด
FORBIDDEN    <สิ่งที่ห้ามทำ>
REPORT       PASS | ISSUES | BLOCKED + หลักฐาน + สิ่งที่รันจริง + จุดที่เบี่ยงจากแผน
```

### 14.4 Template: สกิล fan-out (ข้อเสนอ)
```markdown
---
name: <ชื่อ>
description: "Use for <วลีที่ผู้ใช้พิมพ์>. <ทำอะไร>. Use <skill อื่น> for <งานใกล้เคียง>."
---

## Start
เปิด todolist: 1. Frame 2. Fan out 3. Judge/Aggregate 4. Verify 5. Report

## Phase A: Frame
- artifact ที่ต้องได้ / done predicate
- rubric 3-6 ข้อ (ผู้ทำไม่เห็น)
- โมเดลต่อบทบาท (อ่านจาก config, มี default)
- output path แยกต่อ worker

## Phase B: Fan out
spawn ทุกตัวใน message เดียว, background, prompt จาก references/<role>-prompt.md
ตัวหลุด → ทำต่อ N-1 แล้วบันทึก

## Phase C: Judge / Aggregate
<กฎการเลือก / การรวม / ผลที่ไม่มีหลักฐานถือเป็น gap>

## Phase D: Verify
<บนของจริง; ถ้าพัง กลับ Phase A หรือ C>

## Outputs
<รูปแบบตายตัว>
```

---

## 15. ลำดับการอ่านไฟล์ต้นฉบับ

| ลำดับ | ไฟล์ | เรียนรู้อะไร |
|---|---|---|
| 1 | `plugins/pstack/hooks/session-start-context.md` | เกณฑ์การเข้าระบบ |
| 2 | `plugins/pstack/skills/poteto-mode/SKILL.md` | โครงของ router ทั้งหมด |
| 3 | `skills/poteto-mode/playbooks/bug-fix.md` | playbook ที่อิงหลักฐาน |
| 4 | `skills/poteto-mode/playbooks/feature.md` | throughput checkpoint และ delegation |
| 5 | `skills/poteto-mode/playbooks/refactoring.md` | การตรึงพฤติกรรมและขั้นตัดสินว่าจะเก็บหรือ revert |
| 6 | `skills/arena/SKILL.md` | รูปแบบ fan-out ที่สมบูรณ์ที่สุด |
| 7 | `skills/interrogate/SKILL.md` + `references/reviewer-prompt.md` | การเขียน prompt template |
| 8 | `skills/why/SKILL.md` | การเก็บหลักฐานครบทุกประเภทและการบันทึกผลว่าง |
| 9 | `skills/figure-it-out/SKILL.md` | วิธีออกแบบ workflow ใหม่ |
| 10 | `skills/poteto-mode/playbooks/orchestrate.md` | brief, store และการกู้คืนเมื่อล้มเหลว |
| 11 | `skills/principle-encode-lessons-in-structure/SKILL.md` | การบังคับด้วยโครงสร้าง |
| 12 | `skills/reflect/SKILL.md` | วงจรการพัฒนาตัวเอง |
| 13 | `models.json` + `tools/generate.mjs` | แหล่งความจริงเดียวและ generator |
