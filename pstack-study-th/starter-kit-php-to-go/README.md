# ชุดเริ่มต้น: ย้าย API จาก PHP เป็น Go ด้วยแนวทางของ pstack

[← กลับไปหน้ารวม](../README.md)

ชุดนี้นำ pattern ที่สรุปไว้ใน [Design Patterns](../PSTACK-DESIGN-PATTERNS-TH.md) มาทำเป็นของที่ใช้กับงานย้าย API จาก PHP เป็น Go ได้ทันที โดยต่อจากแผนใน [`PSTACK-DEV-SETUP-TH.md`](../../PSTACK-DEV-SETUP-TH.md) หัวข้อ 3

> **สถานะการทดสอบ:**
> - `parity.py` ผ่าน test 8 ข้อ และได้ลองใส่บั๊ก 2 แบบ ซึ่ง test จับได้ทั้งสองแบบ
> - project playbook ผ่าน `check-playbooks.mjs` ของ pstack
> - `check_rules.py` ผ่าน และจับได้เมื่อประโยคในกฎถูกแก้
> - **ยังไม่ได้ทดสอบกับ API PHP หรือ Go จริง** และยังไม่ได้รัน poteto-mode กับ playbook นี้จริง

---

## มีอะไรอยู่ในชุดนี้

```
starter-kit-php-to-go/
├── .agents/playbooks/php-to-go-endpoint.md   project playbook ต่อจาก Refactoring
├── templates/endpoint-brief.md               brief สำหรับ subagent + checklist PHP→Go
├── scripts/parity.py                         บันทึก baseline จาก PHP แล้วเทียบกับ Go
├── scripts/test_parity.py                    test ของ parity.py
├── scripts/check_rules.py                    ตรวจว่ากฎใน CLAUDE.md ยังอยู่ครบ
├── rules.json                                กฎที่ตรึงไว้ พร้อมที่มาของแต่ละข้อ
├── CLAUDE.md.snippet                         กฎสำหรับเพิ่มใน CLAUDE.md ของโปรเจกต์
└── examples/orders/                          ตัวอย่าง cases.jsonl และ parity.json
```

แต่ละไฟล์มาจาก pattern ไหน

| ไฟล์ | Pattern ของ pstack |
|---|---|
| `php-to-go-endpoint.md` | project playbook ที่ `extends` playbook หลักและยกข้อความมาตรง ๆ ([Workflow Design](../PSTACK-WORKFLOW-DESIGN-TH.md) หัวข้อ 4) |
| `endpoint-brief.md` | brief template ของ Orchestrate: "The brief is the product" ([Deep Dive](../PSTACK-DEEP-DIVE-TH.md)) |
| `parity.py` | Build the Lever + Refactoring ขั้นที่ 1 ตรึงพฤติกรรมเดิมก่อนย้าย + exit code แยกประเภท และ unknown ไม่นับว่าผ่าน ([Design Patterns](../PSTACK-DESIGN-PATTERNS-TH.md) หัวข้อ 3) |
| `test_parity.py` | test พฤติกรรม ไม่ใช่ implementation และทุก check ต้องพิสูจน์ได้ว่า fail ได้จริง |
| `check_rules.py` + `rules.json` | ตรึงกฎด้วยประโยค + อ้างถึงที่มา (`skill-rules.test.mjs`) |

**ทำไมไฟล์ที่ agent อ่านเป็นภาษาอังกฤษ:** playbook ต้องยกข้อความของ playbook หลักของ pstack ซึ่งเป็นภาษาอังกฤษ มาให้ตรงทุกตัวอักษร และ skill ของ pstack ทั้งหมดก็เป็นภาษาอังกฤษ จึงเขียนให้เข้ากัน ส่วนเอกสารที่คนอ่านเป็นภาษาไทย

---

## ติดตั้งในโปรเจกต์ของคุณ

ให้ `<repo>` คือ root ของโปรเจกต์ที่จะย้าย

```bash
KIT=path/to/pstack-study-th/starter-kit-php-to-go
mkdir -p <repo>/.agents/playbooks <repo>/scripts <repo>/templates <repo>/parity
cp $KIT/.agents/playbooks/php-to-go-endpoint.md <repo>/.agents/playbooks/
cp $KIT/scripts/parity.py $KIT/scripts/test_parity.py $KIT/scripts/check_rules.py <repo>/scripts/
cp $KIT/templates/endpoint-brief.md <repo>/templates/
cp $KIT/rules.json <repo>/
cat $KIT/CLAUDE.md.snippet >> <repo>/CLAUDE.md
```

จากนั้น
1. **แก้ `rules.json`** ให้ช่อง `file` ชี้ไปที่ `CLAUDE.md` แทน `CLAUDE.md.snippet`
2. **ตรวจว่าทุกอย่างอยู่ครบ**
   ```bash
   python3 scripts/check_rules.py
   python3 scripts/test_parity.py
   node <pstack plugin>/skills/poteto-mode/scripts/check-playbooks.mjs .
   ```
3. **ใส่ `check_rules.py` และ `test_parity.py` ใน CI** กฎจะได้ไม่หายแบบไม่มีใครรู้
4. **รัน `/pstack:create-verification-skill`** ถ้ายังไม่มี skill สำหรับขับแอป (playbook ของ pstack หลายตัวต้องใช้)

`parity.py` ต้องใช้ Python 3.9 ขึ้นไป และใช้แค่ standard library ไม่ต้องติดตั้งอะไรเพิ่ม

---

## วิธีใช้ทีละ endpoint

### 1. เตรียม case และบันทึก baseline จาก PHP
สร้าง `parity/orders/cases.jsonl` บรรทัดละหนึ่ง request ดูตัวอย่างได้ที่ `examples/orders/cases.jsonl`

