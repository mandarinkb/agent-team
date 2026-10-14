# ชุดสกิล pstack ที่แนะนำสำหรับ dev (ฟีเจอร์ใหม่ แก้บั๊ก และย้าย API จาก PHP เป็น Go)

เอกสารนี้ต่อจาก `PSTACK-GUIDE-TH.md` เน้นว่าควรตั้งค่าและเลือกใช้สกิลอย่างไรสำหรับงานสามแบบ

> ที่มา: สรุปจากการอ่าน playbook Feature, Bug fix, Refactoring, Multi-phase plan และสกิล `figure-it-out` ในโปรเจกต์นี้ ยังไม่ได้ทดลองรันกับโปรเจกต์จริง ส่วนที่เป็นข้อเสนอของผู้เขียนเองจะระบุว่า "ข้อเสนอ"

---

## 1. ตั้งค่าพื้นฐาน (ทำครั้งเดียว)

1. ติดตั้งปลั๊กอิน แล้วรัน `/pstack:setup-pstack`
2. ถ้ากังวลเรื่องค่า token ให้ลดจำนวนโมเดลใน role ที่ใช้หลายตัว (`arena runners`, `interrogate reviewers`) หรือตั้ง effort ให้ต่ำลง
3. ตั้ง `CLAUDE_CODE_ENABLE_TODO_TOOLS=1` เพื่อเปิดตัวติดตามงาน เพราะ `poteto-mode` ใช้ todolist ติดตามทุกขั้น
4. ในแต่ละ repo รัน `/create-verification-skill` เพื่อสร้างสกิลที่ขับแอปหรือยิง API เหมือนผู้ใช้ เพราะ playbook เกือบทุกตัวบังคับให้ตรวจบนของจริง ไม่ใช่แค่ผ่านเทสต์

---

## 2. งานประจำวัน

ใช้ผ่าน `poteto-mode` ได้เลย มันเลือก playbook ให้เอง

| งาน | ตัวอย่างคำสั่ง | สิ่งที่ playbook ทำ |
|---|---|---|
| แก้บั๊ก | `Use poteto-mode to fix <อาการ>` | reproduce เอง → ไล่หาสาเหตุด้วยหลักฐาน → แก้เท่าที่หลักฐานรองรับ → ตรวจซ้ำ → commit repro ก่อนโค้ดที่แก้ → เปิด PR |
| ฟีเจอร์ใหม่ | `Use poteto-mode to add <ฟีเจอร์>` | `how` ศึกษาระบบเดิม → `architect` ออกแบบหลายแบบ → วางแผนงานขนาน → มอบ subagent เขียน → ตรวจบนของจริง → แตกเป็น commit เล็กตามลำดับ → เปิด PR |
| ตรวจก่อนส่ง | `deslop`, `no-comments`, `interrogate` | ล้างร่องรอย AI, ตัด comment ที่ไม่จำเป็น, ให้หลายโมเดลช่วยโต้แย้งเมื่อดีไซน์ถกเถียงได้ |
| ดูแล PR | `babysit` | แก้ CI และตอบคอมเมนต์ที่ตรงไปตรงมาจน merge ได้ |

เคล็ดลับ: บั๊กที่เขียน test เล็ก ๆ ได้ง่าย ให้พูดถึง `tdd` ด้วย จะได้ test ที่ล้มก่อนแล้วค่อยแก้

---

## 3. ย้าย API จาก PHP เป็น Go

### 3.1 เลือก playbook ตามขนาดงาน

| ขนาดงาน | ใช้ |
|---|---|
| ทีละ endpoint (เล็กถึงกลาง ไม่ข้ามระบบ) | playbook **Refactoring** |
| ย้ายทั้งระบบ หรือหลายสิบ endpoint | **`figure-it-out`** (เอกสารระบุว่าเหมาะกับ migration ใหญ่และงานที่คนมาตรวจทีหลัง) |
| ย้ายหลายสัปดาห์ หลาย PR | **Multi-phase plan** เขียนแผน แล้วรันด้วย **Autopilot-stack** (สร้าง stack ของ PR ที่คุณเป็นคน land เอง) |

### 3.2 หัวใจ: pin พฤติกรรมเดิมก่อนย้าย

Refactoring ขั้น 1 บังคับให้เขียน characterization test หรือ equivalence harness ที่จับพฤติกรรมปัจจุบันไว้ก่อนย้ายโครงสร้าง และระบุว่า type check กับ lint ไม่ใช่การ pin

