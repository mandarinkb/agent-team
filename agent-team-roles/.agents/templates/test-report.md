# รายงานผลการทดสอบ: {{TITLE}}

- **Task:** {{TASK_ID}}
- **Workflow:** {{KIND}}
- **Verdict:** <fill: PASS | ISSUES | BLOCKED | INCONCLUSIVE>
- **Revision:** <fill: tree id จาก git write-tree ที่ git ส่งมา>
- **Branch:** <fill>
- **Round:** <fill: 1, 2 หรือ 3 รอบที่ 4 ขึ้นไปต้องมี D9 ที่ผู้ใช้อนุมัติ>
- **Round approval:** <fill: ไม่ต้อง หรืออ้าง D9 ใน decisions.md ที่อนุมัติรอบเพิ่ม>
- **Tested by:** qa (<fill: model>)
- **Date:** {{DATE}}

<!--
qa เป็นผู้เขียนไฟล์นี้คนเดียว ห้ามมีช่องกรอก (fill) เหลืออยู่ เพราะ hook gate_reports.py จะไม่ยอมให้ปิดงาน verify
Verdict:
  PASS          ทุก check ผ่านบนของจริง ไม่มี gap ที่ยังไม่ได้รับการยอมรับ
  ISSUES        พบ defect ที่พิสูจน์ได้ (ระบุทุกข้อ)
  BLOCKED       ทดสอบไม่ได้ เพราะ environment หรือสิ่งที่ต้องมีขาดไป
  INCONCLUSIVE  ทดสอบแล้วแต่สรุปไม่ได้ ไม่นับว่าผ่าน
-->

## สรุปสำหรับผู้ใช้

<fill: 2-3 ประโยค ผลเป็นอย่างไร ควร commit หรือไม่ และมีอะไรที่ผู้ใช้ต้องตัดสินใจ>

## สิ่งที่ทดสอบ

| # | Check | คำสั่งหรือวิธี | ผล | หลักฐาน |
|---|---|---|---|---|
| 1 | <fill> | `<fill>` | <fill: ผ่าน / ไม่ผ่าน / ไม่ได้ทดสอบ> | <fill: output ที่ตัดมาเฉพาะส่วนที่ชี้ขาด หรือ path ของไฟล์หลักฐาน> |

## Reproduction ก่อนและหลังแก้ (bug-fix)

- **ก่อนแก้ ที่ revision** `<fill>`: <fill: output ที่ fail>
- **หลังแก้ ที่ revision** `<fill>`: <fill: output ที่ pass>
- **test ใหม่ fail ได้จริงบน revision เก่า:** <fill: ใช่ พร้อมหลักฐาน หรือ ไม่ได้ตรวจ พร้อมเหตุผล>

<!-- ถ้าไม่ใช่ bug-fix ให้เขียน "ไม่เกี่ยวข้อง" -->

## Parity (migration)

- **MATCH / DIFF / UNREACHABLE:** <fill: ตัวเลขจาก parity.py ในรูปแบบ "12 / 0 / 0" หรือ "ไม่เกี่ยวข้อง">
- **Ignored paths ที่ใช้ และ decision ที่อนุมัติ:** <fill>
- **Side effect ที่ตรวจเพิ่ม (DB, ข้อความ, ไฟล์):** <fill>

## ปัญหาที่พบ

<fill: ทุก defect ที่พิสูจน์ได้ ข้อละบรรทัด พร้อม file:line หรือคำสั่งกับ output หรือ "ไม่พบ">

## สิ่งที่ยังไม่ได้ทดสอบ (gap)

<fill: สิ่งที่ไม่ได้ทดสอบและเหตุผล gap ไม่นับว่าผ่าน หรือ "ไม่มี">

## เรื่องที่ต้องให้ผู้ใช้ตัดสินใจ

<fill: ลิงก์ไปยัง decision request ที่เกี่ยวข้อง หรือ "ไม่มี">

## คำแนะนำเรื่อง commit

<fill: qa แนะนำว่าพร้อม commit หรือไม่ และเพราะอะไร ผู้ใช้เป็นคนตัดสินใจ>

## Commit (lead เป็นผู้เติมหลังผู้ใช้อนุมัติ)

| SHA | Message | อนุมัติเมื่อ |
|---|---|---|
