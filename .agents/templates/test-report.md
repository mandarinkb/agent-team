# รายงานผลการทดสอบ: <fill: ชื่องาน>

- **Job:** <fill>
- **Verdict:** <fill: PASS | FAIL | BLOCKED>
- **Revision:** <fill: tree id ที่ทดสอบรอบสุดท้าย>
- **Reset:** <fill: คำสั่ง reset และ seed ที่รันก่อนการทดสอบรอบสุดท้าย หรือ "งานนี้ไม่ใช้ฐานข้อมูล">
- **Commit:** ดูจาก `job.py status` หลัง git commit
- **ผู้ทดสอบ:** qa

## สรุปสำหรับผู้ใช้

<fill: 3 บรรทัด ทำอะไร ผลเป็นอย่างไร มีอะไรต้องรู้>

## ผลทีละ Acceptance criterion

| AC | วิธีทดสอบ | ผล | หลักฐาน |
|---|---|---|---|
| <fill> | <fill> | <fill: PASS / FAIL> | <fill: evidence/...> |

## Bruno

- **คำสั่ง:** `<fill>`
- **ผล:** <fill: requests / assertions / tests ผ่านกี่ข้อจากกี่ข้อ>
- **ไฟล์ผล:** <fill: evidence/...json>

## ฐานข้อมูล (ทีละ column)

<fill: สรุปจาก evidence/*-db.md ทุก task หรือ "งานนี้ไม่แตะฐานข้อมูล">

## Migration parity

<fill: จำนวนที่ตรงกับ baseline, ส่วนต่างที่ยอมรับพร้อมเลข decision หรือ "ไม่ใช่งาน migration">

## ประวัติแต่ละรอบ

| Task | รอบ | ผล | Fix task |
|---|---|---|---|
| <fill> | <fill> | <fill> | <fill> |

## สิ่งที่ไม่ได้ทดสอบ

<fill: ทุกอย่างที่ไม่ได้ทดสอบ และเหตุผล หรือ "ไม่มี" สิ่งที่อยู่ในหัวข้อนี้ไม่นับว่าผ่าน>
