# {{TASK}}: {{TITLE}}

- **Job:** {{JOB}}
- **Task:** {{TASK}}
- **Owner:** {{OWNER}}
- **Criteria:** {{ACS}}
- **Scope (may write):** {{SCOPE}}
- **Verify by:** {{VERIFY}}

ไฟล์นี้คือ brief ทั้งหมดของ teammate ที่หยิบงาน teammate ถามกลับระหว่างทำไม่ได้ ถ้าเติมช่องไหนไม่ได้ แปลว่างานยังไม่พร้อม

```
GOAL         <fill: หนึ่งประโยค>
CONTEXT      <fill: file:line ที่ต้องอ่าน, หัวข้อใน spec.md, รายงานของ analyst>
MAY NOT      <fill: path ของ task อื่นและสิ่งที่อยู่นอก scope>
DONE WHEN    <fill: สิ่งที่ owner ตรวจเองได้ก่อนส่ง เช่น build ผ่าน, unit test ผ่าน>
FORBIDDEN    ห้ามแก้นอก scope, ห้าม commit/push, ห้ามเขียนฐานข้อมูลผ่าน MCP, ห้ามแก้ไฟล์ใน bruno/
```

## หมายเหตุ

<fill: สิ่งที่ owner ต้องรู้ หรือ "ไม่มี">
