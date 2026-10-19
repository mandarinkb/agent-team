# Spec review: <fill: T-nn> รอบ <fill: n>

- **Task:** <fill: T-nn>
- **Revision:** <fill: tree id จาก git write-tree ใน worktree>
- **Verdict:** <fill: PASS | FAIL>
- **Bruno coverage:** <fill: PASS | FAIL | n/a (task ไม่ได้ verify ด้วย bruno)>
- **Reviewer:** spec-reviewer

## ทีละ criterion

| AC | spec กำหนด | โค้ดทำ (file:line) | ตรง? |
|---|---|---|---|
| <fill> | <fill> | <fill> | <fill: ตรง / ไม่ตรง> |

## Bruno coverage

ตรวจ collection ใน `bruno/<job>/` เทียบกับ spec ว่าทุก AC ของ task มี request ที่ assert body หรือ header ตาม API contract ไม่ใช่แค่ status

| AC | ไฟล์ .bru | สิ่งที่ assert | พอไหม |
|---|---|---|---|
| <fill> | <fill> | <fill> | <fill: พอ / ไม่พอ> |

## นอก spec

<fill: สิ่งที่โค้ดทำเกินหรือขาดจาก spec, ปัญหาความปลอดภัย, ไฟล์นอก scope หรือ "ไม่มี">

## Fix tasks ที่เขียน

<fill: fixes/F-n.md หรือ "ไม่มี">
