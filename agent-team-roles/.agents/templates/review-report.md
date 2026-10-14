# รายงานการรีวิวโค้ด: {{TITLE}}

- **Task:** {{TASK_ID}}
- **Workflow:** {{KIND}}
- **Verdict:** <fill: NO_FINDINGS | FINDINGS | BLOCKED>
- **Revision:** <fill: tree id จาก git write-tree ที่ git ส่งมา ตัวเดียวกับที่ qa ทดสอบ>
- **Round:** <fill: 1, 2 หรือ 3 รอบที่ 4 ขึ้นไปต้องมี D9 ที่ผู้ใช้อนุมัติ>
- **Round approval:** <fill: ไม่ต้อง หรืออ้าง D9 ใน decisions.md ที่อนุมัติรอบเพิ่ม>
- **Diff:** <fill: คำสั่งที่ใช้ดู diff เช่น git -C <worktree> diff --cached>
- **Reviewed by:** reviewer (<fill: model>)
- **High risk:** <fill: ไม่ใช่ หรือ ใช่ พร้อมระบุ auth / เงิน / ข้อมูลส่วนบุคคล / สิทธิ์ / data migration / ความปลอดภัย>
- **Second review:** <fill: ไม่ต้อง / ส่งคำขอให้ผู้ใช้ตัดสินแล้ว (decision-<n>.md) / ทำแล้วด้วยโมเดล ... / ผู้ใช้ตัดสินว่าไม่ต้อง>
- **Date:** {{DATE}}

<!--
ส่วนบนจนถึง "สิ่งที่ไม่ได้รีวิว" reviewer เป็นผู้เขียน ห้ามมีช่องกรอกของ reviewer (fill) เหลือ ไม่อย่างนั้น gate_reports.py จะไม่ยอมให้ปิดงาน review
ส่วน "การคัดกรองของ lead" lead เป็นผู้เขียน ห้ามมีช่องกรอกของ lead เหลือ ไม่อย่างนั้น guard_git.py จะไม่ยอมให้ commit
Verdict:
  NO_FINDINGS  ตรวจครบทุกมุมที่เกี่ยวข้องแล้วไม่พบปัญหา
  FINDINGS     พบปัญหาอย่างน้อยหนึ่งข้อ (ทุกระดับความรุนแรง)
  BLOCKED      รีวิวไม่ได้ เช่น diff ไม่ตรงกับ tree id หรือไม่มี brief/design ให้เทียบ
-->

## สรุปสำหรับผู้ใช้

<fill: 2-3 ประโยค โค้ดนี้มีปัญหาที่ควรแก้ก่อน commit หรือไม่ และเรื่องที่ควรรู้>

## มุมที่ตรวจ

| มุม | ตรวจ | หมายเหตุ |
|---|---|---|
| Correctness | <fill: ใช่ / ไม่เกี่ยว> | <fill> |
| Root cause หรือปิดอาการ | <fill> | <fill> |
| Security | <fill> | <fill> |
| Structure | <fill> | <fill> |
| Verification (test ทดสอบพฤติกรรมจริงไหม) | <fill> | <fill> |
| Complexity budget | <fill> | <fill> |
| Clutter | <fill> | <fill> |
| ตรงกับที่ผู้ใช้อนุมัติ | <fill> | <fill> |

## Findings

<fill: ตารางด้านล่าง หรือเขียนว่า "ไม่พบ">

| # | ระดับ | file:line | ปัญหา | หลักฐาน | ข้อเสนอ |
|---|---|---|---|---|---|

## สิ่งที่ไม่ได้รีวิว

<fill: ส่วนที่ไม่ได้ดูและเหตุผล หรือ "ไม่มี">

## การคัดกรองของ lead

### แก้ก่อน commit
<lead: เลข finding พร้อมเหตุผล หรือ "ไม่มี">

### ควรพิจารณา
<lead: เลข finding พร้อม trade-off ถ้าการแก้ต้องเปลี่ยน design ให้ส่งเป็นคำขอให้ผู้ใช้ตัดสิน>

### รับทราบ
<lead: เลข finding ที่ถูกต้องแต่ยังไม่ต้องทำตอนนี้>

### ปัดตก
<lead: เลข finding พร้อมเหตุผล การปัดตก finding ระดับ critical ต้องให้ผู้ใช้ตัดสิน (D3)>

### หลังแก้
<lead: tree id ใหม่ และผลการรีวิวซ้ำของส่วนที่แก้ หรือ "ไม่มีการแก้">
