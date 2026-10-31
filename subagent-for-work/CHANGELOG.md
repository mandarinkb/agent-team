# CHANGELOG: เปลี่ยนจาก teammate (Agent Teams) เป็น subagent

**เหตุผลรวม:** ตอนใช้งานจริง ทีมทำงานแบบ teammate (มี HOLD / GO / shutdown / idle notification / ส่งข้อความหากัน) และใช้ token มาก เพราะ teammate อยู่ค้างจนถูกปิด และทุกข้อความปลุกให้ทำ turn ใหม่พร้อม context ทั้งหมด ชุดนี้เปลี่ยนเป็น subagent ทีละขั้นแบบ pstack: lead spawn หนึ่งขั้น subagent รายงานแล้วจบ ทุกการส่งต่อผ่าน lead

**หลักที่ใช้ตอนแก้:** ไม่ลบบทเรียนจาก ticket จริง กติกาที่มีอยู่เพราะ teammate ค้างอยู่ (HOLD, GO, คำสั่งแทนที่, idle, shutdown) ถูกแปลงเป็นกติกาที่มีเจตนาเดียวกันในแบบ subagent ส่วนหัวไฟล์ role (`name`, `description`, `disallowedTools`, `model`) และชื่อไฟล์ไม่ได้แก้ HANDOVER.md กับ MANIFEST.sha256 ก็ไม่ได้แก้

## ไฟล์ที่เพิ่ม

| ไฟล์ | เหตุผล |
|---|---|
| `.agents/templates/brief.md` | subagent รู้เฉพาะสิ่งที่อยู่ใน brief และในไฟล์ จึงต้องมีแบบฟอร์มที่บังคับให้ใส่ ticket, รอบ, scope, contract พร้อม `file:line` และคำตัดสินล่าสุดแบบคำต่อคำ และตอบ HANDOVER ข้อ 6.6 ที่ขอแม่แบบข้อความถึง teammate |
| `CHANGELOG.md` | ไฟล์นี้ (ตาม HANDOVER ข้อ 5) |

## ไฟล์ที่แก้

