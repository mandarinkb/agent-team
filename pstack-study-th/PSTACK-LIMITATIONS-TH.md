# ข้อจำกัดของ pstack และเมื่อไรไม่ควรใช้

[← กลับไปหน้ารวม](README.md)

> **ทำไมต้องมีไฟล์นี้:** สี่ไฟล์ก่อนหน้าอธิบายว่า pstack ดีอย่างไร ไฟล์นี้อธิบายต้นทุนและจุดที่อาจไม่เข้ากับทีมของคุณ เพื่อให้เลือกรับมาใช้เฉพาะส่วนที่คุ้ม
>
> **ระดับหลักฐาน:** ทุกข้ออ้างอิงไฟล์จริงใน pstack เวอร์ชัน `0.9.64` จำนวน subagent มาจาก **การนับตามคำสั่งใน skill ไม่ได้วัดจากการรันจริง** ส่วนที่เป็นการตีความของผู้เขียนมีป้าย **(ตีความ)** และวิธีรับมือมีป้าย **(ข้อเสนอ)**

---

## สารบัญ

1. [สรุปสั้น](#1-สรุปสั้น)
2. [ต้นทุน: จำนวน subagent และ token](#2-ต้นทุน-จำนวน-subagent-และ-token)
3. [ขั้นตอนเยอะเกินงาน](#3-ขั้นตอนเยอะเกินงาน)
4. [ค่าเริ่มต้นเรื่องอิสระในการตัดสินใจ](#4-ค่าเริ่มต้นเรื่องอิสระในการตัดสินใจ)
5. [สิ่งที่ pstack สมมติว่าทีมใช้](#5-สิ่งที่-pstack-สมมติว่าทีมใช้)
6. [ความเห็นเฉพาะตัวที่อาจไม่ตรงกับทีม](#6-ความเห็นเฉพาะตัวที่อาจไม่ตรงกับทีม)
7. [กฎส่วนใหญ่ยังพึ่งการทำตามคำสั่ง](#7-กฎส่วนใหญ่ยังพึ่งการทำตามคำสั่ง)
8. [ข้อมูลและความเป็นส่วนตัว](#8-ข้อมูลและความเป็นส่วนตัว)
9. [การดูแลรักษาในระยะยาว](#9-การดูแลรักษาในระยะยาว)
10. [ตารางตัดสินใจ: ใช้หรือไม่ใช้](#10-ตารางตัดสินใจ-ใช้หรือไม่ใช้)
11. [วิธีรับเฉพาะส่วนที่คุ้ม](#11-วิธีรับเฉพาะส่วนที่คุ้ม)

---

## 1. สรุปสั้น

pstack ออกแบบมาสำหรับ **ทีมที่ให้ความสำคัญกับความถูกต้องมากกว่าค่าใช้จ่าย ใช้ GitHub กับ stacked PR และยอมให้ agent ทำงานเองได้มาก** ถ้าทีมของคุณไม่ตรงกับข้อใดข้อหนึ่งนี้ ให้เลือกรับเป็นบางส่วน ไม่ต้องรับทั้งระบบ

| ด้าน | ข้อจำกัดหลัก | ความรุนแรง |
|---|---|---|
| ต้นทุน | งานหนึ่งชิ้นอาจใช้ subagent 10 ถึง 25 ตัว และแต่ละตัวต้องอ่านคำสั่งยาว | สูง |
| ขั้นตอน | งานที่แตะ 2 ไฟล์ก็เข้าระบบเต็มรูปแบบ | กลาง |
| อิสระในการตัดสินใจ | โพสต์ในแชตทีมและอัปเดต ticket ได้โดยไม่ถาม | กลาง ถึงสูง ขึ้นกับองค์กร |
| เครื่องมือ | ผูกกับ GitHub, Graphite และ bun | กลาง |
| ความเห็นเฉพาะตัว | ห้าม shim, ลบ comment หนัก, บังคับ Conventional Commits | ต่ำ ถึงกลาง |
| การบังคับใช้ | กฎส่วนใหญ่เป็นข้อความที่ model อาจไม่ทำตาม | กลาง |
| ข้อมูล | อ่าน transcript, แชต และเอกสารผ่าน MCP | สูงสำหรับข้อมูลลับ |
| การดูแล | ยังเป็นเวอร์ชัน 0.9.x และเปลี่ยนบ่อย | ต่ำ ถึงกลาง |

---

## 2. ต้นทุน: จำนวน subagent และ token

### 2.1 ทุก subagent ต้องอ่านคำสั่งยาวก่อนเริ่ม
- `poteto-mode/SKILL.md` ยาว **25.6 KB (167 บรรทัด)** ซึ่งเป็นภาษาอังกฤษ น่าจะประมาณ 6,000 token **(ตีความ: ประมาณจากขนาดไฟล์)**
- `agents/poteto-agent.md` สั่งว่า "Reads the `poteto-mode` skill's `SKILL.md` in full before any work" **subagent `poteto-agent` ทุกตัวจึงต้องเสียต้นทุนนี้ซ้ำ** และยังต้องอ่าน playbook กับ principle ที่เกี่ยวข้องเพิ่มอีก
- poteto-mode กำหนดว่า "Cite only principles whose leaf SKILL.md you read this session" ทำให้ต้องเปิดไฟล์ principle เพิ่มเพื่อจะอ้างอิงได้

### 2.2 จำนวน subagent ต่อ flow (นับจากคำสั่ง ไม่ได้วัด)
| Flow | ส่วนประกอบตามคำสั่ง | ประมาณการ |
|---|---|---|
| `how` แบบซับซ้อน | explorer 2-4 + explainer 1 | 3-5 |
| `why` | investigator สูงสุด 7 (ตามจำนวนประเภท MCP ที่มี) + synthesizer 1 | 2-8 |
| `arena` | runner 3 + judge 1 | 4 |
| `architect` | `how` (Phase A) + `arena` | 5-9 |
| `interrogate` | reviewer 3 | 3 |
| `reflect` | reviewer 3 + synthesizer 1 | 4 |
| **Feature playbook** | `how` + `architect` + delegate (บังคับใช้ `arena` ถ้าทำได้หลายแบบ) + `interrogate` ถ้ามีข้อโต้แย้ง + ตอนเปิด PR subagent ต้องรัน `interrogate` และ `no-comments` อีก | **ประมาณ 10-25** |
| **Bug fix playbook** | `how` + `why` + `architect` ถ้าข้าม boundary + delegate + ตอนเปิด PR | **ประมาณ 5-20** |
| **Multi-phase plan ต่อ PR ต่อรอบ** | gates 1 + live lanes 10 + perf 1 + audit อย่างน้อย 2 | **อย่างน้อย 14** |

ข้อสังเกต
- Feature ขั้น 1 เรียก `how` แล้วขั้น 2 เรียก `architect` ซึ่ง Phase A ก็เรียก `how` อีก จึงอาจสำรวจซ้ำ **(ตีความ: คำสั่งไม่ได้บอกให้ใช้ผลรอบแรกซ้ำ)**
- **โมเดลค่าเริ่มต้น:** bug-fix, perf-issue, hillclimb และ "strongest judgment" ใช้ `fable` ส่วน panel ใช้ 3 โมเดลคือ opus, fable และ sonnet (`models.json`)
- **ไม่มี telemetry:** README เขียนว่า "pstack has no server or telemetry" ข้อดีคือไม่มีข้อมูลรั่วออก ข้อเสียคือ **คุณไม่รู้ว่าแต่ละงานใช้เงินไปเท่าไร** ถ้าไม่วัดเอง

### 2.3 วิธีรับมือ (ข้อเสนอ)
- ใช้ `/pstack:setup-pstack` ลด panel จาก 3 โมเดลเหลือ 2 สำหรับ `arena runners`, `architect runners` และ `interrogate reviewers` และตั้ง `bug-fix` เป็น `opus` แทน `fable`
- ตั้ง `default effort` ให้ต่ำลง แล้วเพิ่ม effort เฉพาะบทบาทที่ต้องใช้วิจารณญาณ
- **วัดก่อนตัดสินใจ:** ลองรันงานจริง 3-5 งาน แล้วดูค่าใช้จ่ายจาก dashboard ของผู้ให้บริการ ก่อนจะเปิดใช้ทั้งทีม

---

## 3. ขั้นตอนเยอะเกินงาน

### 3.1 เกณฑ์เข้าระบบกว้าง
`hooks/session-start-context.md` สั่งให้เรียก poteto-mode เมื่องาน "touches more than one file" งานประจำวันจำนวนมาก เช่น แก้ handler กับ test ของมัน ก็แตะ 2 ไฟล์แล้ว จึงอาจถูกส่งเข้า flow เต็ม **(ตีความ)**

### 3.2 pstack เองก็รู้เรื่องนี้
- Orchestrate: "Ceremony must scale with the program" และ "A verifier agent whose entire product would be rerunning one command is ceremony, not verification"
- Orchestrate: ถ้า agent ตัวเดียวทำเสร็จได้ ให้ไปใช้ Autonomous run แทน
- figure-it-out: "A second arena over a settled design is over-engineering"
- Multi-phase plan ขั้นที่ 1: งาน 1-2 ไฟล์ที่วิธีทำชัด ให้ข้ามการทำแผน

กฎเหล่านี้ช่วยลดขั้นตอนได้ แต่ **ขึ้นกับว่า model ตัดสินถูกหรือไม่** ว่างานเล็กพอ

### 3.3 วิธีรับมือ (ข้อเสนอ)
- ถ้างานส่วนใหญ่เป็นงานเล็ก ให้ปิด hook (`session hook: off` ใน `pstack-models.md`) แล้วเรียก `/pstack:poteto-mode` เองเฉพาะงานใหญ่
- เขียนใน `CLAUDE.md` ว่างานแบบไหนไม่ต้องใช้ poteto-mode เพราะ hook เขียนไว้ว่า "User instructions (CLAUDE.md, AGENTS.md, direct requests) take precedence"

---

## 4. ค่าเริ่มต้นเรื่องอิสระในการตัดสินใจ

### 4.1 สิ่งที่ทำได้โดยไม่ต้องถาม
poteto-mode ส่วน Autonomy:
> **Just do it.** Use any MCP tool. Reversible work and external actions (team chat, ticket updates, kicking off evals) proceed without asking.

- **การโพสต์ในแชตทีมและการอัปเดต ticket ถูกจัดว่า "ทำได้เลย"** สิ่งที่ต้องหยุดถามเสมอมีแค่ force-push branch ที่ใช้ร่วมกัน, deploy, ลบข้อมูล และส่งข้อความถึงลูกค้า
- principle `never-block-on-the-human` ส่งเสริมให้ "Proceed, then present"
- ใน Autonomous run: "Do not park reversible work for the human or use `AskUserQuestion`"

### 4.2 ความเสี่ยง (ตีความ)
- ในองค์กรที่การโพสต์ในช่องแชตหรือการเปลี่ยนสถานะ ticket มีผลกับคนอื่น สิ่งนี้อาจไม่ถือว่า "ย้อนกลับได้"
- งานที่ "ย้อนกลับได้ในทางเทคนิค" อาจมีต้นทุนจริง เช่น เปิด PR จำนวนมาก หรือ trigger CI ที่มีค่าใช้จ่าย

### 4.3 วิธีรับมือ (ข้อเสนอ)
เพิ่มใน `CLAUDE.md`:
```
- Ask before posting to any team chat channel or changing a ticket's status or assignee.
- Ask before opening more than one PR in a session.
```
และใช้ permission ของ Claude Code จำกัด MCP tool ที่เขียนข้อมูลภายนอก

---

## 5. สิ่งที่ pstack สมมติว่าทีมใช้

| สมมติฐาน | หลักฐาน | ผลถ้าไม่ตรง |
|---|---|---|
| **GitHub** | Babysit, Shipping และ `watch-pr` ใช้ `gh` และ verdict ของ GitHub (Origin CLI เป็นทางเลือก) | GitLab หรือ Bitbucket ต้องดัดแปลงส่วน PR ทั้งหมด |
| **Graphite (`gt`)** | `docs/reference.md`: "The Orchestrate playbook and `orch` stack frontier" ต้องใช้ | ใช้ Orchestrate ไม่ได้เต็มที่ |
| **Stacked PR** | Opening a PR: "Prefer five narrow PRs to one large PR" และเน้นทำงานแบบ stack | ทีมที่ทำ PR ใหญ่ทีละตัวจะรู้สึกว่าขั้นตอนเยอะ |
| **bun** | `bootstrap.ts` ไม่ยอมรันบน node | script ของ Orchestrate และ watch-pr ใช้ไม่ได้ |
| **มีวิธีขับแอปจริง** | playbook ส่วนใหญ่ต้องใช้ driver skill หรือ `verify` | ระบบที่ขับยาก เช่น mobile native, hardware หรือระบบที่ต้อง login ซับซ้อน จะ verify ได้แค่บางส่วน |
| **มี MCP ครบ** | `why` ออกแบบมาให้ค้น 7 ประเภทหลักฐาน | ถ้ามีแค่ git ผลของ `why` จะอ่อนลงมาก (skill บันทึกเป็น gap ไว้ให้) |

---

## 6. ความเห็นเฉพาะตัวที่อาจไม่ตรงกับทีม

pstack คือสไตล์การทำงานของคนคนหนึ่ง (Lauren Tan หรือ "poteto") บางกฎเป็นความเห็น ไม่ใช่ความจริงสากล

| กฎ | ที่มา | อาจขัดกับ |
|---|---|---|
| ห้าม compatibility shim และห้ามมี path เก่ากับใหม่คู่กัน | Refactoring ขั้น 5, `migrate-callers-then-delete-legacy-apis` | migration แบบ strangler ที่ต้องรันเก่ากับใหม่คู่กัน (เช่น PHP → Go) ทั้งนี้ principle ระบุเงื่อนไขไว้ว่า "No external users depend on backward compatibility" |
| ลบ comment อย่างหนัก | `no-comments` / `comment-sicko`: "When I am not sure a keep clause applies, the comment dies." | ทีมที่มีมาตรฐานเอกสารในโค้ด หรืออยู่ในอุตสาหกรรมที่มีกฎหมายกำกับ |
| เปิด PR เป็น ready เสมอ | Opening a PR: "Open every PR ready, never as a draft." | ทีมที่ใช้ draft PR บอกสถานะงาน |
| บังคับ Conventional Commits | Opening a PR: `type(scope): subject` | ทีมที่มีรูปแบบ commit ของตัวเอง |
| ไฟล์ห้ามโตเกิน 1,000 บรรทัด | `thermo-nuclear-code-quality-review`, code-quality lens | codebase ที่มีไฟล์ใหญ่อยู่แล้วตามธรรมชาติ เช่น generated code |
| เอียงไปทางลบโค้ด | `laziness-protocol`, `subtract-before-you-add` | ระบบที่ต้องคงพฤติกรรมเดิมไว้แม้ดูไม่ได้ใช้ |
| กฎการเขียนภาษาอังกฤษ | `unslop` (ห้าม em dash, ห้าม colon กลางประโยค), `technical-writing` | เอกสารภาษาไทย ซึ่งกฎเหล่านี้ใช้ได้แค่บางส่วน **(ตีความ)** |

**วิธีรับมือ (ข้อเสนอ):** เขียนกฎที่ต่างออกไปใน `CLAUDE.md` หรือ project playbook (ดูตัวอย่าง `Replace` ใน [starter kit](starter-kit-php-to-go/.agents/playbooks/php-to-go-endpoint.md)) เพราะคำสั่งของผู้ใช้มีลำดับความสำคัญสูงกว่า

---

## 7. กฎส่วนใหญ่ยังพึ่งการทำตามคำสั่ง

[Deep Dive](PSTACK-DEEP-DIVE-TH.md) แสดงว่ากฎสำคัญบางข้อถูกบังคับด้วยโค้ด แต่ **กฎส่วนใหญ่ยังเป็นข้อความใน Markdown** ที่ model ต้องอ่านแล้วทำตามเอง

- ตัว pstack ยอมรับเอง: `poteto-agent.md` เขียนว่า "Substituting `general-purpose` skips that read and drifts" และ Orchestrate เขียนว่า "Directives decay across resumes, and each dropped one costs a human turn"
- `skill-rules.test.mjs` ป้องกันแค่ไม่ให้ **ประโยคหายจากไฟล์** แต่ไม่ได้รับประกันว่า model จะทำตาม
- คำสั่งรวมกันยาวมาก (poteto-mode + playbook + principle + skill ย่อย) ยิ่งยาว โอกาสที่บางข้อถูกข้ามก็ยิ่งมาก **(ตีความ)**
- ตัวอย่าง: playbook บังคับให้ "copy steps verbatim" และใส่ `skip: <reason>` แต่ไม่มี script ตรวจว่า todolist มีครบจริง

**วิธีรับมือ (ข้อเสนอ):** ทำแบบที่ pstack ทำกับกฎที่สำคัญที่สุด คือเลือก 2-3 กฎที่ถ้าพลาดแล้วเสียหายมาก แล้วเปลี่ยนเป็น script หรือ CI ([starter kit](starter-kit-php-to-go/README.md) ทำแบบนี้กับ parity check)

---

## 8. ข้อมูลและความเป็นส่วนตัว

- README: "Anything its skills ask your agent to read, including session transcripts, goes to your model provider."
- **skill ที่อ่าน transcript:** `reflect`, `recall`, `automate-me` และ Session pickup ทุกตัวจำกัดไว้ที่ workspace ปัจจุบัน และเขียนเตือนไว้ว่า "Don't glob across `~/.claude/projects/`. That crosses workspace boundaries and reads private chats"
- **skill ที่ค้น MCP:** `why` และ `recall` ส่ง investigator ไปค้น Slack, Notion, Linear, Sentry, Datadog และ data warehouse **ข้อมูลจากระบบเหล่านี้จะถูกส่งไปยังผู้ให้บริการ model**
- `why` บังคับให้ investigator ใช้ agent mode ไม่ใช่ readonly เพราะ readonly ตัด MCP ออก investigator จึงมีสิทธิ์เขียนในทางเทคนิค แม้ prompt จะบอกว่าห้ามเขียน

**วิธีรับมือ (ข้อเสนอ):** ถ้ามีข้อมูลลับหรือข้อมูลส่วนบุคคล ให้จำกัด MCP ที่เชื่อมต่อ ตรวจนโยบายข้อมูลของบริษัทก่อน และอย่าใช้ `why` หรือ `recall` กับช่องแชตหรือเอกสารที่มีข้อมูลลูกค้า

---

## 9. การดูแลรักษาในระยะยาว

- **ยังไม่ถึง 1.0:** เวอร์ชันปัจจุบันคือ `0.9.64` และ `CHANGES.md` มีการเปลี่ยนแปลงบ่อย
- **เป็น port ไม่ใช่ต้นฉบับ:** pstack-claude ตามต้นฉบับของ Cursor (`tools/upstream.json` pin ไว้ที่ commit `23e4138`) และมี fork ที่ประกาศไว้ใน `forks.json` การอัปเดตจึงมาจากสองทาง
- **project playbook อาจเสียเมื่ออัปเกรด:** project playbook ยกข้อความจาก playbook หลักมาเป็นตัวอ้างอิง ถ้า pstack แก้ข้อความนั้น playbook ของคุณจะใช้ไม่ได้ (`check-playbooks.mjs` จับได้ แต่ต้องรันเอง)
- **เอกสารชุดนี้จะล้าสมัย:** สรุปจากเวอร์ชัน `0.9.64` เท่านั้น

**วิธีรับมือ (ข้อเสนอ):** pin เวอร์ชันของ plugin ไว้ ใส่ `check-playbooks.mjs` ใน CI ของโปรเจกต์ และอ่าน `CHANGES.md` ก่อนอัปเกรดทุกครั้ง

---

## 10. ตารางตัดสินใจ: ใช้หรือไม่ใช้

| สถานการณ์ | คำแนะนำ |
|---|---|
| แก้ไฟล์เดียว, typo, เปลี่ยน config | **ไม่ใช้** สั่งตรง ๆ |
| ทำ prototype หรือ spike ที่จะทิ้ง | ใช้ playbook **Prototype** อย่างเดียว ไม่ต้องใช้ทั้งระบบ |
| บั๊กที่ยังไม่รู้สาเหตุในระบบสำคัญ | **ใช้ Bug fix** คุ้มที่สุด เพราะบังคับ reproduce และใช้หลักฐาน |
| feature ที่ต้องตัดสินใจเรื่องโครงสร้าง | **ใช้ Feature** แต่ลด panel ลงถ้ากังวลต้นทุน |
| migration ใหญ่ เช่น PHP → Go | **ใช้แบบมีการปรับ** ด้วย project playbook ที่แก้กฎห้าม shim (ดู [starter kit](starter-kit-php-to-go/README.md)) |
| ทีมไม่ได้ใช้ GitHub | ใช้แค่ playbook ที่ไม่เกี่ยวกับ PR และทำส่วน PR เอง |
| งบ token จำกัดมาก | ใช้ principle กับ template เป็นแนวทาง ไม่ต้องเปิด hook และไม่ใช้สกิลที่ส่ง subagent หลายตัว |
| องค์กรห้าม agent โพสต์หรือแก้ระบบภายนอก | ใช้ได้ แต่ต้องเขียนกฎใน `CLAUDE.md` และจำกัด permission ก่อน |
| ข้อมูลลับหรือข้อมูลส่วนบุคคล | ใช้ได้ แต่ห้ามเชื่อม MCP ที่เข้าถึงข้อมูลนั้น และระวัง `why` กับ `recall` |
| ปล่อยงานยาวข้ามคืน | **ใช้ Autonomous run + `show-me-your-work`** เป็นจุดแข็งของ pstack |

---

## 11. วิธีรับเฉพาะส่วนที่คุ้ม

เรียงจากต้นทุนต่ำและคุ้มมาก ไปจนถึงต้นทุนสูง **(ข้อเสนอ)**

| ระดับ | สิ่งที่รับมาใช้ | ต้นทุน | ได้อะไร |
|---|---|---|---|
| 1 | **แนวคิดอย่างเดียว:** principle ที่ชอบใส่ใน `CLAUDE.md`, กรอบระดับความมั่นใจจาก `epistemics.md` และป้าย "วัดมา / อนุมาน / เดา" | แทบไม่มี | agent รายงานซื่อตรงขึ้น และหลักฐานชัดขึ้น |
| 2 | **Template:** brief 9 ช่อง, rationale template และรูปแบบ decision log | ต่ำ | การมอบงานให้ subagent ชัดขึ้น |
| 3 | **เครื่องมือตรวจ:** script แบบ parity หรือ check_rules และตรึงกฎด้วย test | ต่ำ ถึงกลาง (ทำครั้งเดียว) | กฎสำคัญถูกบังคับจริง |
| 4 | **Skill เดี่ยว:** `how`, `why`, `tdd`, `blast-radius`, `deslop` และ `benchmark-checklist` เรียกเองเมื่อต้องใช้ | กลาง | ได้ความสามารถเฉพาะเรื่องโดยไม่มีขั้นตอนทั้งระบบ |
| 5 | **Playbook ที่ใช้บ่อย:** Bug fix และ Refactoring (+ project playbook) | กลาง ถึงสูง | ได้ workflow ที่ตรวจได้ทุกขั้น |
| 6 | **ทั้งระบบ:** เปิด hook, ใช้ panel 3 โมเดล, Orchestrate และ Autopilot | สูง | ทำงานใหญ่ได้เองโดยคนแทบไม่ต้องเข้ามา |

**คำแนะนำ:** เริ่มที่ระดับ 1-3 ก่อน แล้วลองระดับ 5 กับงานจริง 1 งาน (เช่น endpoint แรกด้วย [starter kit](starter-kit-php-to-go/README.md)) วัดต้นทุนกับผลที่ได้ แล้วค่อยตัดสินใจว่าจะไปต่อหรือไม่