ข้อเสนอสำหรับ PHP → Go:
1. บันทึก request/response จริงของ endpoint PHP เป็น baseline (ระวังอย่าให้มีข้อมูลจริงของผู้ใช้)
2. เขียนสคริปต์เล่นซ้ำกับ endpoint Go แล้ว diff ผลลัพธ์ ได้แก่ status code, header สำคัญ, รูปแบบ error
3. ทดสอบ edge case ที่ PHP กับ Go มักต่างกัน เช่น ค่าว่าง/null, การแปลง type อัตโนมัติ, ลำดับ key ของ JSON, ตัวเลขทศนิยม

`figure-it-out` ก็ระบุให้สร้าง harness ตรวจสอบก่อนเริ่มงาน โดยจับ baseline จากสถานะก่อนเปลี่ยน ให้ผลอ่านได้เป็น "ค่าเก่าเทียบค่าใหม่"

### 3.3 ลำดับที่แนะนำสำหรับ 1 endpoint (ข้อเสนอ ประกอบจากขั้นของ Refactoring)

1. `how` อ่าน endpoint PHP ให้เข้าใจสัญญาจริง รวมพฤติกรรมแอบแฝง
2. `blast-radius` หาว่าใครเรียก endpoint นี้ (client, cron, service อื่น)
3. เขียน harness เทียบผล PHP กับ Go
4. ให้ subagent แปลง ถ้ามีหลายแนวทาง (เช่น โครงสร้าง error handling) ใช้ `arena`
5. รัน harness ให้ผลตรงกัน ใช้ `interrogate` กับส่วนเสี่ยง (เงิน, auth, transaction)
6. แตกเป็น commit เล็กและเปิด PR

### 3.4 ข้อขัดกันที่ต้องระบุในโจทย์

Refactoring ห้ามเก็บโค้ดเก่าและใหม่คู่กันแบบ shim แต่ในการย้ายจริง คุณอาจต้องให้ PHP กับ Go ทำงานคู่กันช่วงหนึ่ง (route ทีละ endpoint) ถ้าเป็นกรณีนี้ ให้เขียนเงื่อนไขนี้ในโจทย์ชัด ๆ เพื่อไม่ให้ agent ลบเส้นทางเก่าก่อนเวลา

### 3.5 โจทย์ตัวอย่าง

ทีละ endpoint:
```text
Use poteto-mode to convert the /orders API endpoint from PHP to Go.
Keep the PHP endpoint running during the migration. Pin current behavior
first by replaying recorded requests against both and diffing the responses.
```

ทั้งระบบ:
```text
/figure-it-out migrate the PHP API to Go, one endpoint at a time.
Keep PHP endpoints live until each Go endpoint matches the recorded baseline.
```

---

## 4. สกิลที่แนะนำ

| กลุ่ม | สกิล |
|---|---|
| ประจำวัน | `poteto-mode`, `how`, `why`, `tdd`, `deslop`, `babysit`, `fix-ci` |
| งาน migration | `figure-it-out`, `blast-radius`, `architect`, `arena`, `interrogate`, `show-me-your-work` (บันทึกการตัดสินใจต่อ endpoint พร้อมหลักฐาน) |
| ตั้งต้นต่อ repo | `create-verification-skill` |
| ยังไม่จำเป็น | `orchestrate`, `autopilot-full` (สำหรับโปรแกรมหลายวันที่ใช้ subagent จำนวนมาก), `hillclimb`, `benchmark-checklist` (ใช้เมื่อต้องวัดประสิทธิภาพ เช่น เทียบ PHP กับ Go) |

---

## 5. ข้อควรระวัง

- **ข้อมูลไปที่ผู้ให้บริการโมเดล:** โค้ดที่ subagent อ่านถูกส่งออกไป ถ้า API เกี่ยวกับข้อมูลลับของลูกค้า ให้ตรวจนโยบายก่อน
- **เริ่มจาก endpoint เสี่ยงต่ำ:** ใช้เป็นต้นแบบ แล้วดูว่าขั้นตอนเหมาะกับทีมก่อนขยาย
- **ค่า token:** `arena`, `interrogate`, `architect` เรียกหลาย subagent พร้อมกัน
- **งานเล็กไม่ต้องใช้ทั้งชุด:** แก้บรรทัดเดียวสั่งตรง ๆ ได้