```json
{"id": "list-happy", "method": "GET", "path": "/api/orders?user_id=1001", "headers": {"Authorization": "Bearer ${PARITY_TOKEN}"}}
```

- `id` ต้องไม่ซ้ำกัน
- token ให้ใส่เป็น `${ENV_VAR}` **ห้ามเขียน token จริงลงในไฟล์**
- ใช้บัญชีสำหรับทดสอบเท่านั้น **ห้ามใช้ข้อมูลลูกค้าจริง**
- ตอนบันทึก script จะตัด header `authorization`, `cookie`, `set-cookie`, `date` และ `x-request-id` ทิ้ง

```bash
export PARITY_TOKEN=...
python3 scripts/parity.py record --base-url http://localhost:8080 \
  --cases parity/orders/cases.jsonl --out parity/orders/baseline.jsonl
```

### 2. สั่ง agent
```text
Use poteto-mode to port GET /api/orders from PHP to Go.
Follow the project playbook php-to-go-endpoint.
```
poteto-mode จะอ่าน playbook Refactoring แล้วใช้การเปลี่ยนแปลงจาก project playbook ทับลงไป คือ เขียน brief ก่อน → ใช้ baseline เป็นตัวตรึงพฤติกรรม → ใช้ `blast-radius` หาผู้เรียก → **ไม่ลบ PHP** → ตรวจด้วย parity → นับผลเป็น MATCH, DIFF และ UNREACHABLE → บันทึก decision log → หยุดที่พร้อม merge

### 3. ตรวจ Go ด้วยตัวเองได้ทุกเมื่อ
```bash
python3 scripts/parity.py check --base-url http://localhost:8081 \
  --baseline parity/orders/baseline.jsonl --config parity/orders/parity.json
```

**ตัวอย่าง output จริง** (จากการทดสอบกับ server จำลอง ที่ให้ Go ตอบแบบที่ port มาแล้วมักพลาด)
```
DIFF        list-happy
    $.data[0].id: type string -> number ("17" -> 17)
    $.data[0].tags: type array -> null ([] -> null)
    $.data[0].total: type string -> number ("10.50" -> 10.5)
DIFF        list-empty
    $.data: type array -> null ([] -> null)
MATCH       get-not-found

MATCH 1  DIFF 2  UNREACHABLE 0  of 3
```
exit code คือ 1 สำหรับ agent ให้ใช้ `--json` แล้วอ่าน `counts` กับ `results`

| Exit | ความหมาย |
|---|---|
| 0 | ทุก case ตรงกับ baseline |
| 1 | มีอย่างน้อยหนึ่ง case ต่างจาก baseline |
| 2 | input ผิด เช่น id ซ้ำ, ไฟล์อ่านไม่ได้ หรือไม่ได้ตั้ง env var |
| 3 | ไม่มี case ไหนต่าง แต่มี case ที่เรียกไม่ถึง **ถือว่า inconclusive ไม่นับว่าผ่าน** |

### 4. `parity.json`
```json
{
  "compare_headers": ["content-type", "cache-control"],
  "ignore_paths": ["$.meta.request_id", "$.data[*].updated_at"],
  "max_diffs": 20,
  "timeout": 10
}
```
- `ignore_paths` รองรับ `[*]` (ทุก index ใน array) และ `*` (key ใดก็ได้)
- **ทุก path ที่ ignore ต้องมีเหตุผลเขียนไว้ใน brief** ห้ามเพิ่ม ignore เพื่อให้ diff หายไปเฉย ๆ

---

## script นี้เทียบอะไร และไม่เทียบอะไร

**เทียบ**
- status code
- header ตามที่ระบุไว้ใน `compare_headers`
- body ที่เป็น JSON แบบละเอียด ได้แก่ **type** (`"1"` กับ `1` ถือว่าต่าง), key ที่หายไปหรือเกินมา, ความยาวของ array, ลำดับใน array และค่าแต่ละตัว
- ลำดับของ key ใน object ไม่นับ

**ไม่เทียบ (ข้อจำกัดที่ควรรู้)**
- **ข้อความ JSON ดิบ:** `"é"` กับ `"é"` และ `"\/"` กับ `"/"` ถือว่าเท่ากัน เพราะเทียบหลัง parse แล้ว ถ้า client เปรียบเทียบเป็น string ต้องเพิ่ม case ตรวจเอง
- **ตัวเลข:** `10.50` กับ `10.5` ที่เป็น number เท่ากันหลัง parse
- **side effect:** ไม่ได้ตรวจการเขียน DB ส่งอีเมล หรือเรียก service อื่น endpoint ที่เขียนข้อมูลต้องตรวจด้วย verification skill หรือ query DB เพิ่ม
- **request ที่ไม่ deterministic:** ถ้า response ขึ้นกับเวลาหรือข้อมูลที่เปลี่ยนไป ให้ใช้ข้อมูลทดสอบที่คงที่ หรือ ignore path นั้นพร้อมเหตุผล

---

## ขั้นต่อไปที่แนะนำ

1. ลองกับ endpoint ที่อ่านอย่างเดียวและเสี่ยงต่ำก่อน 1 ตัว แล้วดูว่าขั้นตอนเหมาะกับทีมไหม ตรงกับขั้น Pilot ของ Orchestrate
2. รัน `/reflect` หลังจบ endpoint แรก แล้วนำบทเรียนที่ผ่านการคัดกรองมาเพิ่มใน `CLAUDE.md` และ `rules.json`
3. เมื่อมั่นใจแล้ว ถ้าจะย้ายหลาย endpoint ให้ใช้ Multi-phase plan วางแผนก่อน แล้วรันด้วย Autopilot-stack (ดูต้นทุนก่อนใน [ข้อจำกัดของ pstack](../PSTACK-LIMITATIONS-TH.md))
