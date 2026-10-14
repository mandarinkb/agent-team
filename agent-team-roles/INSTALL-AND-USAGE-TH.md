# คู่มือติดตั้งและใช้งานทีม Agent

คู่มือนี้บอกขั้นตอนติดตั้งและใช้งานทีม teammate ในโฟลเดอร์ `agent-team-roles/` ตั้งแต่ต้นจนจบ ส่วนเหตุผลของการออกแบบและรายละเอียดของแต่ละส่วน อยู่ใน [README-TH.md](README-TH.md)

> **สถานะ:** script และ hook ผ่าน test 68 ข้อ แต่ทีมยังไม่เคยรันกับ Agent Teams จริง แนะนำให้ทำตามหัวข้อ 4 (ลองครั้งแรก) ก่อนใช้กับงานจริง

---

## สารบัญ

1. [สิ่งที่ต้องมี](#1-สิ่งที่ต้องมี)
2. [ติดตั้งลงโปรเจกต์](#2-ติดตั้งลงโปรเจกต์)
3. [ตั้งค่าครั้งแรกหลังติดตั้ง](#3-ตั้งค่าครั้งแรกหลังติดตั้ง)
4. [ลองครั้งแรก](#4-ลองครั้งแรก)
5. [ใช้งานประจำวัน](#5-ใช้งานประจำวัน)
6. [หน้าที่ของคุณระหว่างทีมทำงาน](#6-หน้าที่ของคุณระหว่างทีมทำงาน)
7. [หยุดงานและกลับมาทำต่อ](#7-หยุดงานและกลับมาทำต่อ)
8. [ทบทวนงานและปรับทีม](#8-ทบทวนงานและปรับทีม)
9. [เมื่อ teammate ติดวน](#9-เมื่อ-teammate-ติดวน)
10. [แก้ไขและอัปเดตชุด](#10-แก้ไขและอัปเดตชุด)
11. [แก้ปัญหาที่พบบ่อย](#11-แก้ปัญหาที่พบบ่อย)
12. [คำสั่งอ้างอิง](#12-คำสั่งอ้างอิง)

---

## 1. สิ่งที่ต้องมี

| สิ่งที่ต้องมี | ใช้ทำอะไร | ตรวจด้วย |
|---|---|---|
| Claude Code ที่รองรับ Agent Teams | รันทีม | `claude --version` (เครื่องคุณตอนนี้คือ 2.1.295) |
| Python 3.9 ขึ้นไป | script ทั้งหมดในชุด (ใช้แค่ standard library) | `python3 --version` |
| git | branch, worktree, stage และ commit | `git --version` |
| โปรเจกต์ที่เป็น git repository | hook เทียบ tree id และ worktree ต้องใช้ git | `git -C <project> status` |
| tmux หรือ iTerm2 (ไม่บังคับ) | ถ้าอยากเห็น teammate แยก pane | `which tmux` |

**ไม่ต้องติดตั้ง pstack** เพราะ skill ของ pstack ที่ทีมใช้ถูกคัดลอกมาไว้ในชุดแล้ว ถ้าคุณติดตั้ง pstack ไว้ ให้ปิด hook ของ pstack (`session hook: off` ใน `~/.claude/pstack-models.md`) เพื่อไม่ให้ teammate ถูกส่งเข้า `poteto-mode` ซ้อนอีกชั้น

---

## 2. ติดตั้งลงโปรเจกต์

### 2.1 รัน install

ให้ `<project>` คือ root ของโปรเจกต์ที่จะใช้ทีม เช่น repo ของ API PHP ที่จะย้ายเป็น Go

```bash
cd /path/to/pstack-claude-main/agent-team-roles
python3 install.py /path/to/<project>
```

`install.py` ทำสิ่งต่อไปนี้ และรันการตรวจให้ในตอนท้าย

| สิ่งที่ทำ | ปลายทาง |
|---|---|
| คัดลอกชุดทั้งหมด | `<project>/.agents/` |
| คัดลอก teammate 6 บทบาท | `<project>/.claude/agents/` |
| คัดลอก skill 18 ตัว (รวม `references/`) | `<project>/.claude/skills/` |
| สร้างหรือเพิ่ม import ใน `CLAUDE.md` | `<project>/CLAUDE.md` (เพิ่มบรรทัด `@.agents/AGENTS.md`) |
| สร้าง settings ถ้ายังไม่มี | `<project>/.claude/settings.json` |

บรรทัดสุดท้ายต้องเป็น `OK: 6 teammates, 18 skills, 0 problem(s)`

**ถ้าไฟล์มีอยู่แล้วแต่เนื้อหาต่างกัน** install จะข้ามไฟล์นั้นและบอกไว้ ถ้าต้องการทับ ให้รันใหม่พร้อม `--force` แต่ `.claude/settings.json` จะไม่ถูกทับในทุกกรณี

### 2.2 รวม settings (เฉพาะกรณีที่โปรเจกต์มี `.claude/settings.json` อยู่แล้ว)

install จะแจ้งว่า `merge permissions, hooks, and env ... by hand` ให้คัดลอก 3 ส่วนจาก `<project>/.agents/settings.example.json` ไปรวมกับไฟล์ที่มีอยู่

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "permissions": {
    "ask": ["Bash(git commit *)", "Bash(git push *)", "Bash(git merge *)", "Bash(git rebase *)", "Bash(gh pr create *)"],
    "deny": ["Bash(git push --force *)", "Bash(git push -f *)", "Bash(git push --force-with-lease *)",
             "Bash(git reset --hard *)", "Bash(git clean *)", "Bash(git branch -D *)", "Bash(gh pr merge *)"]
  },
  "hooks": {
    "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command",
      "command": "python3 \"${CLAUDE_PROJECT_DIR}/.agents/scripts/hooks/guard_git.py\""},
      {"type": "command",
      "command": "python3 \"${CLAUDE_PROJECT_DIR}/.agents/scripts/hooks/loop_guard.py\""}]}],
    "TaskCompleted": [{"hooks": [{"type": "command",
      "command": "python3 \"${CLAUDE_PROJECT_DIR}/.agents/scripts/hooks/gate_reports.py\""}]}]
  }
}
```

**ส่วน `permissions` และ `hooks` สำคัญที่สุด:**
- ask rule ทำให้ทุก commit ต้องให้คุณอนุมัติ และเอกสาร Claude Code ระบุว่าถามทุกโหมด แม้ใน auto mode
- hook ตรวจรายงานก่อน commit และไม่ยอมให้ปิดงาน verify หรือ review ถ้ารายงานยังไม่เสร็จ

**เรื่อง `env`:** `~/.claude/settings.json` ของคุณตั้ง `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` ไว้แล้ว ซึ่งเปิด Agent Teams ทุกโปรเจกต์ ถ้าต้องการเปิดเฉพาะโปรเจกต์นี้ ให้ลบค่านั้นออกจากไฟล์ของผู้ใช้ แล้วใช้ค่าในไฟล์ของโปรเจกต์แทน

### 2.3 ตรวจผลการติดตั้ง

```bash
cd /path/to/<project>
python3 .agents/scripts/check_team.py --installed
python3 .agents/scripts/sync_claude.py --check
```

ทั้งสองคำสั่งต้องผ่าน คือได้ `OK` และ `0 stale`

**ถ้าอยากรัน test ของชุดด้วย** (ไม่บังคับ) ให้รันในโฟลเดอร์ `agent-team-roles/`
```bash
for t in tests/*.py; do python3 $t; done
```

---

## 3. ตั้งค่าครั้งแรกหลังติดตั้ง

### 3.1 เขียนข้อมูลโปรเจกต์ใน `CLAUDE.md`

teammate ทุกตัวอ่าน `CLAUDE.md` ข้อมูลที่ชัดตรงนี้ช่วยประหยัด token และลดการที่ qa รายงาน `BLOCKED` ให้เขียนไว้เหนือบรรทัด `@.agents/AGENTS.md`

```markdown
# Project

## How to run
- PHP API: `docker compose up php` → http://localhost:8080
- Go API: `make run` → http://localhost:8081
- Test data: `make seed-test` (บัญชีทดสอบ user_id 1001, 1002)
- Auth for tests: export PARITY_TOKEN จาก `scripts/test-token.sh`

## Commands
- Go build/test/lint: `go build ./...`, `go test ./...`, `golangci-lint run`
- PHP tests: `vendor/bin/phpunit`

## Layout
- PHP handlers: `app/Http/Controllers/Api/`
- Go: `internal/<domain>/`, routes in `cmd/api/routes.go`

## Conventions
- Go errors: ...

@.agents/AGENTS.md
```

ตัวอย่างข้างบนเป็นแค่รูปแบบ ให้แทนด้วยคำสั่งและ path จริงของโปรเจกต์คุณ

### 3.2 ให้ทีมสร้าง skill `verify` ของโปรเจกต์

ทำครั้งเดียวก่อนงานแรก เพื่อให้ qa มีขั้นตอนตายตัวในการเปิด PHP และ Go, ตรวจว่าพร้อม, ขับ API และปิด

1. เปิด Claude Code ในโปรเจกต์ (`cd <project> && claude`)
2. พิมพ์:
   ```text
   ให้ qa ใช้ create-verification-skill สร้าง verify skill ของโปรเจกต์นี้
   ```
3. คุณจะได้คำขอให้ตัดสินใจ (D4) ให้อนุมัติ
4. qa สร้าง `.claude/skills/verify/` แล้วลองรันจริงหนึ่งรอบ จากนั้นไฟล์จะผ่านการรีวิวและการอนุมัติ commit เหมือนงานอื่น

### 3.3 (ไม่บังคับ) ตั้งคำตัดสินที่ใช้ซ้ำได้ล่วงหน้า

ถ้ามีเรื่องที่รู้แน่อยู่แล้วว่าจะตอบเหมือนเดิมทุกครั้ง เพิ่มไว้ใน `.agents/standing-decisions.md` ได้เลย ทีมจะได้ไม่ต้องถามซ้ำ

```markdown
## SD-1: คง ID เป็น string ตาม PHP
- **Codes:** D2
- **Scope:** migration PHP เป็น Go ทั้งหมด
- **Ruling:** "ID ทุกตัวใน response ของ Go ต้องเป็น string เหมือน PHP"
- **Recorded:** 2026-10-09, ผู้ใช้เขียนเอง
- **Status:** active
```

แล้วรัน `python3 .agents/scripts/check_team.py --installed` ตรวจรูปแบบ เรื่อง D7, D8 และ D11 ใส่ไม่ได้ เพราะต้องถามคุณทุกครั้ง

---

## 4. ลองครั้งแรก

แนะนำให้ลองตามลำดับนี้ก่อนใช้กับงานจริง เพื่อดูว่าแต่ละกลไกทำงานจริง

| ขั้น | สิ่งที่สั่ง | สิ่งที่ควรเห็น |
|---|---|---|
| 1 | "ให้ analyst และ qa สืบบั๊ก <บั๊กที่คุณรู้คำตอบแล้ว> ตาม workflow bug-fix แค่ถึงขั้นหา root cause" | analyst รายงาน root cause พร้อมหลักฐาน และคุณได้คำขอให้อนุมัติแผน (G1) |
| 2 | ปฏิเสธแผนแล้วบอกว่าหยุดแค่นี้ | lead ไม่ลงมือแก้เอง และบันทึกคำตอบของคุณใน `decisions.md` |
| 3 | สร้าง branch ทดลอง แล้วสั่ง "ให้ git commit ไฟล์ README ที่แก้ใน branch นี้" | prompt ขออนุมัติเด้งขึ้นที่ session ของ lead พร้อมข้อความว่าไม่ได้ตรวจรายงาน เพราะไม่มีบรรทัด `Task:` |
| 4 | ทำ migration endpoint ที่อ่านอย่างเดียว 1 ตัวเป็น pilot (หัวข้อ 5.3) | ได้รายงานผลทดสอบและรายงานรีวิว และ prompt commit บอกว่า tree ตรงกับรายงาน |
| 5 | ดูค่าใช้จ่ายด้วย `/usage` | ประเมินว่าควรใช้โมเดลแบบไหน (หัวข้อ 10.3) |

---

## 5. ใช้งานประจำวัน

**วิธีสั่งงาน:** เปิด Claude Code ในโปรเจกต์ แล้วบอก lead ว่าใช้ workflow ไหน และต้องการ teammate ใคร ตั้งชื่อ teammate ให้ตรงกับบทบาท (agent type) เพื่อให้ได้นิยามบทบาทที่ถูกต้อง lead จะสร้างงานด้วย `new_task.py` และไฟล์ของงานอยู่ที่ `.agents/work/<task-id>/`

### 5.1 หาบั๊ก
```text
ใช้ workflow .agents/workflows/bug-fix.md
บั๊ก: หน้า /orders แสดงรายการว่างเมื่อผู้ใช้มีคำสั่งซื้อเกิน 100 รายการ
สร้างทีม: analyst-a และ analyst-b (agent type analyst), qa, backend, reviewer, git
ให้ analyst ทั้งสองคนตั้งสมมติฐานคนละข้อแล้วพยายามหักล้างกัน
```
ถ้าบั๊กไม่ซับซ้อน ใช้ analyst คนเดียวก็พอ ส่วน reviewer ข้ามได้เฉพาะงานแก้ไฟล์เดียวที่ไม่เสี่ยง

### 5.2 เพิ่มฟีเจอร์
```text
ใช้ workflow .agents/workflows/feature.md
ฟีเจอร์: ให้ GET /api/orders กรองตามสถานะได้หลายค่า (status[]=paid&status[]=shipped)
สร้างทีม: analyst, backend, qa, reviewer, git
```
คุณจะได้เลือก design อย่างน้อย 2 แบบที่ G1

### 5.3 ย้าย endpoint เดียว (PHP เป็น Go)
```text
ใช้ workflow .agents/workflows/migration.md
ย้าย GET /api/orders จาก PHP (http://localhost:8080) เป็น Go (http://localhost:8081)
นี่คือ endpoint แรก ทำเป็น pilot
สร้างทีม: analyst, backend, qa, reviewer, git
```

### 5.4 ย้ายหลาย endpoint (โปรแกรม)
```text
ใช้ workflow .agents/workflows/migration-program.md
ย้าย API ทั้งหมดใน app/Http/Controllers/Api จาก PHP เป็น Go
เริ่มด้วย analyst และ qa ก่อน แล้วค่อยเพิ่ม backend, reviewer, git เมื่อเริ่มหน่วยแรก
```
ดูความคืบหน้าได้ทุกเมื่อ:
```text
ขอสถานะโปรแกรม migration
```
lead จะรัน `migration_status.py` แล้วส่ง `STATUS.md` ที่คำนวณจากข้อมูลจริงให้ ไม่ได้รายงานจากความจำ

### 5.5 ลบโค้ด PHP หลังย้าย traffic แล้ว
```text
ฉันย้าย traffic ของ GET /api/orders ไป Go แล้ว และใช้งานมา 2 สัปดาห์ไม่มีปัญหา
ใช้ workflow .agents/workflows/migration-retire.md
```
การย้าย traffic เป็นงานของคุณเอง ทีมไม่ทำให้

### 5.6 คำแนะนำในการสั่งงาน
- **บอกชื่อ teammate ทุกครั้ง** (analyst, backend, qa, reviewer, git) เพื่อให้ได้นิยามบทบาทของชุดนี้
- **ทีม 3-5 คนกำลังดี** frontend กับ analyst คนที่สองเพิ่มเมื่อจำเป็นเท่านั้น
- **ถ้า lead เริ่มเขียนโค้ดเอง** ให้พิมพ์ "รอ teammate ทำงานให้เสร็จก่อน"
- **ถ้าอยากคุยกับ teammate ตรง ๆ** ใช้ลูกศรขึ้นลงเลือกใน agent panel แล้วกด Enter ถ้าต้องการให้ teammate หยุดงาน กด `x`

---

## 6. หน้าที่ของคุณระหว่างทีมทำงาน

คุณมีหน้าที่ 3 อย่าง

### 6.1 ตัดสินใจ
lead จะแสดงคำถามพร้อมตัวเลือกอย่างน้อย 2 ตัว ตัวที่แนะนำอยู่บนสุดและมีป้าย `(แนะนำ)` รายละเอียดเต็มอยู่ใน `.agents/work/<task-id>/decision-<n>.md`

- **เลือกตัวเลือก หรือพิมพ์คำตอบของคุณเอง** lead บันทึกคำพูดของคุณตรงตัวลง `decisions.md`
- **ถ้าเป็นเรื่องที่จะตอบเหมือนเดิมทุกครั้ง** บอก lead ว่า "ใช้คำตอบนี้กับกรณีแบบเดียวกันต่อไป ขอบเขต: ..." แล้ว lead จะเพิ่มเป็น standing decision
- **ถ้ายังไม่พร้อมตอบ ไม่ต้องตอบ** งานที่รอคำตอบจะหยุด แต่งานอื่นยังเดินต่อ ทีมไม่ถือว่าการเงียบคือการอนุมัติ

รหัสของการตัดสินใจ (รายละเอียดอยู่ใน `.agents/protocols/decisions.md`)

| รหัส | เรื่อง |
|---|---|
| D1 | เลือก design หรือวิธีแก้ |
| D2 | เปลี่ยนพฤติกรรม, API contract หรือรูปแบบข้อมูล |
| D3 | ยอมรับความต่าง เช่น DIFF ของ parity หรือ path ที่ ignore |
| D4 | เปลี่ยนขอบเขตงาน |
| D5 | เพิ่ม dependency หรือ service |
| D6 | schema หรือ data migration |
| D7 | การกระทำที่ย้อนกลับไม่ได้ เช่น push, merge, deploy หรือย้าย traffic |
| D8 | อนุมัติแผน (G1) และอนุมัติ commit (G2) |
| D9 | หยุดหรือเริ่มงานใหม่หลังเจอทางตัน |
| D10 | ใช้ทรัพยากรเพิ่ม เช่น รีวิวซ้ำด้วยอีกโมเดล หรือ retro แบบ full |
| D11 | เปลี่ยนกฎ, skill หรือ workflow ของทีม |

### 6.2 อ่านรายงาน
ก่อนอนุมัติ commit ให้อ่าน 2 ไฟล์

| ไฟล์ | ดูอะไร |
|---|---|
| `.agents/work/<task-id>/test-report.md` | **Verdict** (`PASS` / `ISSUES` / `BLOCKED` / `INCONCLUSIVE`), สรุปสำหรับผู้ใช้, สิ่งที่ยังไม่ได้ทดสอบ (gap), parity สำหรับ migration |
| `.agents/work/<task-id>/review-report.md` | **Verdict** (`NO_FINDINGS` / `FINDINGS` / `BLOCKED`), findings ระดับ critical และส่วน **การคัดกรองของ lead** โดยเฉพาะกลุ่ม "ปัดตก" ซึ่งคุณกลับคำตัดสินได้ |

ค่า `INCONCLUSIVE` และ gap **ไม่นับว่าผ่าน**

### 6.3 อนุมัติ commit
เมื่อ git รัน `git commit` จะมี prompt เด้งขึ้นที่ session ของ lead พร้อมข้อความจาก hook

| ข้อความที่เห็น | ความหมาย | ควรทำ |
|---|---|---|
| `Test report: PASS at ... Review: ... The staged content matches the reports.` | สิ่งที่จะ commit คือสิ่งที่ถูกทดสอบและรีวิวแล้ว | อนุมัติ ถ้ารายงานไม่มีปัญหา |
| `WARNING: the staged content differs from what qa tested` | มีการแก้ไฟล์หลังการตรวจ | **ปฏิเสธ** แล้วขอให้ทดสอบและรีวิวใหม่ที่ tree id ล่าสุด |
| `WARNING: the test verdict is ISSUES, not PASS` | ยังมี defect | ปฏิเสธ หรืออนุมัติถ้าคุณยอมรับ defect นั้นแล้ว |
| `Review: no review report.` | งานนี้ข้ามการรีวิว | ตรวจว่ามีเหตุผลการข้ามใน `log.tsv` |
| `no 'Task: <task-id>' line, so the test and review reports were not checked` | commit ที่ไม่ได้ผูกกับงาน เช่น commit ของ retro | ตรวจสิ่งที่ stage ไว้เองก่อนอนุมัติ |

ถ้าคุณปฏิเสธ git จะไม่ทำอะไรต่อจนกว่า lead จะถามคุณว่าต้องแก้อะไร

**การ push และ merge** ทีมไม่ทำเอง ถ้าต้องการให้ทำ ให้สั่งเป็นการตัดสินใจ D7 ส่วน force-push และ `gh pr merge` ถูกปิดไว้ทั้งหมด

---

## 7. หยุดงานและกลับมาทำต่อ

Agent Teams **resume teammate ไม่ได้** ถ้าปิด session ทีมจะหายทั้งหมด จึงต้องบันทึก checkpoint ทุกครั้งที่หยุด

**หยุดงาน**
```text
หยุดก่อน พรุ่งนี้ทำต่อ
```
1. lead สั่งทุกคนหยุดที่จุดที่ปลอดภัย โดยไม่ commit หรือ push
2. git stage งานที่เสร็จแล้ว
3. lead เขียน `checkpoint-note.md` แล้วรัน `checkpoint.py save`
4. lead ปิด teammate และบอกคุณว่างานอยู่ตรงไหน

**กลับมาทำต่อ** (เปิด session ใหม่ในโปรเจกต์เดิม)
```text
ทำต่อจากเมื่อวาน
```
1. lead รัน `checkpoint.py read`
2. lead แจ้งว่ามีอะไรเปลี่ยนไปตั้งแต่ตอนหยุด เช่น ไฟล์ที่ถูกแก้ หรือ tree ที่เปลี่ยน
3. lead ตรวจข้ออ้างที่งานต่อจากนี้ต้องพึ่งพาซ้ำ แล้วตั้งทีมใหม่

**ถ้าลืม checkpoint** ไฟล์ของงานใน `.agents/work/<task-id>/` ยังอยู่ครบ ให้บอก lead ว่า "อ่าน .agents/work/<task-id>/ แล้วทำต่อ" แต่จะไม่มีรายการสิ่งที่เปลี่ยนไปตั้งแต่ตอนหยุดให้

---

## 8. ทบทวนงานและปรับทีม

หลังจบงานที่มีบทเรียน เช่น pilot ของ migration หรือบั๊กที่แก้หลายรอบ ให้สั่ง:
```text
ทำ retro ของงาน <task-id> ตาม workflow retro
```

1. lead อ่านบันทึกของงานจาก 3 มุม แล้วเขียน `retro.md`
2. คุณได้รายการข้อเสนอให้อนุมัติทีละแถว (D11) แต่ละแถวบอกปัญหา, สิ่งที่จะแก้, ไฟล์ที่จะแก้ และหลักฐาน
3. lead แก้เฉพาะแถวที่อนุมัติ, รัน `sync_claude.py` และ `check_team.py` แล้วขอ commit จากคุณ

ถ้าอยากให้ตรวจละเอียดกว่านี้ สั่ง "retro แบบ full" ทีมจะใช้ agent เพิ่ม 4 ตัว และจะถามคุณก่อนเพราะมีค่าใช้จ่าย (D10)

---

## 9. เมื่อ teammate ติดวน

ทีมมีกลไกกันการวนไม่รู้จบ 3 ชั้น (รายละเอียดอยู่ใน `.agents/protocols/loops.md`)

1. **งบ 3 รอบต่องาน:** แก้ → stage → ทดสอบ → รีวิว ได้ไม่เกิน 3 รอบ ถ้าจะทำรอบที่ 4 ต้องให้คุณอนุมัติ (D9) และถ้าล้มแบบเดิม 2 ครั้ง ทีมต้องหยุดแล้วถามคุณทันที
2. **hook ตรวจจับการวน:** ถ้า teammate รันคำสั่งเดิมซ้ำ 6 ครั้งใน 10 นาทีโดยไม่มีไฟล์เปลี่ยน คำสั่งนั้นจะถูกปฏิเสธ และ teammate ต้องรายงาน `BLOCKED`
3. **lead คอยเฝ้า:** lead รัน `team_health.py` ทุกครั้งที่ teammate รายงาน และเปลี่ยน teammate ที่ติดวนเป็นตัวใหม่

**คำขอ D9 ที่คุณจะได้** มีตัวเลือก เช่น เปลี่ยนแนวทาง, ลด scope, หาสิ่งที่ขาด หรือหยุดงาน พร้อมหลักฐานว่าลองอะไรไปแล้วและล้มเพราะอะไร ไม่มีค่าเริ่มต้น งานจะรอจนกว่าคุณตอบ

**ถ้าคุณเห็นเองว่า teammate วนอยู่**

| ขั้น | ทำอะไร |
|---|---|
| 1 | เลือก teammate ใน agent panel (ลูกศรขึ้นลง แล้ว Enter) เพื่อดูว่ามันทำอะไรอยู่ |
| 2 | กด **Escape** เพื่อขัดจังหวะ turn ปัจจุบัน แล้วพิมพ์ "หยุด รายงานสถานะและสิ่งที่ลองไปแล้วให้ lead" |
| 3 | ถ้ายังวนอยู่ เลือก teammate นั้นแล้วกด **`x`** เพื่อหยุด |
| 4 | บอก lead ว่า "teammate <ชื่อ> ติดวน ให้ spawn ตัวใหม่พร้อม brief ที่รวมทุกอย่างแล้ว" |
| 5 | ดูภาพรวมด้วย `python3 .agents/scripts/team_health.py` |

**อย่าเพิ่มเพดานเพื่อให้ทีมทำต่อ** ถ้างานติดเพดานบ่อย ให้ทำ retro (หัวข้อ 8) เพื่อหาสาเหตุ เพดานปรับได้ด้วย env `LOOP_GUARD_MAX` และ `LOOP_GUARD_WINDOW` แต่ถือเป็นการเปลี่ยนกฎของทีม (D11)

## 10. แก้ไขและอัปเดตชุด

### 10.1 แก้กฎ, บทบาท หรือ skill ด้วยตัวเอง
**แก้ที่ `.agents/` เสมอ** อย่าแก้ที่ `.claude/agents/` หรือ `.claude/skills/` โดยตรง
```bash
# หลังแก้ไฟล์ใน .agents/agents/ หรือ .agents/skills/
python3 .agents/scripts/sync_claude.py
python3 .agents/scripts/check_team.py --installed
```
ถ้าแก้ประโยคที่ถูกตรึงไว้ใน `.agents/rules.json` `check_team.py` จะแจ้ง ให้ตัดสินใจว่าจะคืนประโยคนั้น หรือแก้ `rules.json` ให้ตรงกับกฎใหม่

### 10.2 อัปเดตชุดจากโฟลเดอร์ `agent-team-roles/`
ถ้ามีชุดเวอร์ชันใหม่ใน `agent-team-roles/`
```bash
cd /path/to/agent-team-roles
python3 install.py /path/to/<project> --force
```
`--force` จะทับไฟล์ใน `.agents/` ของโปรเจกต์ ถ้าคุณเคยแก้ไฟล์ในโปรเจกต์ไว้ ให้นำการแก้นั้นกลับเข้าไปใน `agent-team-roles/.agents/` ก่อน ส่วน `settings.json` จะไม่ถูกทับ

### 10.3 เปลี่ยนโมเดล (ลดค่าใช้จ่าย)
แก้บรรทัด `model:` ในไฟล์ `.agents/agents/<role>.md` แล้วรัน `sync_claude.py`

| บทบาท | ค่าเริ่มต้น | ถ้าต้องการประหยัด |
|---|---|---|
| analyst | `opus` | `sonnet` (หา root cause ได้แย่ลง) |
| backend, frontend | `sonnet` | คงไว้ |
| qa | `opus` | `sonnet` (ผู้ตรวจจะใช้โมเดลเดียวกับผู้เขียน) |
| reviewer | `opus` | คงไว้ ถ้ารีวิวเป็นเรื่องสำคัญของคุณ |
| git | `sonnet` | `haiku` ได้ เพราะงานไม่ซับซ้อน |

### 10.4 อัปเดต skill ที่คัดลอกจาก pstack
ทำในโฟลเดอร์ `agent-team-roles/` แล้วติดตั้งใหม่
```bash
python3 .agents/scripts/vendor_pstack_skills.py --pstack /path/to/pstack-claude --check
python3 .agents/scripts/vendor_pstack_skills.py --pstack /path/to/pstack-claude
python3 install.py /path/to/<project> --force
```
ถ้า script แจ้ง `upstream drift` แปลว่า pstack เปลี่ยนข้อความตรงจุดที่ชุดนี้ปรับไว้ ต้องแก้ script ก่อน

---

## 11. แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุ | วิธีแก้ |
|---|---|---|
| ไม่มี teammate เกิดขึ้น | Agent Teams ยังไม่เปิด หรือ lead เลือกใช้ subagent แทน | ตรวจ `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` แล้วสั่งชัด ๆ ว่า "สร้าง agent team" พร้อมชื่อ teammate |
| teammate ไม่ใช้นิยามบทบาทของชุด | ไม่ได้ระบุ agent type หรือไฟล์ใน `.claude/agents/` ไม่ตรงกับ `.agents/agents/` | สั่ง "ใช้ agent type qa" และรัน `sync_claude.py --check` |
| commit ถูกปฏิเสธ: `has no test-report.md` | qa ยังไม่ได้ทดสอบ | ให้ทีมทำขั้น verify ให้เสร็จก่อน |
| commit ถูกปฏิเสธ: `test-report.md still has placeholders` | qa ยังกรอกรายงานไม่ครบ | ให้ qa กรอกให้ครบ |
| commit ถูกปฏิเสธ: `unfinished reviewer or lead triage sections` | lead ยังไม่ได้คัดกรองผลรีวิว | บอก lead ให้คัดกรองผลรีวิวตาม team-review |
| งาน verify หรือ review ปิดไม่ได้ | รายงานยังไม่ครบ, verdict ผิดรูปแบบ หรือไม่มี tree id | ข้อความจาก hook บอกว่าขาดอะไร |
| prompt commit ขึ้น `WARNING ... differs` | มีการแก้หลังการตรวจ | ปฏิเสธ แล้วให้ git stage ใหม่ จากนั้นให้ qa และ reviewer ตรวจที่ tree id ใหม่ |
| ถูกถามบ่อยเกินไป | เรื่องที่ตอบซ้ำ ๆ ยังไม่เป็น standing decision | เพิ่มใน `standing-decisions.md` (หัวข้อ 3.3) หรือทำ retro |
| qa รายงาน `BLOCKED` บ่อย | ไม่มีวิธีเปิดระบบที่ชัดเจน | ทำหัวข้อ 3.1 และ 3.2 |
| lead ลงมือเขียนโค้ดเอง | lead ไม่รอ teammate | พิมพ์ "รอ teammate ทำงานให้เสร็จก่อน" |
| teammate หยุดกลางทางหลังเจอ error | ข้อจำกัดของ Agent Teams | เลือก teammate ใน panel แล้วสั่งต่อ หรือขอ lead spawn ตัวใหม่ |
| teammate รันคำสั่งเดิมซ้ำ ๆ หรือแก้แล้วล้มแบบเดิม | ติดวน | หัวข้อ 9 |
| คำสั่งถูกปฏิเสธ: `Loop guard: you have run this exact command ...` | รันคำสั่งเดิมซ้ำ 6 ครั้งโดยไม่มีไฟล์เปลี่ยน | ให้ teammate รายงาน `BLOCKED` แล้ว lead ตัดสินว่าจะเปลี่ยนวิธีหรือเปลี่ยนตัว ถ้ากำลังรอ service ให้ใช้คำสั่งรอเดียวที่มี time limit |
| งาน verify ปิดไม่ได้: `round 4 is past the budget of 3` | แก้เกิน 3 รอบ | ตอบคำขอ D9 ถ้าอนุมัติรอบเพิ่ม รายงานต้องอ้าง D9 ในช่อง Round approval |
| หลัง `/resume` แล้ว lead พยายามคุยกับ teammate ที่ไม่มีแล้ว | resume teammate ไม่ได้ | สั่ง "อ่าน checkpoint แล้วตั้งทีมใหม่" (หัวข้อ 7) |
| `check_team.py` แจ้ง `no longer says` | ประโยคที่ถูกตรึงไว้ถูกแก้ | คืนประโยคนั้น หรือแก้ `rules.json` ถ้าตั้งใจเปลี่ยนกฎ |
| tmux session ค้างหลังปิด Claude | ทีมปิดไม่สมบูรณ์ | `tmux ls` แล้ว `tmux kill-session -t <name>` |
| ค่าใช้จ่ายสูง | ทีมใหญ่, ใช้ `opus` หลายบทบาท หรือ teammate ค้างไว้นาน | ลดจำนวน teammate, เปลี่ยนโมเดล (10.3) และสั่งปิด teammate ที่เสร็จงานแล้ว |

---

## 12. คำสั่งอ้างอิง

ส่วนใหญ่ lead หรือ teammate เป็นคนรัน คุณรันเองได้เพื่อตรวจสอบ ทุกคำสั่งรันจาก root ของโปรเจกต์

| คำสั่ง | ใช้ทำอะไร |
|---|---|
| `python3 .agents/scripts/new_task.py <bug\|feature\|migration\|program\|retire> "<title>"` | สร้างโฟลเดอร์งานพร้อม template |
| `python3 .agents/scripts/checkpoint.py save <task-id>` | บันทึก checkpoint ตอนหยุดงาน |
| `python3 .agents/scripts/checkpoint.py read [<task-id>]` | อ่าน checkpoint ล่าสุดพร้อมรายการสิ่งที่เปลี่ยนไป |
| `python3 .agents/scripts/migration_status.py <program-task-id>` | สร้าง `STATUS.md` ของโปรแกรม migration |
| `python3 .agents/scripts/parity.py record --base-url <php> --cases <cases.jsonl> --out <baseline.jsonl>` | บันทึก baseline จาก PHP |
| `python3 .agents/scripts/parity.py check --base-url <go> --baseline <baseline.jsonl> [--config <parity.json>]` | เทียบ Go กับ baseline (exit 0 คือผ่าน, 3 คือสรุปไม่ได้) |
| `python3 .agents/scripts/log_row.py <task-id> <phase> <decision> <why> <evidence> <result>` | เพิ่มแถวใน `log.tsv` |
| `python3 .agents/scripts/check_team.py --installed` | ตรวจว่าชุดครบ, ลิงก์ถูก, กฎที่ตรึงไว้ยังอยู่ และสำเนาใน `.claude/` ตรงกัน |
| `python3 .agents/scripts/sync_claude.py [--check]` | ซิงก์ teammate และ skill จาก `.agents/` ไป `.claude/` |
| `python3 .agents/scripts/team_health.py` | แสดง teammate ที่อาจติดวน, งานที่ถึงรอบ 3 และ log ที่ซ้ำ |

**ไฟล์ที่คุณจะเปิดดูบ่อย**

| ไฟล์ | เนื้อหา |
|---|---|
| `.agents/work/<task-id>/test-report.md` | รายงานผลทดสอบ |
| `.agents/work/<task-id>/review-report.md` | รายงานรีวิวและการคัดกรองของ lead |
| `.agents/work/<task-id>/decisions.md` | การตัดสินใจของคุณพร้อมคำพูดต้นฉบับ |
| `.agents/work/<task-id>/log.tsv` | บันทึกทุกจุดตัดสินใจของทีม |
| `.agents/work/<program-id>/STATUS.md` | สถานะโปรแกรม migration |
| `.agents/standing-decisions.md` | คำตัดสินที่ใช้ซ้ำได้ |

ไฟล์ใน `.agents/work/` ไม่ถูก commit โดยค่าเริ่มต้น ถ้าต้องการเก็บไว้ใน git ให้ลบ `.agents/work/.gitignore`
