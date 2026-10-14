# สรุปการศึกษา pstack (ภาษาไทย)

เอกสารชุดนี้สรุปจากการอ่าน source ของ pstack ในโปรเจกต์นี้ (`plugins/pstack/`, `tools/`, `tests/` และ `docs/`) เพื่อศึกษาหลักการออกแบบ agent workflow แล้วนำไปประยุกต์ใช้

> **เวอร์ชันที่ใช้สรุป:** pstack-claude `0.9.64` (ตามต้นฉบับ Cursor ถึง commit `23e4138`) ถ้า plugin อัปเดต ให้ดู `CHANGES.md` ก่อนเชื่อเนื้อหาในชุดนี้
>
> **การยืนยัน:** ทุกอย่างมาจากการอ่านไฟล์ ยังไม่ได้รัน skill หรือ script ใดจริง ส่วนที่เป็นการตีความหรือข้อเสนอของผู้เขียนมีป้ายกำกับไว้ในแต่ละไฟล์

## ไฟล์ในชุดนี้

| ไฟล์ | เนื้อหา | ควรอ่านเมื่อ |
|---|---|---|
| [1. หลักการออกแบบ Workflow Agent](PSTACK-WORKFLOW-DESIGN-TH.md) | วิธีที่ pstack ออกแบบและเขียน workflow ทีละขั้น ตั้งแต่ hook, router, โครงของ playbook, สกิลที่กระจายงานให้ subagent, การมอบงาน, การตรวจผล, ระดับอิสระในการตัดสินใจ ไปจนถึง checklist และ template สำหรับออกแบบเอง | อ่านก่อน ถ้าต้องการเข้าใจภาพรวมของระบบ |
| [2. คู่มือ Skill ทั้งหมด](PSTACK-SKILLS-CATALOG-TH.md) | skill ทั้ง 56 ตัว (รวม principle 24 ตัว) และ playbook 23 ตัว บอกว่าแต่ละตัวทำอะไร เหมาะกับงานแบบไหน มีขั้นตอนอย่างไร พร้อมตารางเลือก skill ตามสถานการณ์ | ใช้เปิดหาเมื่อจะเลือกว่าใช้ skill ไหน |
| [3. เจาะลึก Reference, Prompt, Script และ Generator](PSTACK-DEEP-DIVE-TH.md) | ส่วนที่บังคับกฎด้วยโค้ด ได้แก่ prompt template ของ subagent, กรอบระดับความมั่นใจ (epistemics), script อย่าง orch, watch-pr และ check-plan รวมถึง generator และ sync ของ repo | อ่านเมื่อต้องการรู้ว่ากฎถูกบังคับอย่างไร |
| [4. Design Patterns ที่นำไปใช้ได้](PSTACK-DESIGN-PATTERNS-TH.md) | 7 จุดที่ควรเรียนรู้ ได้แก่ ระบบที่เรียนรู้จากตัวเอง, บันทึกที่ตรวจตัวเองได้, การตัดสินใจที่ทดสอบได้, store ที่ทนต่อ crash, การสร้าง subagent runtime, test ที่ปกป้อง prompt และ portability พร้อมตาราง 14 pattern | อ่านเมื่อจะนำไปออกแบบระบบของตัวเอง |
| [5. ข้อจำกัดและเมื่อไรไม่ควรใช้](PSTACK-LIMITATIONS-TH.md) | ต้นทุน (นับจำนวน subagent ต่อ flow), ขั้นตอนที่เยอะเกินงาน, ค่าเริ่มต้นเรื่องอิสระในการตัดสินใจ, เครื่องมือที่ต้องมี, ความเห็นเฉพาะตัว, ความเป็นส่วนตัว พร้อมตารางตัดสินใจและวิธีรับเฉพาะส่วนที่คุ้ม | อ่านก่อนตัดสินใจนำไปใช้กับทีม |
| [6. ชุดเริ่มต้น: ย้าย API จาก PHP เป็น Go](starter-kit-php-to-go/README.md) | project playbook, brief template, script เทียบ response ของ PHP กับ Go (มี test) และกฎใน CLAUDE.md ที่ตรึงด้วย script | ใช้เมื่อเริ่มย้าย endpoint จริง |
| [7. Agent Teams เทียบกับ pstack](PSTACK-VS-AGENT-TEAMS-TH.md) | เทียบสถาปัตยกรรมทีละด้าน, ข้อดีและข้อเสีย, แบบไหนกิน token มากกว่า (พร้อมปัจจัยต้นทุนและการประเมินตามสถานการณ์), การใช้ร่วมกัน และวิธีวัด token เอง | อ่านเมื่อกำลังเลือกระหว่าง Agent Teams กับ pstack |

