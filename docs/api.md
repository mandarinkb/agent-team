# Registration API

สัญญาระหว่าง frontend และ backend คำศัพท์อ้างอิงจาก `GLOSSARY.md`

## POST /api/users

สมัครสมาชิก สร้าง User ใหม่

### Request

`Content-Type: application/json`

```json
{ "email": "a@example.com", "password": "secret123", "displayName": "Alice" }
```

### กฎของข้อมูล (backend ตัดสิน, frontend ตรวจซ้ำเพื่อ UX)

| ช่อง | กฎ |
|---|---|
| `email` | trim แล้วต้องเป็นรูปแบบอีเมลที่ถูกต้อง, แปลงเป็น lowercase ก่อนบันทึกและก่อนเทียบซ้ำ |
| `password` | 8 ตัวอักษรขึ้นไป และไม่เกิน 72 bytes (นับเป็น bytes ของ UTF-8), ไม่บังคับรูปแบบอื่น, ห้าม trim |
| `displayName` | trim แล้วยาว 1–50 ตัวอักษร, ไม่ต้องไม่ซ้ำกับคนอื่น |

### Responses

**201 Created**

```json
{ "id": 1, "email": "a@example.com", "displayName": "Alice" }
```

ห้ามคืน `password` หรือ hash ในทุกกรณี

**400 Bad Request** (JSON ผิดรูปแบบ หรือข้อมูลไม่ผ่านกฎ)

```json
{ "errors": { "email": "invalid email", "password": "too short" } }
```

คีย์ใน `errors` เป็นชื่อช่อง (`email`, `password`, `displayName`) ค่าเป็นข้อความสั้นภาษาอังกฤษ ถ้า body อ่านเป็น JSON ไม่ได้ ให้ใช้คีย์ `"body"`

**409 Conflict** (อีเมลซ้ำ)

```json
{ "errors": { "email": "email already registered" } }
```

**500 Internal Server Error**

```json
{ "errors": { "server": "internal error" } }
```

## การจัดเก็บ

- ตาราง `users`: `id` (PK), `email` (UNIQUE, lowercase), `display_name`, `password_hash` (bcrypt), `created_at`
- กันอีเมลซ้ำด้วย UNIQUE constraint ในฐานข้อมูล และแปลง error ของ constraint เป็น 409 (กัน race condition)

## การรัน

- backend ฟังที่ `:8080` ไฟล์ SQLite ตั้งผ่าน env `DB_PATH` (ค่าเริ่มต้น `backend/data/app.db`)
- frontend ใช้ Vite dev server พอร์ต `5173` และ proxy `/api` ไปที่ `http://localhost:8080`

## นอกขอบเขตรอบนี้

login, ยืนยันอีเมล, reset password, dashboard, rate limiting, HTTPS
