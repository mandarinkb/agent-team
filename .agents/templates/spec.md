# Spec: {{TITLE}}

- **Job:** {{JOB}}
- **Kind:** {{KIND}}
- **Grill:** [grill-notes.md](grill-notes.md)

## 1. เป้าหมาย

<fill: หนึ่งย่อหน้า คนที่ไม่เห็นแชตอ่านแล้วเข้าใจ>

## 2. ขอบเขต

- **ทำ:** <fill>
- **ไม่ทำ:** <fill>

## 3. Acceptance criteria

ทุกข้อต้องตรวจได้ด้วยการรันอะไรสักอย่าง ข้อที่ตรวจไม่ได้ (เช่น "เร็วขึ้น" โดยไม่มีตัวเลข) ห้ามใส่

| ID | เงื่อนไข | ตรวจด้วย (bruno / db / test) |
|---|---|---|
| AC-1 | <fill> | <fill> |

## 4. API contract

ลบหัวข้อนี้ถ้างานไม่มี API

### <fill: METHOD /path>

- **Request:** <fill: headers, params, body พร้อมชนิดข้อมูล>
- **Response สำเร็จ:** <fill: status และ body ตัวอย่าง>
- **Error:** <fill: ทุกกรณี: status, body, เงื่อนไขที่ทำให้เกิด>

## 5. Data contract

ลบหัวข้อนี้ถ้างานไม่แตะฐานข้อมูล ทุก column ที่งานเขียนต้องอยู่ในตาราง column ที่ไม่ได้ระบุจะไม่ถูกตรวจ

กฎที่ใช้ได้: `= <ค่า>`, `= request.<field>`, `not null`, `null`, `format: <uuid|iso-datetime|email|regex>`, `unchanged`

| Case | Table | Column | กฎ | AC |
|---|---|---|---|---|
| <fill> | <fill> | <fill> | <fill> | AC-1 |

## 6. ข้อมูลทดสอบ: seed และ reset

ลบหัวข้อนี้ถ้างานไม่แตะฐานข้อมูล qa รัน reset แล้ว seed ก่อนทดสอบรอบสุดท้ายทุกครั้ง เพื่อให้ผลตรวจทีละ column ซ้ำได้

- **Reset:** <fill: คำสั่งที่ล้างข้อมูลทดสอบ>
- **Seed:** <fill: คำสั่งหรือ request ที่สร้างข้อมูลตั้งต้น และข้อมูลที่ได้ (id, สถานะ)>

## 7. Baseline (migration เท่านั้น)

<fill: ที่เก็บ baseline จากระบบเก่า, env ของระบบเก่าและใหม่, ส่วนต่างที่ผู้ใช้ยอมรับแล้วพร้อมเลข decision หรือลบหัวข้อนี้>

## 8. เรื่องที่รอผู้ใช้ตัดสิน

<fill: ลิงก์ decisions/D-n.md หรือ "ไม่มี">