### `.agents/workflows/ticket.md`
| ประเด็น | ก่อน | หลัง | เหตุผล |
|---|---|---|---|
| กลไก | ไม่ได้ระบุ (ใช้จริงเป็น teammate) | เพิ่มหัวข้อ "กลไก": spawn ด้วย Agent tool ไม่ตั้ง `name`, หนึ่ง spawn ต่อหนึ่งขั้น, ไม่คุยกันเอง, ขั้นที่ขนานกันใช้ background | ทำให้ตรงกับ README และกัน spawn ที่ตั้งชื่อแล้วกลายเป็น teammate เมื่อเปิด Agent Teams ไว้ |
| ขั้น 1 รายการไฟล์ | backend ส่งรายการไฟล์ให้ lead ก่อนเขียนโค้ด | lead ใส่รายการไฟล์ในแผนที่ผู้ใช้ยืนยัน แล้วส่งให้ backend ใน brief | subagent ส่งข้อความกลางทางไม่ได้ และแบบใหม่เข้มกว่าเดิม เพราะผู้ใช้เห็นรายการไฟล์ก่อนเริ่ม |
| ขั้น 1 analyst | ไม่ระบุว่าเรียกตอนไหน | spawn ก่อนสรุปแผน เมื่อ ticket ยังมีข้อสงสัย | ระบุให้ชัดว่าเรียกตอนไหน |
| ขั้น 2–4 | backend แจ้ง qa ตรง, qa รอ "GO" | lead spawn qa แยกเป็น 3 ขั้น (เขียน / เทียบ contract / รัน) และการ spawn ขั้นรันถือเป็น GO | ไม่มีตัวที่ค้างรอข้อความ |
| ขั้น 4 | ไม่ได้บอกให้ปิด server | qa ต้องหยุด server และ `bru` ที่ตัวเองเปิดก่อนรายงาน | subagent จบหลังรายงาน process ที่ค้างจะไม่มีเจ้าของ |
| ขั้น 5 | fix item ส่งให้ backend ผ่าน lead | lead spawn backend ตัวใหม่พร้อม path ของ fix item และนับรอบจากไฟล์ | subagent ตัวใหม่จำรอบก่อนไม่ได้ |
| ขั้น 7 ปิดทีม | ส่ง shutdown ตามชื่อ รอยืนยัน แล้วดู `tmux ls` | ตรวจว่าไม่มี subagent แบบ background ค้าง และไม่มี server / `bru` ค้าง (`ps`) | subagent ไม่ต้อง shutdown แต่เจตนา "อย่ารายงานว่าปิดแล้วจากการคาดเอา" ยังอยู่ |
| กติกากลาง | "teammate คุยกันเองได้เรื่อง contract" / "ส่งสรุปถึง lead ทุกครั้ง" | role ไม่คุยกันเอง ส่ง contract ผ่านรายงานและ brief | ข้อ "ส่งสรุปถึง lead" มีไว้เพราะ lead มองไม่เห็นข้อความระหว่าง teammate ตอนนี้ปัญหานี้ไม่มีแล้ว |
| ประสานงานข้อ 1 (HOLD) | ส่ง HOLD ให้ทุกคนที่ขึ้นกับคำตัดสิน | ห้าม spawn ขั้นที่ขึ้นกับคำตัดสิน ส่วนตัวที่รันอยู่ให้รอผลแล้วตรวจใหม่ | เจตนาเดิม: ไม่ให้ใครลงมือก่อนผู้ใช้ตัดสิน |
| ประสานงานข้อ 3 (คำสั่งแทนที่) | ส่งข้อความ "แทนที่คำสั่ง..." และรอยืนยันกลับ | brief ใส่เฉพาะคำตัดสินล่าสุด พร้อมระบุว่าแทนของเดิม | ทุก spawn เริ่มจาก brief ใหม่ ไม่มีคำสั่งเก่าค้าง |
| ประสานงานข้อ 6 (GO) | qa รันเมื่อได้ข้อความ "GO" | qa รันได้เฉพาะ spawn ที่ brief เขียน `Step: 4 run` | เจตนาเดิม: มีสัญญาณเริ่มรันจุดเดียวที่ชัดเจน |
| ประสานงานข้อ 7 (idle) | ไม่ตอบ idle notification ซ้ำ | รอผลจาก subagent แบบ background ให้ครบ ไม่ spawn ซ้ำ และไม่เดาผล | idle notification ไม่มีในแบบ subagent ข้อใหม่กันปัญหาที่คล้ายกัน |
| ข้อ 2, 4, 5, 8 | | คงไว้ แก้แค่คำว่า "ส่งข้อความ / แจ้ง teammate" เป็น "brief" | |

### `.claude/agents/backend.md`
| ประเด็น | ก่อน | หลัง | เหตุผล |
|---|---|---|---|
| ข้อ 1 | ส่งรายการไฟล์ให้ lead ก่อนเขียนโค้ด | ใช้รายการไฟล์จาก brief ถ้าต้องแตะไฟล์นอกรายการ ให้หยุดและรายงาน | ตามขั้น 1 ของ workflow |
| ข้อ 5 | tell the lead **and `qa`** "implemented" แล้ว stop and wait | รายงาน lead พร้อม contract แล้ว lead ส่งต่อให้ qa จบขั้นด้วยรายงาน | ไม่คุยกันเอง |
| ข้อ 6 | "When a fix item arrives" | "When your brief names a fix item" และให้อ่าน review ด้วย | subagent ตัวใหม่ต้องอ่านบริบทจากไฟล์ |
| decision request | "to the lead" / "wait for the lead" | ใส่ในรายงาน แล้วจบ lead จะ spawn ใหม่พร้อมคำตอบ | subagent รอข้อความไม่ได้ |
| Language | "messages to the lead and other teammates" | "reports to the lead" | |