## ลำดับการอ่านที่แนะนำ

1. **อยากเข้าใจภาพรวม:** เริ่มจาก [หลักการออกแบบ Workflow Agent](PSTACK-WORKFLOW-DESIGN-TH.md) หัวข้อ 1 ถึง 5
2. **อยากเริ่มใช้ pstack:** เปิด [ตารางเลือก skill ตามสถานการณ์](PSTACK-SKILLS-CATALOG-TH.md#ภาคผนวก-ตารางเลือก-skill-ตามสถานการณ์)
3. **อยากออกแบบ workflow ของตัวเอง:** อ่าน [Checklist และ Template](PSTACK-WORKFLOW-DESIGN-TH.md#14-checklist-และ-template-สำหรับออกแบบ-workflow-ของคุณ) แล้วต่อด้วย [Pattern ที่นำไปใช้ได้ทันที](PSTACK-DESIGN-PATTERNS-TH.md#8-สรุป-pattern-ที่นำไปใช้ได้ทันที)
4. **กำลังตัดสินใจว่าจะใช้กับทีมไหม:** อ่าน [ข้อจำกัดและเมื่อไรไม่ควรใช้](PSTACK-LIMITATIONS-TH.md) โดยเฉพาะ [ตารางตัดสินใจ](PSTACK-LIMITATIONS-TH.md#10-ตารางตัดสินใจ-ใช้หรือไม่ใช้)
5. **จะเริ่มย้าย PHP เป็น Go:** ใช้ [ชุดเริ่มต้น](starter-kit-php-to-go/README.md)
6. **กำลังเลือกระหว่าง Agent Teams กับ pstack:** อ่าน [Agent Teams เทียบกับ pstack](PSTACK-VS-AGENT-TEAMS-TH.md) โดยเฉพาะ [แบบไหนกิน token มากกว่ากัน](PSTACK-VS-AGENT-TEAMS-TH.md#5-แบบไหนกิน-token-มากกว่ากัน)
7. **อยากรู้ว่ากฎถูกบังคับด้วยโค้ดอย่างไร:** อ่าน [เจาะลึก Reference, Prompt, Script และ Generator](PSTACK-DEEP-DIVE-TH.md)

## สารบัญรวม

### [1. หลักการออกแบบ Workflow Agent](PSTACK-WORKFLOW-DESIGN-TH.md)

- [แนวคิดตั้งต้น](PSTACK-WORKFLOW-DESIGN-TH.md#1-แนวคิดตั้งต้น)
- [สถาปัตยกรรมชั้นของ workflow](PSTACK-WORKFLOW-DESIGN-TH.md#2-สถาปัตยกรรมชั้นของ-workflow)
- [ขั้นที่ 0: การเข้าระบบด้วย Hook](PSTACK-WORKFLOW-DESIGN-TH.md#3-ขั้นที่-0-การเข้าระบบด้วย-hook)
- [ขั้นที่ 1: Router (`poteto-mode`)](PSTACK-WORKFLOW-DESIGN-TH.md#4-ขั้นที่-1-router-poteto-mode)
- [กายวิภาคของ Playbook](PSTACK-WORKFLOW-DESIGN-TH.md#5-กายวิภาคของ-playbook)
- [Playbook ทีละตัวแบบละเอียด](PSTACK-WORKFLOW-DESIGN-TH.md#6-playbook-ทีละตัวแบบละเอียด)
- [สกิล fan-out ทีละตัวแบบละเอียด](PSTACK-WORKFLOW-DESIGN-TH.md#7-สกิล-fan-out-ทีละตัวแบบละเอียด)
- [สัญญาการมอบหมายงาน (Delegation Contract)](PSTACK-WORKFLOW-DESIGN-TH.md#8-สัญญาการมอบหมายงาน-delegation-contract)
- [ระบบการตรวจสอบ (Verification)](PSTACK-WORKFLOW-DESIGN-TH.md#9-ระบบการตรวจสอบ-verification)
- [ระดับอิสระในการตัดสินใจ (Autonomy)](PSTACK-WORKFLOW-DESIGN-TH.md#10-ระดับอิสระในการตัดสินใจ-autonomy)
- [ความต่อเนื่อง: หยุด รับช่วง และ decision trail](PSTACK-WORKFLOW-DESIGN-TH.md#11-ความต่อเนื่อง-หยุด-รับช่วง-และ-decision-trail)
- [การบังคับด้วยโครงสร้างแทนข้อความ](PSTACK-WORKFLOW-DESIGN-TH.md#12-การบังคับด้วยโครงสร้างแทนข้อความ)
- [การเขียน prompt และ skill](PSTACK-WORKFLOW-DESIGN-TH.md#13-การเขียน-prompt-และ-skill)
- [Checklist และ Template สำหรับออกแบบ workflow ของคุณ](PSTACK-WORKFLOW-DESIGN-TH.md#14-checklist-และ-template-สำหรับออกแบบ-workflow-ของคุณ)
- [ลำดับการอ่านไฟล์ต้นฉบับ](PSTACK-WORKFLOW-DESIGN-TH.md#15-ลำดับการอ่านไฟล์ต้นฉบับ)

### [2. คู่มือ Skill ทั้งหมด](PSTACK-SKILLS-CATALOG-TH.md)

- [ภาพรวมและแผนที่การเลือก skill](PSTACK-SKILLS-CATALOG-TH.md#ภาพรวมและแผนที่การเลือก-skill)
- [หมวด A: ตัว Router และ Workflow หลัก](PSTACK-SKILLS-CATALOG-TH.md#หมวด-a-ตัว-router-และ-workflow-หลัก)
- [หมวด B: ทำความเข้าใจโค้ดและบริบท](PSTACK-SKILLS-CATALOG-TH.md#หมวด-b-ทำความเข้าใจโค้ดและบริบท)
- [หมวด C: ออกแบบและกระจายงานคู่ขนาน](PSTACK-SKILLS-CATALOG-TH.md#หมวด-c-ออกแบบและกระจายงานคู่ขนาน)
- [หมวด D: รีวิวและตรวจคุณภาพ](PSTACK-SKILLS-CATALOG-TH.md#หมวด-d-รีวิวและตรวจคุณภาพ)
- [หมวด E: ทดสอบและพิสูจน์ผล](PSTACK-SKILLS-CATALOG-TH.md#หมวด-e-ทดสอบและพิสูจน์ผล)
- [หมวด F: งาน PR และ CI](PSTACK-SKILLS-CATALOG-TH.md#หมวด-f-งาน-pr-และ-ci)
- [หมวด G: การเขียน](PSTACK-SKILLS-CATALOG-TH.md#หมวด-g-การเขียน)
- [หมวด H: ความต่อเนื่องและการเรียนรู้ของระบบ](PSTACK-SKILLS-CATALOG-TH.md#หมวด-h-ความต่อเนื่องและการเรียนรู้ของระบบ)
- [หมวด I: ตั้งค่าและปรับให้เป็นของตัวเอง](PSTACK-SKILLS-CATALOG-TH.md#หมวด-i-ตั้งค่าและปรับให้เป็นของตัวเอง)
- [หมวด J: ภาษาเฉพาะ](PSTACK-SKILLS-CATALOG-TH.md#หมวด-j-ภาษาเฉพาะ)
- [หมวด K: Principles (หลักคิด 24 ข้อ)](PSTACK-SKILLS-CATALOG-TH.md#หมวด-k-principles-หลักคิด-24-ข้อ)
- [ภาคผนวก: Playbook ภายใน poteto-mode](PSTACK-SKILLS-CATALOG-TH.md#ภาคผนวก-playbook-ภายใน-poteto-mode)
- [ภาคผนวก: ตารางเลือก skill ตามสถานการณ์](PSTACK-SKILLS-CATALOG-TH.md#ภาคผนวก-ตารางเลือก-skill-ตามสถานการณ์)

### [3. เจาะลึก Reference, Prompt, Script และ Generator](PSTACK-DEEP-DIVE-TH.md)

- [สิ่งที่ได้เรียนรู้เพิ่มจากรอบนี้](PSTACK-DEEP-DIVE-TH.md#1-สิ่งที่ได้เรียนรู้เพิ่มจากรอบนี้)
- [Orchestrate: ส่วนที่เหลือ](PSTACK-DEEP-DIVE-TH.md#2-orchestrate-ส่วนที่เหลือ)
- [Multi-phase plan: skeleton และ check-plan](PSTACK-DEEP-DIVE-TH.md#3-multi-phase-plan-skeleton-และ-check-plan)
- [Reference ของ poteto-mode](PSTACK-DEEP-DIVE-TH.md#4-reference-ของ-poteto-mode)
- [Prompt template ของ subagent](PSTACK-DEEP-DIVE-TH.md#5-prompt-template-ของ-subagent)
- [Scripts: กลไกที่บังคับแทนคำสั่ง](PSTACK-DEEP-DIVE-TH.md#6-scripts-กลไกที่บังคับแทนคำสั่ง)
- [Tools ระดับ repo: generator และ sync](PSTACK-DEEP-DIVE-TH.md#7-tools-ระดับ-repo-generator-และ-sync)
- [บทเรียนสำหรับนำไปออกแบบเอง](PSTACK-DEEP-DIVE-TH.md#8-บทเรียนสำหรับนำไปออกแบบเอง)

### [4. Design Patterns ที่นำไปใช้ได้](PSTACK-DESIGN-PATTERNS-TH.md)

- [Reflect: ระบบที่เรียนรู้จากตัวเอง](PSTACK-DESIGN-PATTERNS-TH.md#1-reflect-ระบบที่เรียนรู้จากตัวเอง)
- [Show-me-your-work: บันทึกที่ตรวจตัวเองได้](PSTACK-DESIGN-PATTERNS-TH.md#2-show-me-your-work-บันทึกที่ตรวจตัวเองได้)
- [Policy as pure functions: การตัดสินใจที่ทดสอบได้](PSTACK-DESIGN-PATTERNS-TH.md#3-policy-as-pure-functions-การตัดสินใจที่ทดสอบได้)
- [Store ที่ทนต่อ crash และหลาย process](PSTACK-DESIGN-PATTERNS-TH.md#4-store-ที่ทนต่อ-crash-และหลาย-process)
- [การสร้าง subagent runtime เอง](PSTACK-DESIGN-PATTERNS-TH.md#5-การสร้าง-subagent-runtime-เอง)
- [Test ที่ปกป้องเนื้อหาของ prompt](PSTACK-DESIGN-PATTERNS-TH.md#6-test-ที่ปกป้องเนื้อหาของ-prompt)
- [Portability: skill ชุดเดียว ใช้ได้หลาย runtime](PSTACK-DESIGN-PATTERNS-TH.md#7-portability-skill-ชุดเดียว-ใช้ได้หลาย-runtime)
- [สรุป: Pattern ที่นำไปใช้ได้ทันที](PSTACK-DESIGN-PATTERNS-TH.md#8-สรุป-pattern-ที่นำไปใช้ได้ทันที)

### [5. ข้อจำกัดและเมื่อไรไม่ควรใช้](PSTACK-LIMITATIONS-TH.md)

- [สรุปสั้น](PSTACK-LIMITATIONS-TH.md#1-สรุปสั้น)
- [ต้นทุน: จำนวน subagent และ token](PSTACK-LIMITATIONS-TH.md#2-ต้นทุน-จำนวน-subagent-และ-token)
- [ขั้นตอนเยอะเกินงาน](PSTACK-LIMITATIONS-TH.md#3-ขั้นตอนเยอะเกินงาน)
- [ค่าเริ่มต้นเรื่องอิสระในการตัดสินใจ](PSTACK-LIMITATIONS-TH.md#4-ค่าเริ่มต้นเรื่องอิสระในการตัดสินใจ)
- [สิ่งที่ pstack สมมติว่าทีมใช้](PSTACK-LIMITATIONS-TH.md#5-สิ่งที่-pstack-สมมติว่าทีมใช้)
- [ความเห็นเฉพาะตัวที่อาจไม่ตรงกับทีม](PSTACK-LIMITATIONS-TH.md#6-ความเห็นเฉพาะตัวที่อาจไม่ตรงกับทีม)
- [กฎส่วนใหญ่ยังพึ่งการทำตามคำสั่ง](PSTACK-LIMITATIONS-TH.md#7-กฎส่วนใหญ่ยังพึ่งการทำตามคำสั่ง)
- [ข้อมูลและความเป็นส่วนตัว](PSTACK-LIMITATIONS-TH.md#8-ข้อมูลและความเป็นส่วนตัว)
- [การดูแลรักษาในระยะยาว](PSTACK-LIMITATIONS-TH.md#9-การดูแลรักษาในระยะยาว)
- [ตารางตัดสินใจ: ใช้หรือไม่ใช้](PSTACK-LIMITATIONS-TH.md#10-ตารางตัดสินใจ-ใช้หรือไม่ใช้)
- [วิธีรับเฉพาะส่วนที่คุ้ม](PSTACK-LIMITATIONS-TH.md#11-วิธีรับเฉพาะส่วนที่คุ้ม)

### [6. ชุดเริ่มต้น: ย้าย API จาก PHP เป็น Go](starter-kit-php-to-go/README.md)

- [มีอะไรอยู่ในชุดนี้](starter-kit-php-to-go/README.md#มีอะไรอยู่ในชุดนี้)
- [ติดตั้งในโปรเจกต์ของคุณ](starter-kit-php-to-go/README.md#ติดตั้งในโปรเจกต์ของคุณ)
- [วิธีใช้ทีละ endpoint](starter-kit-php-to-go/README.md#วิธีใช้ทีละ-endpoint)
- [script นี้เทียบอะไร และไม่เทียบอะไร](starter-kit-php-to-go/README.md#script-นี้เทียบอะไร-และไม่เทียบอะไร)
- [ขั้นต่อไปที่แนะนำ](starter-kit-php-to-go/README.md#ขั้นต่อไปที่แนะนำ)

### [7. Agent Teams เทียบกับ pstack](PSTACK-VS-AGENT-TEAMS-TH.md)

- [สรุปสั้น](PSTACK-VS-AGENT-TEAMS-TH.md#1-สรุปสั้น)
- [แต่ละแบบคืออะไร](PSTACK-VS-AGENT-TEAMS-TH.md#2-แต่ละแบบคืออะไร)
- [เทียบสถาปัตยกรรมทีละด้าน](PSTACK-VS-AGENT-TEAMS-TH.md#3-เทียบสถาปัตยกรรมทีละด้าน)
- [ข้อดีและข้อเสีย](PSTACK-VS-AGENT-TEAMS-TH.md#4-ข้อดีและข้อเสีย)
- [แบบไหนกิน token มากกว่ากัน](PSTACK-VS-AGENT-TEAMS-TH.md#5-แบบไหนกิน-token-มากกว่ากัน)
- [ใช้ร่วมกันได้ไหม และต้องระวังอะไร](PSTACK-VS-AGENT-TEAMS-TH.md#6-ใช้ร่วมกันได้ไหม-และต้องระวังอะไร)
- [เลือกแบบไหนสำหรับงานแบบไหน](PSTACK-VS-AGENT-TEAMS-TH.md#7-เลือกแบบไหนสำหรับงานแบบไหน)
- [วิธีวัด token ด้วยตัวเอง](PSTACK-VS-AGENT-TEAMS-TH.md#8-วิธีวัด-token-ด้วยตัวเอง)
- [แหล่งอ้างอิง](PSTACK-VS-AGENT-TEAMS-TH.md#9-แหล่งอ้างอิง)

## เอกสารภาษาไทยอื่นในโปรเจกต์

ไฟล์เหล่านี้มีอยู่ก่อนแล้วในโฟลเดอร์หลัก ไม่ได้ถูกย้ายมาไว้ที่นี่

- [คู่มือติดตั้งและใช้งาน pstack](../PSTACK-GUIDE-TH.md)
- [การออกแบบ Agent Team ของ pstack](../PSTACK-AGENT-TEAM-DESIGN-TH.md)
- [ทีม Agent สำหรับหาบั๊ก เพิ่มฟีเจอร์ และย้ายระบบ (analyst, backend, frontend, qa, reviewer, git)](../agent-team-roles/README-TH.md)
- [ชุดสกิล pstack ที่แนะนำสำหรับ dev (ฟีเจอร์ใหม่ แก้บั๊ก และย้าย API จาก PHP เป็น Go)](../PSTACK-DEV-SETUP-TH.md)