### `.claude/agents/qa.md`
| ประเด็น | ก่อน | หลัง | เหตุผล |
|---|---|---|---|
| Running: GO / HOLD | รอ "GO" จาก lead, หยุดเมื่อได้ HOLD | รันได้เฉพาะเมื่อ brief เขียน `Step: 4 run` | ตามข้อ 6 ของการประสานงาน (ยังอ้างบทเรียน ticket 47) |
| เพิ่ม | | หยุดทุก server และ `bru` ที่เปิดเองก่อนรายงาน | subagent จบหลังรายงาน |
| แก้ Bruno หลัง review | tell the lead right away | เขียนไว้บนสุดของรายงาน | ไม่มีช่องทางส่งข้อความกลางทาง |

### `.agents/README.md`
- บรรทัด "ยังไม่ใช่ teammate": เขียนใหม่ให้ชัดว่าทุก role เป็น subagent ทีละขั้น ไม่ตั้ง `name` และอ้างถึง brief กับหัวข้อ "กลไก" (แก้ปัญหาที่ HANDOVER ข้อ 6.7 ชี้ไว้)
- ตาราง templates: เพิ่ม `brief.md`

### `.agents/templates/decision-request.md`
- "ความเห็นของ teammate อื่น" เปลี่ยนเป็น "ความเห็นของ role อื่นที่ lead ส่งมาใน brief"

## เพิ่มภายหลัง: เสนอ retro ตอนปิดงาน

| ไฟล์ | ก่อน | หลัง | เหตุผล |
|---|---|---|---|
| `.agents/workflows/ticket.md` ขั้น 7 | ไม่มี | ถ้า ticket วนแก้ตั้งแต่ 2 รอบ หรือมีการทำผิดกติกา lead บอกผู้ใช้ว่าควรรัน `/retro` พร้อมเหตุผล และห้ามรันเอง | ผู้ใช้เจอปัญหาหลังจบ ticket บ่อย จึงต้องการทบทวนเพื่อปรับ workflow ด้วย skill `retro` ของ mattpocock ซึ่งตั้งใจให้ผู้ใช้เรียกเอง (`disable-model-invocation: true`) การรันทุก ticket ทำให้เปลือง token และกฎงอกจาก ticket ที่ไม่มีปัญหา lead จึงทำหน้าที่แค่เตือน |

## เพิ่มภายหลัง: หลักฐานทุกรอบ

**เหตุผล:** ผู้ใช้ต้องการอ่านหลักฐานว่า subagent ทำงานถูกจริงทุกรอบ และสุ่มทดสอบเองได้ โดยไม่ต้องเชื่อรายงาน หลักคือผลดิบจากเครื่องมือ (log) เป็นหลักฐาน ส่วนข้อความที่ subagent เขียนเป็นแค่สารบัญ ให้บันทึก output ลงไฟล์แทนการอ่านเข้า context รายงานจึงอ้าง path แทนการแปะผล token จึงไม่ควรเพิ่มมาก (ตีความ ยังไม่ได้วัด) ผู้ใช้เลือกใช้การเทียบสถานะไฟล์ (ทางเลือก A) แทน fingerprint เพราะจะลบเอกสารหลังอ่าน

| ไฟล์ | ก่อน | หลัง | เหตุผล |
|---|---|---|---|
| `.agents/templates/evidence.md` (ใหม่) | | หน้าเดียวที่ผู้ใช้อ่าน: ผลทีละ AC พร้อมลิงก์ไปหาผลดิบ, ประวัติรอบ, สิ่งที่ไม่ได้ทดสอบ, เคสแนะนำให้สุ่มตรวจ, คำตอบว่าโค้ดเปลี่ยนหลัง qa รันรอบสุดท้ายไหม | ผู้ใช้ไม่ต้องเปิดหลายไฟล์ไล่หาเอง |
| `.agents/workflows/ticket.md` กลไก | | เพิ่ม "หลักฐานทุกรอบ": โฟลเดอร์ `reviews/<ticket>/r<n>/`, ผลดิบคือหลักฐาน, `> file 2>&1`, รายงานอ้าง path | หลักร่วมของทุกขั้น |
| `ticket.md` ขั้น 2, 4, 5 | | brief ระบุโฟลเดอร์หลักฐานของรอบ, backend เขียน `backend-tests.md`, spec-reviewer เขียน `r<n>/spec-review.md`, qa เขียน `qa.md` + `bruno.log` + `git-status.txt`, รอบแก้ใช้โฟลเดอร์ `r<n+1>/` | แยกรอบ จึงเห็นว่ารอบก่อนพังเพราะอะไร |
| `ticket.md` ขั้น 6 | | lead เทียบ `git status --short` + `git diff --stat` กับ `git-status.txt` ของรอบสุดท้าย แล้วเขียนผลลง `evidence.md` ห้ามข้าม | ทางเลือก A: กันกรณีหลักฐานเก่ากว่าโค้ดที่จะ commit โดยไม่ต้องคำนวณ hash |
| `ticket.md` ขั้น 7 | | lead เขียน `evidence.md` จาก `r*/*.md` เท่านั้น ไม่อ่าน log เต็ม แล้วบอก path ก่อนขอให้สั่ง commit | context ของ lead ไม่บวม |
| `ticket.md` กติกากลาง | qa เขียน `<ticket>-qa-cases.md` | qa เขียน `<ticket>/r<n>/qa.md` (รวมคู่มือทดสอบด้วยมือ) | ไม่เขียนทับรอบก่อน |
| `.claude/agents/qa.md` | หัวข้อ "Test case summary for the user" | หัวข้อ "Evidence for each run": `git-status.txt`, `bruno.log` (CLI output เท่านั้น ห้ามเก็บ `--reporter-json` หรือ verbose), `db.md` เมื่อ ticket เขียน DB, `qa.md` ตาราง AC → request → ผล → หลักฐาน, grep หา secret ก่อนจบ แล้วตามด้วย "Manual test guide" ที่เป็นเนื้อหาเดิม | ผลดิบตรวจย้อนได้ และ reporter-json มี header ที่มี token อยู่ (HANDOVER ข้อ 6.1 เคยมี secret หลุดจริง) |
| `qa.md` You write / Report | เขียนรายงานไฟล์เดียวตาม path ที่กำหนด | เขียนหลักฐานในโฟลเดอร์ของรอบ รายงานอ้าง path ไม่แปะ output | |
| `.claude/agents/backend.md` | ห้ามเขียนใน `.scratch/` | ยกเว้นไฟล์เดียว `backend-tests.md` ในโฟลเดอร์หลักฐาน + ข้อ 8: test ที่แดงก่อนแก้, test ที่ไม่เคยเห็นแดง, ตาราง mutation | หลักฐาน test-first ที่เดิมอยู่แค่ในรายงาน |
| `.claude/agents/spec-reviewer.md` | ค่าเริ่มต้น `reviews/<ticket>-r<n>.md` | `reviews/<ticket>/r<n>/spec-review.md` | ให้ไฟล์ของรอบเดียวกันอยู่ในโฟลเดอร์เดียวกัน |
| `.agents/templates/brief.md` | | เพิ่มช่อง Evidence folder | |
| `.agents/templates/db-check.md` | Revision = commit SHA | Revision = รอบที่ n + `git-status.txt` | ทีมนี้ไม่ commit ระหว่างทาง ทำให้ template นี้มีขั้นตอนที่เรียกใช้แล้ว (เดิมไม่มี role ไหนใช้) |
| `.agents/README.md` | | เพิ่ม `evidence.md` ในรายการ template | |

## เพิ่มภายหลัง: บันทึกการตัดสินใจ, ไฟล์สถานะ และ retry ตามประเภท (นำมาจาก pstack)

| ไฟล์ | เพิ่มอะไร | เหตุผล |
|---|---|---|
| `ticket.md` กลไก | `log.tsv` ที่ lead เขียนคนเดียว เพิ่มต่อท้ายอย่างเดียว แถวละหนึ่งการตัดสินใจ (`ts step decision why evidence result`) | จาก show-me-your-work ของ pstack ให้ retro อ่านไฟล์เดียวแทน transcript ของ subagent ทุกตัว ทำให้ retro ถูกลงและไม่พลาดปัญหาระหว่างทาง |
| `ticket.md` กลไก + กติกากลาง | `progress.md` ที่ lead เขียนทับหลังจบทุกขั้น (ตารางเดียวกับที่สรุปให้ผู้ใช้) | จาก Pause safely / Session pickup ของ pstack เดิมทำต่อไม่ได้ถ้า session หลุดกลาง ticket |
| `ticket.md` หัวข้อใหม่ "ทำต่อเมื่อ session หลุด" | อ่าน `progress.md` + `log.tsv` ก่อน, ตรวจกับ git และไฟล์จริง, ถือ PASS เก่าเป็นคำกล่าวอ้าง, ไม่ทำซ้ำขั้นที่เสร็จ, spawn ใหม่เฉพาะขั้นที่หายไป | กฎของ Session pickup: ไม่ทำงานซ้ำ และไม่เชื่อรายงานของตัวก่อน |
| `ticket.md` หัวข้อใหม่ "เมื่อเครื่องมือหรือสภาพแวดล้อมล้ม" | ตาราง retry ตามประเภท (network/DB ครั้งเดียว, OTP ห้าม retry ทันทีให้ BLOCKED พร้อมเวลา, server/tool เปลี่ยนวิธีครั้งเดียว, timeout ลด scope), ล้มแบบเดิม 2 ครั้งให้หยุด, subagent ที่ติดให้ spawn ตัวใหม่ ถ้าติดซ้ำให้ถามผู้ใช้ | จาก Orchestrate ของ pstack กฎ 3 รอบเดิมใช้กับโค้ดผิด แต่ไม่มีกฎสำหรับสภาพแวดล้อมพัง ซึ่งทำให้วนรันจนเปลือง token และ OTP · subagent ใช้ `sleep` รอเองไม่ได้ lead จึงต้อง spawn ใหม่หลังโควตาว่าง |
| `ticket.md` ขั้น 7 (เสนอ retro) | บอกให้ retro อ่าน `log.tsv` กับ `progress.md` ก่อน | |
| `.claude/agents/qa.md` Running | เพิ่มกฎสภาพแวดล้อมล้ม อ้างไปที่ตารางใน `ticket.md` | |
| `.claude/agents/backend.md` | หัวข้อใหม่ "When the environment fails" อ้างไปที่ตารางเดียวกัน และไม่นับเป็นรอบ | |
| `.agents/templates/evidence.md` | รายการไฟล์รวม `log.tsv` และ `progress.md` | |

## ไม่ได้แก้ (ตั้งใจ)
- `analyst.md`, `spec-reviewer.md`: ทำงานตามที่ผู้เรียกกำหนดอยู่แล้ว และไม่มีส่วนที่คุยกับ role อื่น
- `HANDOVER.md`: ข้อ 3 กับตาราง qa ยังเขียนว่า "รันเมื่อ lead สั่ง GO" ซึ่งเป็นคำอธิบายของต้นทาง ฝั่งต้นทางควรแก้เอง
- HANDOVER ข้อ 6.1–6.5: เป็นเรื่องกติกาเนื้องาน ไม่เกี่ยวกับการเปลี่ยนเป็น subagent จึงยังไม่ได้แก้

## คำถามถึงฝั่งต้นทาง
1. skill `local-run` อาจบอกให้เปิด server แบบค้างไว้ (เช่นใน tmux) ถ้าใช่ ต้องปรับให้ qa ปิด server เองตอนจบ spawn หรือให้ lead เป็นคนเปิดและปิด server แทน
2. ถ้า global settings ของเครื่องที่ใช้งานเปิด `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` อยู่ ต้องการปิดไหม หรือจะคงไว้แล้วอาศัยกฎ "ไม่ตั้ง `name`"
4. skill `bruno-regression` อาจกำหนดวิธีรันหรือ flag ของ `bru` ไว้ต่างจาก `bru run <folder> -r --env <env> > bruno.log 2>&1` ใน `qa.md` ถ้าต่าง ให้ใช้ของ skill แต่ต้องบันทึก CLI output ลง `bruno.log` เหมือนเดิม
3. ขั้น 3 (qa เทียบ contract) กับขั้น 4 (qa รัน) ตอนนี้รวมเป็น spawn เดียวได้ถ้าไม่มีความต่าง ต้องการบังคับให้แยกเสมอไหม (แยกกันจะได้ contract ที่ตรวจแล้วก่อนรันเสมอ แต่ใช้ token มากกว่า)
