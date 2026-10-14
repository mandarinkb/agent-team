# ทีม Agent สำหรับหาบั๊ก เพิ่มฟีเจอร์ และย้ายระบบ (ใช้แนวคิดจาก pstack)

> **ต้องการแค่วิธีติดตั้งและใช้งาน:** อ่าน [INSTALL-AND-USAGE-TH.md](INSTALL-AND-USAGE-TH.md) ไฟล์นี้ (README) อธิบายการออกแบบและเหตุผลของแต่ละส่วน

ชุดนี้คือทีม teammate ของ Claude Code [Agent Teams](https://code.claude.com/docs/en/agent-teams) ที่นำหลักการออกแบบที่ดีของ pstack มาใช้ ทุกอย่างอยู่ในโฟลเดอร์ `.agents/` และเชื่อมเข้ากับโปรเจกต์ผ่าน `CLAUDE.md`

> **สถานะการทดสอบ:**
> - script และ hook ผ่าน test 68 ข้อ (`tests/`) ผมลองใส่บั๊กลงไปแล้ว test จับได้ทุกครั้ง และ test เจอบั๊กจริง 2 จุดใน `install.py` กับ `check_team.py` ซึ่งแก้แล้ว
> - `check_team.py` ตรวจว่าไฟล์ครบ ลิงก์ถูก และกฎสำคัญยังอยู่
> - **ยังไม่ได้ทดสอบกับ Agent Teams จริง** และยังไม่ได้ลองกับโปรเจกต์จริง ควรเริ่มจากงานเล็กก่อน ดูหัวข้อ 11
>
> **ไฟล์เดิม:** `agents/*.md` กับ `AGENTS.md` ของชุดก่อนถูกย้ายและปรับเข้าไปใน `.agents/` แล้ว

---

## 1. ภาพรวม

```
                         ┌─────────────────────────────┐
                         │   คุณ (User)                 │
                         │   ตัดสินใจ · อ่านผลทดสอบ · อนุมัติ commit │
                         └──────────────▲──────────────┘
                     คำขอตัดสินใจ + ตัวเลือก │ คำตอบของคุณ (บันทึกคำพูดต้นฉบับ)
                         ┌──────────────┴──────────────┐
                         │   Lead (session หลัก)        │
                         │   แบ่งงาน · เขียน brief · ส่งเรื่องให้คุณ │
                         └──┬─────┬──────┬──────┬────┬─┘
                            │     │      │      │    │   shared task list
        ┌───────────────────┘     │      │      │    └──────────────┐
   ┌────▼────┐   ┌────────▼───┐ ┌──▼───┐ ┌▼───────┐            ┌────▼───┐
   │ analyst │◄─►│ backend /  │◄►│  qa  │◄►│reviewer│            │  git   │
   │ สืบสวน  │   │ frontend   │ │ทดสอบ │ │ รีวิว  │            │ commit │
   │ หา root │   │ เขียนโค้ด  │ │รายงาน│ │(เสริม) │            │หลังอนุมัติ│
   └─────────┘   └────────────┘ └──────┘ └────────┘            └────────┘
          teammate คุยกันเองได้ตรง ๆ แต่ตัดสินใจแทนคุณไม่ได้
```

**หน้าที่ของคุณมี 3 อย่าง**
1. **ตัดสินใจ** เมื่อ teammate เสนอตัวเลือกมา
2. **อ่านรายงานผลการทดสอบ** ที่ qa เขียนเป็นไฟล์ `.md`
3. **อนุมัติ commit** ที่ prompt ซึ่งเด้งขึ้นมา

การเขียนโค้ด การทดสอบ และการจัดการ git เป็นงานของ teammate ทั้งหมด

---

## 2. โครงสร้างไฟล์

```
agent-team-roles/
├── README-TH.md              คู่มือนี้
├── CLAUDE.md.example         ตัวอย่าง CLAUDE.md ที่ import @.agents/AGENTS.md
├── install.py                ติดตั้งลงโปรเจกต์
├── tests/                    test ของ script และ hook (68 ข้อ)
└── .agents/
    ├── AGENTS.md             กฎกลางของทีม (โหลดเข้า context ทุกตัว จึงเขียนให้สั้น)
    ├── agents/               นิยาม teammate 6 บทบาท → ติดตั้งไปที่ .claude/agents/
    ├── skills/               team-* 10 ตัว + skill ที่คัดลอกจาก pstack 8 ตัว → ติดตั้งไปที่ .claude/skills/
    │                         (THIRD_PARTY_NOTICES.md และ licenses/ ระบุที่มาและ license)
    ├── workflows/            bug-fix.md · feature.md · migration.md · migration-program.md · migration-retire.md · retro.md
    ├── protocols/            decisions.md · messaging.md · commit-approval.md · loops.md
    ├── templates/            brief · decision-request · decisions · test-report · review-report · migration-plan · inventory · checkpoint-note · retro
    ├── scripts/              new_task · log_row · parity · check_team · hooks/
    ├── settings.example.json permission + hook + env สำหรับ .claude/settings.json
    ├── rules.json            กฎสำคัญที่ตรึงไว้ ถ้าประโยคหาย check_team จะ fail
    ├── standing-decisions.md คำตัดสินของคุณที่ใช้ซ้ำได้ (หัวข้อ 5.5)
    └── work/                 ไฟล์ของแต่ละงาน (ไม่ commit โดยค่าเริ่มต้น)
```

**ทำไมต้องคัดลอกไปที่ `.claude/`:** Claude Code อ่านนิยาม agent จาก `.claude/agents/` และ skill จาก `.claude/skills/` เท่านั้น `install.py` จึงคัดลอกจาก `.agents/` ไปให้ และ `check_team.py --installed` ตรวจว่าสองที่ยังตรงกัน ให้แก้ที่ `.agents/` เสมอ แล้วรัน `install.py --force` ใหม่

---

## 3. ติดตั้ง

```bash
python3 agent-team-roles/install.py /path/to/your-project
```

`install.py` ทำสิ่งต่อไปนี้
1. คัดลอก `.agents/` ไปไว้ที่โปรเจกต์
2. คัดลอก teammate ไปที่ `.claude/agents/` และ skill ไปที่ `.claude/skills/`
3. **CLAUDE.md:** ถ้ายังไม่มี จะสร้างจาก `CLAUDE.md.example` ถ้ามีอยู่แล้ว จะเพิ่มบรรทัด `@.agents/AGENTS.md` ต่อท้าย
4. **`.claude/settings.json`:** ถ้ายังไม่มี จะสร้างจาก `settings.example.json` ถ้ามีอยู่แล้ว **จะไม่แก้ไฟล์** แต่บอกให้คุณรวมส่วน `permissions`, `hooks` และ `env` เอง
5. ไฟล์ที่มีอยู่แล้วแต่เนื้อหาต่าง จะถูกข้ามและแจ้งไว้ ถ้าต้องการทับให้ใช้ `--force` (ไม่ทับ settings.json ในทุกกรณี)
6. รัน `check_team.py --installed` ตรวจผลให้

**ถ้า `CLAUDE.md` อยู่ใน `.claude/CLAUDE.md`** ให้ใช้บรรทัด `@../.agents/AGENTS.md` แทน เพราะ import อ้างอิงจากตำแหน่งของไฟล์ที่ import

**ใส่ข้อมูลโปรเจกต์ใน CLAUDE.md:** คำสั่ง build, test และ run, โครงโฟลเดอร์ และ URL ของ PHP กับ Go ตอนรัน local teammate ทุกตัวอ่านไฟล์นี้

**สิ่งที่ต้องมีในเครื่อง:** Python 3.9 ขึ้นไป, git และ Claude Code ที่รองรับ Agent Teams ถ้าต้องการ split pane ต้องมี tmux หรือ iTerm2 ด้วย

**ถ้าติดตั้ง pstack ไว้ด้วย:** ให้ปิด hook ของ pstack (`session hook: off` ใน `pstack-models.md`) ไม่อย่างนั้น teammate อาจเรียก `poteto-mode` ซ้อนเข้าไปอีกชั้น ทำให้ใช้ token เพิ่มเป็นสองเท่าและขั้นตอนชนกัน

**การเปิด Agent Teams:** `settings.example.json` ตั้ง `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` ไว้ระดับโปรเจกต์ ผลข้างเคียงคือในโปรเจกต์นี้ subagent ที่ Claude ตั้งชื่อเองจะกลายเป็น teammate ด้วย ถ้าไม่ต้องการ ให้ลบ `env` ออกจาก settings แล้วเปิดเฉพาะตอนใช้ทีมด้วย `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 claude`

---

## 4. บทบาทและโมเดล

| Teammate | โมเดล | เครื่องมือ | หน้าที่ |
|---|---|---|---|
| `analyst` | `opus` | Read, Grep, Glob, Write, Bash | สืบสวนโค้ด, หา root cause ด้วยหลักฐาน, หา blast radius, เตรียมตัวเลือกให้คุณตัดสิน **ไม่แก้ source** |
| `backend` | `sonnet` | Read, Grep, Glob, Edit, Write, Bash | เขียนโค้ดฝั่ง server และ port PHP เป็น Go ตามแผนที่คุณอนุมัติ |
| `frontend` | `sonnet` | เหมือน backend | เขียนโค้ดฝั่ง client (ตัดออกได้ถ้างานเป็น API อย่างเดียว) |
| `qa` | `opus` | Read, Grep, Glob, Edit, Write, Bash | reproduce บั๊ก, บันทึก baseline, เขียน test, ตรวจบนของจริง, **เขียนรายงานผลการทดสอบ** |
| `reviewer` | `opus` | Read, Grep, Glob, Write, Bash (ตัด Edit) | รีวิวสิ่งที่ stage ไว้ 8 มุม และ **เขียนรายงานรีวิว** บังคับใช้ใน feature, migration และ retire ส่วน bug-fix บังคับเมื่อแก้หลายไฟล์หรือแตะส่วนเสี่ยง (ดูหัวข้อ 8.2) |
| `git` | `sonnet` | Read, Grep, Glob, Bash (ตัด Edit, Write) | สร้าง branch และ worktree, stage แล้วส่ง **tree id** ให้ qa และ reviewer, และ commit หลังคุณอนุมัติ |

**ทำไมเลือกโมเดลแบบนี้**
- **ผู้ตรวจใช้โมเดลต่างจากผู้เขียน:** `qa` และ `reviewer` ใช้ `opus` ส่วน `backend` ใช้ `sonnet` ตามหลักของ pstack ที่ว่าผู้ตรวจควรมองต่างมุมจากผู้ทำ
- **analyst ใช้โมเดลแรง:** การหา root cause ต้องใช้วิจารณญาณสูง ตรงกับที่ pstack ใช้โมเดลแรงที่สุดกับงาน bug-fix
- **ถ้าต้องการประหยัด:** เปลี่ยน `model:` ทุกไฟล์ใน `.agents/agents/` เป็น `sonnet` แล้วรัน `install.py --force` แต่จะเสียความเป็นอิสระของการตรวจไปบางส่วน
- **จำนวน teammate:** เอกสารแนะนำ 3-5 คน งานส่วนใหญ่ใช้ analyst, backend, qa และ git ส่วน reviewer กับ frontend ใช้เมื่อจำเป็น

### 4.1 teammate เลือก skill เอง

**กลไกของ Claude Code:** model เห็นชื่อ, `description` และ `when_to_use` ของทุก skill ที่ติดตั้งไว้ตลอดเวลา แล้วเลือกเรียกเองเมื่อเห็นว่าเข้ากับงาน เนื้อหาเต็มของ skill จะโหลดเฉพาะตอนที่ถูกเรียก teammate โหลด skill ของโปรเจกต์ (`.claude/skills/`) และของผู้ใช้ด้วย

**ชุดนี้ตั้งกรอบไว้ 3 ระดับ** (`.agents/AGENTS.md` หัวข้อ Choosing skills)

| ระดับ | Skill | เหตุผล |
|---|---|---|
| **บังคับใช้** | `team-decision`, `team-verify`, `team-parity` และ `team-review` | เป็นตัวที่ถือกฎที่คุณพึ่งพา คือการตัดสินใจผ่านคุณ, รายงานผลทดสอบ, การเทียบ PHP กับ Go และรายงานรีวิว |
| **เลือกเองได้** | `team-*` ตัวอื่น, skill ที่คัดลอกจาก pstack มาไว้ในชุด 8 ตัว (ดู 4.2) และ skill ของโปรเจกต์ | ให้ teammate ใช้วิจารณญาณเองว่าอะไรเหมาะกับงาน |
| **ต้องถาม lead ก่อน** | skill ที่สร้าง agent เพิ่ม (`arena`, `swarm`, `interrogate`, `how`, `why`), skill ที่รัน workflow ทั้งชุด (`poteto-mode`, `figure-it-out`) และ skill ที่ push, เปิด PR หรือ merge | ทำให้ค่าใช้จ่ายเพิ่มหลายเท่า หรือข้ามไปทำงานของบทบาทอื่น |

**องค์ประกอบที่ช่วยให้เลือกได้แม่น**
- **ไฟล์ของแต่ละบทบาทมีตาราง "Choosing skills"** บอกว่าบทบาทนั้นมักใช้ skill ไหนในสถานการณ์ไหน เป็นคำแนะนำ ไม่ใช่ข้อบังคับ
- **skill ทุกตัวมี `when_to_use`** บอกว่าเหมาะกับบทบาทไหน และมีวลีที่มักใช้เรียก
- **workflow บอกชื่อ skill เป็นตัวเลือกปกติ** และเขียนไว้ชัดว่าเลือกตัวอื่นได้ ยกเว้น 3 ตัวที่บังคับ
- **teammate ต้องบอกใน report และ `log.tsv` ว่าใช้ skill ไหน** เพื่อให้คุณดูย้อนหลังได้ว่า skill ไหนช่วยจริง แล้วปรับตารางแนะนำให้ดีขึ้น
- **`check_team.py` ตรวจว่ากรอบนี้ยังครบ** ทุกบทบาทต้องมีส่วน Choosing skills ทุก skill ต้องมี `when_to_use` และกฎ skill บังคับถูกตรึงไว้ใน `rules.json`

**ข้อจำกัด**
- การเลือก skill เป็นวิจารณญาณของ model ไม่มีอะไรรับประกันว่าจะเลือกถูกทุกครั้ง ถ้าเห็นว่า teammate ไม่เรียก skill ที่ควรใช้ ให้ปรับ `description` หรือ `when_to_use` ของ skill นั้น หรือเพิ่มแถวในตาราง Choosing skills ของบทบาทนั้น
- skill บังคับก็ยังบังคับด้วยคำสั่งเป็นหลัก มีแค่ผลลัพธ์ของ `team-verify` (รายงานผลทดสอบ) ที่ hook ตรวจจริง
- ชุดนี้ **ไม่ต้องติดตั้ง pstack** เพราะ skill ของ pstack ที่ทีมใช้ถูกคัดลอกมาไว้ในชุดแล้ว (ดู 4.2)
- **skill ทุกตัวที่ติดตั้งเพิ่ม context ของทุก teammate ในทุก turn** (ตามเอกสาร) ใช้ `/skill-doctor` ดูได้ว่าแต่ละ skill มีต้นทุนเท่าไรและถูกใช้บ่อยแค่ไหน skill ที่ไม่ได้ใช้ควรปิดด้วย `disable-model-invocation: true`

### 4.2 skill ที่คัดลอกมาจาก pstack

ชุดนี้คัดลอก skill ของ pstack ที่ทีมใช้จริงมาไว้ใน `.agents/skills/` จึงใช้ได้โดยไม่ต้องติดตั้ง pstack ตัว `install.py` คัดลอกไปที่ `.claude/skills/` ให้ รวมถึงโฟลเดอร์ `references/`

| Skill | ใครมักใช้ | ทำอะไร | ปรับอะไรสำหรับทีม |
|---|---|---|---|
| `tdd` | qa, backend, frontend | เขียน test ที่ fail ก่อน แล้วค่อยแก้ ใช้เมื่อ test เขียนง่ายและถูก | เพิ่ม `when_to_use` |
| `deslop` | backend, frontend, reviewer | ล้าง comment เกินจำเป็น, defensive check, cast `any` และ nesting ลึกออกจาก diff | เพิ่ม `when_to_use` |
| `blast-radius` | analyst, backend, reviewer | หาว่าการแก้จะทำให้อะไรนอก diff พัง และพิสูจน์ "ข้อเท็จจริงเดียวที่ทำให้ปลอดภัย" ด้วยการรันจริง | ให้อ้างถึง `team-investigate` แทน `how`/`why` และให้ถาม lead แทนการใช้ `arena` |
| `benchmark-checklist` | qa, analyst | ตรวจตัวเลข performance 7 ข้อก่อนรายงาน เช่น เทียบ PHP กับ Go | แนบ principle Explain the Number ไว้ใน `references/` และเปลี่ยนส่วนที่อ้างถึง playbook ของ pstack |
| `typescript-best-practices` | frontend, reviewer | กฎ TypeScript (โหลดอัตโนมัติเมื่อแตะไฟล์ `.ts` หรือ `.tsx`) | แนบ principle Type System Discipline และ Boundary Discipline ไว้ใน `references/` |
| `create-verification-skill` | qa (หลังคุณอนุมัติ D4) | สร้าง skill `verify` เฉพาะโปรเจกต์ (launch, doctor, drive, evidence, cleanup และ feature map) และพิสูจน์ว่าใช้ได้จริงก่อนส่งมอบ | ต้องให้คุณอนุมัติก่อนสร้าง และไฟล์ที่ได้ผ่าน stage, รีวิว และอนุมัติ commit เหมือนงานอื่น |
| `maintain-verification-skill` | qa (lead อนุญาตก่อน) | ตรวจว่า skill `verify` และ feature map ยังตรงกับระบบ ทั้งจาก source และการขับจริงทุก feature | การรันแบบขนานต้องขอ lead ก่อน และเปลี่ยนจาก PR เป็นขั้นตอนอนุมัติ commit ของทีม |
| `thermo-nuclear-code-quality-review` | reviewer | รีวิวคุณภาพโค้ดแบบเข้มงวด สำหรับการปรับโครงสร้างใหญ่หรือ migration ตัวแรก | ให้เขียนรายงานในโฟลเดอร์ของงาน และให้ถาม lead แทนการใช้ `swarm` |

**ที่ไม่ได้คัดลอกมา และเหตุผล**
- `how`, `why`, `arena`, `swarm`, `interrogate` และ `architect` สร้าง agent เพิ่มอีกหลายตัว ซ้ำกับสิ่งที่ทีมทำอยู่แล้ว และแพง แนวคิดของ skill เหล่านี้อยู่ใน `team-investigate`, `team-root-cause`, `team-design-options` และ `team-review` แล้ว
- `poteto-mode` และ `figure-it-out` เป็นตัวคุม workflow ทั้งชุด ซึ่งจะชนกับ workflow ของทีม
- `babysit`, `fix-ci` และ `make-pr-easy-to-review` push หรือแก้ประวัติ git ซึ่งเป็นการตัดสินใจของคุณ (D7)

**การอัปเดตเมื่อ pstack มีเวอร์ชันใหม่**
```bash
python3 .agents/scripts/vendor_pstack_skills.py --pstack /path/to/pstack-claude --check   # ดูว่ามีอะไรเปลี่ยน
python3 .agents/scripts/vendor_pstack_skills.py --pstack /path/to/pstack-claude           # คัดลอกใหม่
python3 install.py /path/to/your-project --force                                          # ติดตั้งลงโปรเจกต์
```
- **script แก้ข้อความแต่ละจุดโดยระบุข้อความต้นฉบับไว้ตรงตัว** ถ้า pstack เปลี่ยนข้อความตรงนั้น script จะ fail และบอกว่าจุดไหน เพื่อไม่ให้ได้ skill ที่ปรับไม่ครบ
- **ห้ามแก้ไฟล์ skill ที่คัดลอกมาด้วยมือ** ให้แก้ใน script แทน ถ้าแก้ไฟล์โดยตรง `--check` จะรายงานว่าไฟล์ไม่ตรง

**License:** skill ทั้ง 6 ตัวเป็น MIT (ของ Lauren Tan, Michael Denyer และ Cursor) ที่มาและการเปลี่ยนแปลงบันทึกไว้ใน `.agents/skills/THIRD_PARTY_NOTICES.md` และตัวเต็มของ license อยู่ใน `.agents/skills/licenses/` ถ้าแจกจ่ายชุดนี้ต่อ ให้นำสองส่วนนี้ไปด้วย

---

## 5. บทบาทของคุณ: การตัดสินใจและการอนุมัติ

### 5.1 จุดที่ต้องให้คุณตัดสินใจ (Gate)
ทุก workflow มีจุดตัดสินใจประจำ 2 จุด

| Gate | เกิดเมื่อ | คุณจะเห็น | สิ่งที่รอคำตอบ |
|---|---|---|---|
| **G1 อนุมัติแผน** | ก่อนเริ่มเขียนโค้ด | root cause และหลักฐาน หรือ design หลายแบบ หรือแผน port พร้อมตัวเลือกและคำแนะนำ | ขั้นเขียนโค้ดทั้งหมด |
| **G2 อนุมัติ commit** | หลัง qa ทดสอบ, reviewer รีวิว และ lead คัดกรองผลเสร็จ | รายงานผลทดสอบและรายงานรีวิวที่ tree id เดียวกัน, การคัดกรองของ lead, รายการไฟล์ที่ stage และข้อความ commit | `git commit` |

นอกจากนี้ teammate จะส่งคำขอให้ตัดสินใจระหว่างทางเมื่อเจอเรื่องในรหัส D1 ถึง D11 (ดู `.agents/protocols/decisions.md`) เช่น ต้องเปลี่ยน API contract, ยอมรับ DIFF ใน migration, เพิ่ม dependency หรือจะรีวิวงานเสี่ยงสูงด้วยอีกโมเดลไหม (D10)

### 5.2 อะไรที่ไม่ส่งมาให้คุณ
เพื่อไม่ให้คุณต้องตอบทุกเรื่องเล็กน้อย เรื่องต่อไปนี้ teammate ตัดสินเองภายในแผนที่อนุมัติแล้ว และบันทึกไว้ใน `log.tsv`
- ชื่อตัวแปรหรือฟังก์ชันภายใน และโครงสร้างภายในของ design ที่อนุมัติแล้ว
- ลำดับการเขียน test และวิธีรันคำสั่ง
- การแก้บั๊กที่ qa เจอในงานของตัวเอง โดยไม่ออกนอก design

**ข้อเท็จจริงไม่ใช่การตัดสินใจ:** ถ้าคำถามตอบได้ด้วยการรันอะไรสักอย่าง (เช่น "PHP คืนค่า null หรือ []") teammate ต้องรันเอง ไม่ส่งมาถามคุณ (หลัก never-block-on-the-human ของ pstack)

**ถ้า teammate ไม่แน่ใจว่าเป็นการตัดสินใจหรือไม่ ให้ถือว่าเป็น**

### 5.3 คำขอให้ตัดสินใจหน้าตาเป็นอย่างไร
teammate เขียนจาก `.agents/templates/decision-request.md` ซึ่งต้องมี
- คำถาม, หลักฐานที่ติดป้าย measured / inferred / guess
- **ตัวเลือกอย่างน้อย 2 ตัว** แต่ละตัวมีข้อดี, ข้อเสียและความเสี่ยง, ต้นทุน และวิธีตรวจ
- คำแนะนำพร้อมเหตุผล และความเห็นของ teammate อื่น

lead จะนำเสนอเป็นตัวเลือกให้คุณกดเลือก โดยตัวที่แนะนำอยู่บนสุดและมีป้าย `(แนะนำ)` จากนั้น lead บันทึก **คำพูดต้นฉบับของคุณ** ลง `decisions.md` และส่งต่อให้ teammate ตรงตามคำพูดนั้น
- **lead ห้ามเลือกแทนคุณ** แม้ teammate ทุกคนจะเห็นตรงกัน
- **ไม่มีค่าเริ่มต้นและไม่มี timeout** ถ้าคุณยังไม่ตอบ งานที่รอคำตอบจะหยุด แต่งานอื่นที่ไม่เกี่ยวข้องยังเดินต่อ

### 5.4 การอนุมัติ commit

**ปัญหาที่ต้องแก้:** backend ห้าม commit และคุณต้องอนุมัติทุก commit จึงไม่มี commit SHA ให้ qa ทดสอบ ชุดนี้จึงใช้ **tree id** จาก `git write-tree` แทน ค่านี้ระบุเนื้อหาที่ stage ไว้ได้แน่นอน ถ้าไฟล์ที่ stage เปลี่ยนแม้แต่ตัวเดียว tree id ก็จะเปลี่ยน

1. backend หรือ frontend ทำเสร็จ แล้วแจ้ง git ว่า "ready to stage" (qa ก็แจ้งสำหรับไฟล์ test ของงานนั้น)
2. **git stage** เฉพาะไฟล์ใน scope แล้วส่ง **tree id** ให้ qa, reviewer และ lead
3. **qa ทดสอบ** ที่ tree id นั้น แล้วเขียนรายงานผลทดสอบ
4. **reviewer รีวิว** `git diff --cached` ที่ tree id เดียวกัน แล้วเขียนรายงานรีวิว
5. **lead คัดกรองผลรีวิว** เป็น 4 กลุ่ม ถ้าต้องแก้ จะวนกลับไปข้อ 2 ได้ tree id ใหม่ แล้วทดสอบและรีวิวส่วนที่แก้ใหม่
6. git ร่าง **commit เดียวต่องาน** และใส่บรรทัดสุดท้ายว่า `Task: <task-id>`
7. lead ส่งสรุปให้คุณ ได้แก่ รายงานทั้งสองฉบับ, การคัดกรองของ lead, ไฟล์ที่ stage, ข้อความ commit และ gap ที่ยังเหลือ
8. git รัน `git commit` แล้ว hook ตรวจรายงานก่อน
   - **ปฏิเสธทันที** ถ้ารายงานผลทดสอบยังไม่มีหรือยังไม่เสร็จ หรือรายงานรีวิวยังมีส่วนของ reviewer หรือ lead ที่ไม่เสร็จ
   - **ถ้าผ่าน จะถามคุณ** โดยข้อความใน prompt บอก verdict ของรายงานทั้งสอง และบอกว่า **tree ที่ stage อยู่ตรงกับที่ถูกทดสอบและรีวิวหรือไม่** ถ้าไม่ตรง จะขึ้น `WARNING`
9. คุณกดอนุมัติหรือปฏิเสธที่ prompt ซึ่งเด้งขึ้นที่ session ของ lead

prompt นี้มาจาก ask rule ใน `.claude/settings.json` ซึ่งตามเอกสาร Claude Code **ยังถามคุณทุกโหมด แม้ใน auto mode และ bypassPermissions** hook ไม่เคยอนุมัติแทนคุณ มันมีแค่สองทางคือปฏิเสธ หรือส่งต่อให้คุณพร้อมข้อมูล

**ทำไมเป็น commit เดียวต่องาน:** เพื่อให้ tree ตอน commit ตรงกับ tree ที่ถูกทดสอบและรีวิวพอดี ถ้าคุณต้องการแยกหลาย commit ทำได้ แต่ hook จะขึ้น WARNING ทุก commit ย่อย ส่วนสำหรับ bug-fix หลักฐานว่า test fail ก่อนแก้อยู่ในรายงานผลทดสอบแทนประวัติ git

### 5.5 คำตัดสินที่ใช้ซ้ำได้ (standing decisions)

ไฟล์ `.agents/standing-decisions.md` เก็บคำตัดสินของคุณที่ใช้ได้กับทุกกรณีแบบเดียวกัน ภายในขอบเขตที่คุณกำหนด (ดัดแปลงจาก `preferences.md` ของ Orchestrate และหลัก epistemics ของ pstack)

**ทำงานอย่างไร**
1. ก่อนส่งคำขอให้ตัดสินใจ teammate ต้องอ่านไฟล์นี้ก่อน
2. **ถ้ามีรายการที่ใช้ได้** คือสถานะ `active`, รหัสตรง และอยู่ในขอบเขต teammate ทำตามรายการนั้นได้เลย และอ้างรหัส เช่น `SD-3` ใน `log.tsv` และในรายงาน ไม่ต้องถามคุณซ้ำ
3. **ถ้าไม่แน่ใจ** ให้ส่งคำขอตามปกติ และบอกว่ารายการไหนน่าจะเกี่ยวข้อง ห้ามขยายรายการไปเกินขอบเขต
4. หลังคุณตอบคำถามที่น่าจะเกิดซ้ำ lead จะถามว่า "ให้ใช้คำตอบนี้กับกรณีแบบเดียวกันต่อไปไหม และขอบเขตแค่ไหน"

**ตัวอย่างรายการ**
```markdown
## SD-1: ignore request id ทุก endpoint
- **Codes:** D3
- **Scope:** migration program T-20261009-php-api-to-go
- **Ruling:** "request_id ใน meta ignore ได้ทุก endpoint ไม่ต้องถามอีก"
- **Recorded:** 2026-10-09, lead, จาก decisions.md ของ T-20261009-orders
- **Status:** active
```

**ข้อจำกัดที่ตั้งใจไว้**
- **เรื่องที่ต้องถามทุกครั้งเสมอ:** D7 (การกระทำที่ย้อนกลับไม่ได้), D8 (อนุมัติแผนและอนุมัติ commit), D11 (การเปลี่ยนกฎของทีม) และการปัดตก finding ระดับ critical
- **คำพูดต้นฉบับ:** lead เพิ่มรายการได้เฉพาะเมื่อคุณสั่งชัด ๆ และต้องคัดลอกคำพูดของคุณมาตรงตัว
- **ห้ามแก้หรือลบรายการ:** ถ้าจะยกเลิก ให้เปลี่ยนเป็น `revoked <วันที่>` พร้อมคำพูดของคุณ
- **ตรวจด้วยโค้ด:** `check_team.py` ตรวจรูปแบบ ได้แก่ รหัสห้ามเป็น D7, D8 หรือ D11, ต้องมีคำพูดในเครื่องหมายคำพูด, สถานะต้องถูกต้อง และ id ห้ามซ้ำ

---

## 6. Workflow

### 6.1 หาบั๊ก (`bug-fix.md`)
```
lead: สร้างงาน → qa: reproduce บนของจริง → analyst: หา root cause ด้วยหลักฐาน
(ถ้าสาเหตุไม่ชัด ใช้ analyst 2-3 คนถกและหักล้างสมมติฐานกัน)
→ [G1 คุณอนุมัติ root cause และวิธีแก้] → backend: แก้ให้น้อยที่สุด
→ git: stage + ส่ง tree id → qa: repro ต้อง pass, test ใหม่ต้อง fail บน revision เก่า, เขียนรายงาน
→ reviewer: รีวิว + เขียนรายงาน (ข้ามได้เฉพาะงานแก้ไฟล์เดียวที่ไม่เสี่ยง) → lead: คัดกรองผล
→ git: commit เดียว → [G2 คุณอนุมัติ commit]
```
ตัวอย่างคำสั่ง:
```text
ใช้ workflow .agents/workflows/bug-fix.md
บั๊ก: หน้า /orders แสดงรายการว่างเมื่อผู้ใช้มีคำสั่งซื้อเกิน 100 รายการ
สร้างทีม: analyst 2 คน (ตั้งชื่อ analyst-a และ analyst-b ใช้ agent type analyst), qa, backend, reviewer, git
ให้ analyst ทั้งสองคนตั้งสมมติฐานคนละข้อแล้วพยายามหักล้างกัน
```

### 6.2 เพิ่มฟีเจอร์ (`feature.md`)
```
lead: สร้างงาน → analyst: สำรวจระบบ + blast radius → analyst: ออกแบบอย่างน้อย 2 แบบ
(ถาม backend และ qa เรื่องต้นทุน) → [G1 คุณเลือก design]
→ lead: แบ่งงานให้แต่ละคนแตะไฟล์คนละชุด → qa: เขียน acceptance test ไปพร้อมกับ backend/frontend ที่ลงมือเขียน
→ git: stage + ส่ง tree id → qa: ตรวจบนของจริง + เขียนรายงาน → reviewer: รีวิว + เขียนรายงาน
→ lead: คัดกรองผล → git: commit เดียว → [G2 คุณอนุมัติ commit]
```
ตัวอย่างคำสั่ง:
```text
ใช้ workflow .agents/workflows/feature.md
ฟีเจอร์: ให้ API /orders กรองตามสถานะได้หลายค่า (status[]=paid&status[]=shipped)
สร้างทีม: analyst, backend, qa, reviewer, git
```

### 6.3 Migration PHP → Go

การย้ายระบบมี 3 ระดับ และทุกระดับใช้หลักการใน skill `team-migration` (ดูหัวข้อ 6.4)

| ระดับ | Workflow | ใช้เมื่อ |
|---|---|---|
| **โปรแกรม** | `migration-program.md` | ย้ายหลาย endpoint หรือทั้งระบบ |
| **ทีละหน่วย** | `migration.md` | ย้าย endpoint, job หรือ module ทีละตัว (โปรแกรมเรียกใช้ซ้ำทีละหน่วย) |
| **ปลดระบบเก่า** | `migration-retire.md` | ลบโค้ด PHP หลังคุณย้าย traffic แล้ว |

**ระดับโปรแกรม**
```
lead: สร้างโปรแกรม → analyst: ทำรายการทุกหน่วย (inventory.tsv) + หาส่วนที่ใช้ร่วมกัน (auth, error format, DB)
→ analyst: เรียงลำดับ ส่วนที่ใช้ร่วมกันก่อน → pilot ที่อ่านอย่างเดียวและเสี่ยงต่ำ → หน่วยที่เสี่ยงที่สุด
→ analyst: แผน (เงื่อนไขว่าเสร็จที่นับเป็นตัวเลขได้, โครงสร้างปลายทาง, compatibility layer, data migration)
→ qa: ลอง harness 1 case → [G1 คุณอนุมัติแผน ลำดับ และ ruling ที่ใช้ทั้งโปรแกรม]
→ รันทีละหน่วยด้วย migration.md (หน่วยถัดไปเริ่มได้เมื่อหน่วยที่มันพึ่งพา commit แล้ว)
→ หลัง pilot: ทบทวนแผน และพิจารณาสร้างเครื่องมือช่วย → migration_status.py สร้างสถานะจากข้อมูลจริง
→ [G2 คุณปิดโปรแกรมเมื่อครบเงื่อนไขและไม่มีจุดที่ข้อมูลขัดกัน]
```

**ทีละหน่วย**
```
lead: สร้างงาน (ตรวจว่าหน่วยที่พึ่งพา commit แล้ว) → analyst: อ่าน handler PHP + หา caller + ดูประวัติของพฤติกรรมแปลก ๆ
→ qa: เขียน cases.jsonl + บันทึก baseline จาก PHP (ใช้ข้อมูลทดสอบเท่านั้น)
→ analyst: แผน port (domain type ปลายทาง, compatibility layer ที่ขอบระบบ, data migration, path ที่ขอ ignore)
→ [G1 คุณอนุมัติแผนและทุก ignore] → backend: port โดยไม่แตะ PHP และไม่แก้ baseline หรือ harness
→ qa: parity.py check ต้อง exit 0 (DIFF ที่ Go "ดีกว่า" ก็ยังต้องให้คุณตัดสิน, baseline ดูผิดให้หยุดถาม)
→ qa: ตรวจ side effect + data migration รันซ้ำได้ + เขียนรายงาน
→ reviewer: รีวิว + เทียบ security check ของ PHP กับ Go → lead: คัดกรองผล → git → [G2 คุณอนุมัติ commit]
```

**ปลดระบบเก่า** (เริ่มได้หลังคุณตัดสินใจย้าย traffic และปลด PHP แล้วเท่านั้น)
```
analyst: หาทุกจุดที่อ้างถึง PHP (route, client, cron, config, test, flag) → qa: พิสูจน์ว่า path เก่าไม่มีใครใช้แล้ว
→ [G1 คุณอนุมัติแผนการลบ] → backend: ลบทั้งหมดในรอบเดียว → qa: Go ยังผ่าน baseline + ไม่มีจุดอ้างถึงเหลือ
→ reviewer: ยืนยันว่าไม่มีจุดอ้างถึงเหลือ และไม่มี security check ที่หายไปพร้อมโค้ดเก่า → git → [G2 คุณอนุมัติ commit]
```

ตัวอย่างคำสั่ง:
```text
ใช้ workflow .agents/workflows/migration-program.md
ย้าย API ทั้งหมดใน app/Http/Controllers/Api จาก PHP (http://localhost:8080) เป็น Go (http://localhost:8081)
สร้างทีม: analyst, qa ก่อน แล้วเพิ่ม backend, reviewer, git เมื่อเริ่มหน่วยแรก
```

### 6.4 หลักการ migration ที่นำมาจาก pstack

skill `team-migration` รวมหลักการเรื่อง migration ของ pstack ทั้งหมดไว้ที่เดียว และ workflow ทั้ง 3 ตัวอ้างถึงมัน

| หลักการ | ที่มาใน pstack | ใช้ในชุดนี้อย่างไร |
|---|---|---|
| เลือกระดับงานก่อน | `poteto-mode` (Refactoring / figure-it-out / Orchestrate) | 3 workflow: โปรแกรม, ทีละหน่วย, ปลดระบบเก่า |
| ตรึงพฤติกรรมก่อนย้าย และสร้าง harness ก่อนเริ่มงาน | Refactoring ขั้น 1, figure-it-out phase B | baseline จาก PHP ด้วย `parity.py` ก่อนเขียน Go |
| baseline คือ spec, ห้ามแก้ harness และห้ามบิดโค้ดให้ diff ผ่าน | Visual parity | กฎกันการโกงใน `team-migration` ข้อ 3 และใน `migration.md` |
| ย้ายส่วนที่ใช้ร่วมกันก่อน และเรียงจากสิ่งที่เสี่ยงที่สุด | Visual parity, figure-it-out | คอลัมน์ `depends_on` + ลำดับในแผน + `migration_status.py` ตรวจว่าเริ่มก่อน dependency หรือไม่ |
| งานหนึ่งหน่วยมีเจ้าของคนเดียว และงานคู่ขนานต้องแยก worktree | Feature playbook, separate-before-serializing | `team-migration` ข้อ 4 |
| มุ่งไปที่สถาปัตยกรรมปลายทาง | outcome-oriented-execution | Go เป็นแบบปลายทาง ส่วนพฤติกรรมของ PHP อยู่ใน compatibility layer ที่ขอบระบบ |
| ตรวจที่ขอบระบบ และ domain ต้องสะอาด | boundary-discipline, model-the-domain | compatibility rule ทุกข้อระบุ parity case ที่ต้องการมัน |
| ทำทีละหน่วยเล็กและตรวจทุกหน่วย | sequence-verifiable-units | rebase บน trunk ที่สะอาด, ตรวจก่อนเริ่มหน่วยถัดไป, ลำดับ commit |
| สร้างเครื่องมือเมื่องานเริ่มซ้ำ | build-the-lever | ทบทวนหลัง pilot และพิสูจน์ด้วยการ diff กับงานที่ทำมือ |
| การย้ายข้อมูลต้องรันซ้ำได้ | make-operations-idempotent | คำถาม 4 ข้อ + พิสูจน์บนข้อมูลสำเนา (D6) |
| ย้ายผู้เรียกแล้วลบของเก่าในรอบเดียว | migrate-callers-then-delete-legacy-apis | `migration-retire.md` หลังคุณย้าย traffic แล้ว (D7) |
| เข้าใจพฤติกรรมแปลก ๆ ก่อนจะลอกตาม | why, epistemics | ดูประวัติก่อน และการคงบั๊กไว้หรือแก้เป็นการตัดสินใจของคุณ |
| ruling ระดับโปรแกรมพร้อมขอบเขต | epistemics, Orchestrate `preferences.md` | ส่วน Program-wide rulings ในแผน เก็บคำพูดต้นฉบับของคุณ |
| เงื่อนไขว่าเสร็จที่นับได้ และสถานะจากข้อมูลจริง | Orchestrate, figure-it-out phase A | `migration_status.py` สร้าง `STATUS.md` และ exit 1 ถ้าข้อมูลขัดกัน |
| ตัวเลข performance ต้องอธิบายได้ | explain-the-number, benchmark-checklist | qa ใช้ `benchmark-checklist` เมื่อแผนอ้างผลด้าน performance |

**`migration_status.py` ตรวจอะไร:** หน่วยที่บอกว่า verified แต่รายงานไม่ใช่ PASS, parity ที่ยังมี DIFF หรือ UNREACHABLE, หน่วยที่บอกว่า commit แล้วแต่ไม่มี commit ในรายงาน, หน่วยที่เริ่มก่อน dependency commit และหน่วยที่ไม่มี task_id หรือไม่มีรายงาน หน่วยจะนับว่าเสร็จก็ต่อเมื่อผ่านทุกข้อ

### 6.5 ทบทวนงาน (`retro.md`)

ดัดแปลงจาก `reflect` ของ pstack เพื่อให้ทีมเรียนรู้จากงานที่จบไปแล้ว และถามคุณน้อยลงเรื่อย ๆ

```
lead: เลือกโหมด (light เป็นค่าเริ่มต้น / full ต้องให้คุณอนุมัติ D10 เพราะใช้ agent เพิ่ม 4 ตัว)
→ อ่านบันทึกของงาน (brief, decisions, log, รายงานทดสอบและรีวิว) ด้วย 3 มุม: judgment, tooling, divergent
→ คัดกรองด้วยเกณฑ์ของ synthesizer → เขียน retro.md (Accepted / Standing decision proposals / Backlog / Rejected)
→ [G1 คุณอนุมัติทีละแถว (D11)] → lead แก้เฉพาะแถวที่อนุมัติ + ตรึงกฎใน rules.json + sync_claude.py + check_team
→ git → [G2 คุณอนุมัติ commit]
```

**เกณฑ์คัดกรอง** ได้แก่
- **ยังจริงไหมในอีก 6 เดือน**
- **ทีมจะทำต่างไปจริงไหม** ไม่ใช่แค่อ่านมากขึ้น
- **มีไฟล์ที่ดูแลเรื่องนี้อยู่แล้วหรือยัง**
- **ไฟล์เป้าหมายเขียนเรื่องนี้ไว้แล้วหรือยัง**
- **ทำเป็น hook, check หรือ script ได้ไหม** ถ้าได้ ให้ไปอยู่ใน Backlog แทนการเพิ่มข้อความ

**แหล่งข้อมูล:** retro อ่านจาก **บันทึกของงาน** ใน `.agents/work/<task-id>/` แทน transcript เพราะแต่ละ teammate มีแชตแยกกัน บันทึกจึงเป็นที่เดียวที่ครอบคลุมทั้งทีม

**ไม่มีอะไรถูกแก้เองโดยอัตโนมัติ** ทุกแถวต้องผ่านการอนุมัติของคุณ และการเปลี่ยนกฎของทีมเป็นการตัดสินใจ D11

### 6.6 หยุดงานและกลับมาทำต่อ (`team-checkpoint`)

**ปัญหา:** Agent Teams **resume teammate ไม่ได้** ถ้าปิด session ทีมจะหายทั้งหมด

**หยุดงาน** เมื่อคุณสั่ง เช่น "หยุดก่อน" หรือ "พักงาน" หรือเมื่อ session ใกล้หมด
1. lead สั่งให้ทุกคนหยุดที่จุดที่ปลอดภัย และไม่ commit หรือ push เพื่อหยุดงาน
2. git stage งานที่เสร็จแล้วและรายงาน tree id
3. lead เขียน `checkpoint-note.md` ให้คนที่ไม่เคยเห็นแชตนี้อ่านเข้าใจ ได้แก่ เป้าหมาย, สิ่งที่เสร็จและตรวจแล้ว, สิ่งที่ค้าง, ขั้นต่อไป, ทีมที่ต้องตั้งใหม่ และเรื่องที่รอคุณตัดสิน
4. รัน `python3 .agents/scripts/checkpoint.py save <task-id>` script จะไม่ยอมบันทึกถ้ายังมีหัวข้อว่าง, มีช่องที่ยังไม่ได้กรอก หรือมี path ที่ไม่มีอยู่จริง ถ้าผ่าน จะบันทึก hash ของทุกไฟล์ที่อ้างถึง และสถานะของทุก worktree (HEAD, tree ที่ stage และจำนวนไฟล์ที่เปลี่ยน)

**กลับมาทำต่อ** ใน session ใหม่ ให้พิมพ์ว่า "ทำต่อจากเมื่อวาน"
1. lead รัน `python3 .agents/scripts/checkpoint.py read`
2. script แสดง note พร้อม **รายการสิ่งที่เปลี่ยนไปตั้งแต่ตอนหยุด** เช่น ไฟล์ที่ถูกแก้ หรือ worktree ที่ tree หรือ HEAD เปลี่ยน
3. lead ตรวจข้ออ้างที่งานต่อจากนี้ต้องพึ่งพาซ้ำ ไม่ทำงานที่เสร็จแล้วซ้ำ แล้วตั้งทีมใหม่ตาม note

checkpoint แต่ละชุดแก้ไม่ได้หลังบันทึก และไม่ได้ทำให้ข้ามจุดอนุมัติใด ๆ ได้

### 6.7 กันการวนไม่รู้จบ (`protocols/loops.md`)

ดัดแปลงจาก pstack: retry ตามประเภทความล้มเหลวและ "2 ครั้งแล้วเลิก" ของ Orchestrate, "3 รอบแล้วหยุด" ของ skill `babysit`, flaky ให้ retry ครั้งเดียวของ playbook Babysit และหลัก `attack-the-premise` ส่วนตัวตรวจจับการวน (`loop_guard.py`) เป็นของใหม่ที่ pstack ไม่มี

| กลไก | ทำอะไร | บังคับด้วย |
|---|---|---|
| **งบ 3 รอบต่องาน** | หนึ่งรอบคือ แก้ → stage → ทดสอบ → รีวิว รายงานทั้งสองฉบับมีช่อง **Round** | `gate_reports.py` ไม่ยอมปิดงานรอบที่ 4 ขึ้นไป ถ้าไม่มี D9 ที่คุณอนุมัติ |
| **ล้มแบบเดิม 2 ครั้ง = หยุด** | เขียนสมมติฐานที่ทั้งสองรอบใช้ร่วมกันออกมา ทดสอบมัน แล้วส่ง D9 ให้คุณ | คำสั่ง + `team_health.py` เตือน |
| **retry ตามประเภทความล้มเหลว** | เกินเวลาหรือ memory ให้ลด scope, network ให้ retry ครั้งเดียว, tool error ให้เปลี่ยนวิธี, flaky ให้รันใหม่ครั้งเดียว ครบ 2 ครั้งแล้วให้รายงาน `BLOCKED` | คำสั่ง |
| **ตรวจจับการวน** | agent ตัวเดิมรันคำสั่งเดิมซ้ำ **6 ครั้งใน 10 นาที โดยไม่มีไฟล์เปลี่ยน** hook จะปฏิเสธ และบอกให้หยุดแล้วรายงาน `BLOCKED` ถ้ามีการแก้ไฟล์หรือ stage ระหว่างรอบ hook นับว่ามีความคืบหน้าและเริ่มนับใหม่ | `loop_guard.py` (PreToolUse) |
| **lead คอยเฝ้า** | `team_health.py` แสดง agent ที่ใกล้ถึงเพดาน, งานที่ถึงรอบ 3 และแถวใน `log.tsv` ที่ซ้ำ | script ที่ lead ต้องรันทุกครั้งที่ teammate รายงาน |
| **เปลี่ยนตัว ไม่สั่งซ้ำ** | teammate ที่ติดวนให้หยุด แล้ว spawn ตัวใหม่พร้อม brief ที่รวม brief เดิม, คำสั่งที่เพิ่มทีหลัง, รายงานล่าสุด และหลักฐานการวน (หลัก fresh subagent ของ pstack) ถ้าตัวใหม่ติดที่เดิมอีก แปลว่าเป็นทางตัน ให้ส่ง D9 | คำสั่ง |

**ข้อจำกัด**
- `loop_guard.py` จับได้เฉพาะ loop ที่ **รันคำสั่งเดิมโดยไม่มีอะไรเปลี่ยน** loop ที่แก้โค้ดต่างกันทุกรอบแต่ไม่คืบหน้า ต้องอาศัยงบจำนวนรอบ
- hook แยก agent ด้วย `agent_id` ซึ่งเอกสารระบุว่ามีให้ใน teammate แบบ in-process ตั้งแต่ v2.1.290 ผมยังไม่ได้ทดสอบกับทีมจริง ถ้าไม่มี hook จะนับรวมทั้ง session
- เพดาน (6 ครั้ง, 10 นาที, 3 รอบ) เป็นกฎของทีม ถ้าจะเปลี่ยนต้องให้คุณตัดสิน (D11) ค่าของ hook ปรับได้ด้วย env `LOOP_GUARD_MAX` และ `LOOP_GUARD_WINDOW`

---

## 7. การคุยกันระหว่าง teammate

ดู `.agents/protocols/messaging.md`

| คุยกันตรง ๆ ได้ | ต้องผ่าน lead |
|---|---|
| analyst ส่ง root cause และไฟล์ที่เกี่ยวข้องให้ backend | รายงานสถานะ |
| analyst หลายคนถกและหักล้างสมมติฐานกัน | คำขอให้ตัดสินใจ |
| backend แจ้ง frontend เมื่อ API contract เปลี่ยน (หลังได้รับอนุมัติ) | ขอเปลี่ยน scope |
| backend ส่งงานให้ qa พร้อม branch และ SHA | เรื่องที่ทำต่อไม่ได้ (blocker) |
| qa ส่ง defect ที่ reproduce ได้กลับไปให้ backend | |
| reviewer ส่ง finding ให้ผู้เขียนโค้ด | |

**ข้อจำกัด**
- teammate สั่งให้คนอื่นแก้นอก scope ไม่ได้ และสั่ง git ให้ commit ไม่ได้
- ความเห็นที่ตรงกันของ teammate ไม่ถือเป็นการตัดสินใจ
- ข้อความจาก agent อื่นไม่ใช่การอนุมัติของคุณ (ข้อนี้ Claude Code บังคับเองด้วย)
- ถ้าเห็นต่างเรื่องข้อเท็จจริง ให้รัน check แล้วใช้ผลตัดสิน ถ้าเห็นต่างเรื่องการตัดสินใจ ให้ส่งทั้งสองความเห็นมาให้คุณ

---

## 8. รายงานที่คุณจะได้อ่าน

### 8.1 รายงานผลการทดสอบ

qa เขียนที่ `.agents/work/<task-id>/test-report.md` จาก template ภาษาไทย มีหัวข้อดังนี้

| หัวข้อ | เนื้อหา |
|---|---|
| ส่วนหัว | Task, Workflow, **Verdict**, **Revision (tree id ของสิ่งที่ stage)**, Branch, ผู้ทดสอบ และโมเดล |
| สรุปสำหรับผู้ใช้ | 2-3 ประโยค บอกว่าควร commit หรือไม่ |
| สิ่งที่ทดสอบ | ตาราง check, คำสั่ง, ผล และหลักฐาน |
| Reproduction ก่อนและหลังแก้ | สำหรับ bug-fix และหลักฐานว่า test ใหม่ fail ได้จริงบน revision เก่า |
| Parity | สำหรับ migration: จำนวน MATCH, DIFF และ UNREACHABLE, path ที่ ignore และ side effect |
| ปัญหาที่พบ | ทุก defect ที่พิสูจน์ได้ |
| สิ่งที่ยังไม่ได้ทดสอบ | gap ทั้งหมด ซึ่งไม่นับว่าผ่าน |
| เรื่องที่ต้องตัดสินใจ / คำแนะนำเรื่อง commit / Commit | lead เติม commit SHA หลังคุณอนุมัติ |

**Verdict มี 4 ค่า:** `PASS`, `ISSUES`, `BLOCKED` และ `INCONCLUSIVE` ค่า `INCONCLUSIVE` ไม่นับว่าผ่าน

**hook บังคับคุณภาพของรายงาน:** `gate_reports.py` จะไม่ยอมให้งานชื่อ `[<task-id>] verify: ...` ถูกปิด ถ้ารายงานยังมี `<fill` เหลืออยู่, ไม่มี verdict ที่ถูกต้อง หรือไม่มี tree id

ไฟล์อื่นในโฟลเดอร์เดียวกัน
- `review-report.md`: รายงานรีวิว (หัวข้อ 8.2)
- `brief.md`: brief ที่ใช้มอบงาน
- `decisions.md`: การตัดสินใจทั้งหมดของคุณ พร้อมคำพูดต้นฉบับ
- `investigation.md` และ `design.md`: งานของ analyst
- `log.tsv`: บันทึกการตัดสินใจทุกจุด แบบเพิ่มได้อย่างเดียว

---

### 8.2 รายงานรีวิวโค้ด

reviewer เขียนที่ `.agents/work/<task-id>/review-report.md` ใช้ skill `team-review` ซึ่งดัดแปลงจาก `interrogate` (rubric, code-quality lens, lead judgment), `deslop` และ `no-comments` ของ pstack

**8 มุมที่ตรวจ** (Correctness กับ Security ต้องตรวจทุกครั้ง)

| มุม | ดูอะไร |
|---|---|
| **Correctness** | edge case, error handling, concurrency, รันซ้ำหรือ crash กลางทาง และต้องไล่ call path ให้เห็น |
| **Root cause หรือปิดอาการ** | guard, retry หรือ cast ที่ซ่อนปัญหาจริง และคำสั่ง "อย่าทำ X" ที่ควรเป็น type หรือ lint |
| **Security** | input ไปถึง SQL, shell, path หรือ HTML, auth และสิทธิ์ระดับ object, secret หรือข้อมูลส่วนบุคคลใน log หรือ fixture, TOCTOU และ **check ที่ PHP มีแต่ Go ทำหาย** |
| **Structure** | validation อยู่ที่ขอบระบบ, logic อยู่ใน layer ที่ถูก, ไม่มี if กระจาย, ไฟล์ไม่เกิน 1,000 บรรทัด และ compatibility rule อยู่ใน response-mapping layer |
| **Verification** | test ทดสอบพฤติกรรมจริงไหม, test fail ได้จริงไหม และเทียบกับรายงานผลทดสอบที่ tree id เดียวกัน |
| **Complexity budget** | abstraction ที่ใช้ที่เดียว, config สำหรับกรณีที่ไม่มีจริง และโค้ดที่ไม่ใช้แล้ว |
| **Clutter** | comment ที่ไม่จำเป็น, defensive check เกินเหตุ, cast `any` และ nesting ลึก |
| **ตรงกับที่คุณอนุมัติ** | diff ทำตามตัวเลือกที่คุณเลือก ไม่เกินกว่านั้น |

**Verdict มี 3 ค่า:** `NO_FINDINGS`, `FINDINGS` และ `BLOCKED` และแต่ละ finding มีระดับ `critical` / `warning` / `nit` พร้อม `file:line` และหลักฐาน

**lead คัดกรองผลเป็น 4 กลุ่ม** (จาก lead judgment ของ pstack)

| กลุ่ม | ความหมาย |
|---|---|
| **แก้ก่อน commit** | ปัญหาจริงด้าน correctness, security หรือ maintainability ถ้ามีเกิน 5 ข้อแปลว่ายังกรองไม่พอ หรืองานควรคิดใหม่ |
| **ควรพิจารณา** | ถ้าการแก้ต้องเปลี่ยน design หรือพฤติกรรม ต้องส่งเป็นคำขอให้คุณตัดสิน |
| **รับทราบ** | ถูกต้องแต่ยังไม่ต้องทำตอนนี้ |
| **ปัดตก** | พร้อมเหตุผลบรรทัดเดียว **การปัดตก finding ระดับ critical ต้องให้คุณตัดสิน (D3)** |

กลุ่ม "ปัดตก" แสดงให้คุณเห็นว่าอะไรถูกตัดทิ้งและเพราะอะไร คุณจึงกลับคำตัดสินของ lead ได้

**งานเสี่ยงสูง:** ถ้า diff แตะ auth, เงิน, ข้อมูลส่วนบุคคล, สิทธิ์, data migration หรือ cryptography reviewer จะส่งคำขอให้ตัดสินใจ (D10) ถามคุณว่าจะให้อีกโมเดลรีวิวซ้ำไหม พร้อมบอกต้นทุนโดยประมาณ ถ้าคุณอนุมัติ lead รวมผลจากทั้งสอง reviewer ข้อที่ทั้งคู่เจอตรงกันมีน้ำหนักที่สุด

**รีวิวซ้ำหลังแก้:** reviewer ดูเฉพาะส่วนที่เปลี่ยนระหว่าง tree id เก่ากับใหม่ (`git diff <old-tree> <new-tree>`) และยืนยันว่าทุกข้อใน "แก้ก่อน commit" แก้แล้ว

**hook ที่บังคับ**
- `gate_reports.py` ไม่ยอมให้ปิดงาน `review` ถ้าส่วนของ reviewer ยังไม่เสร็จ
- `guard_git.py` ไม่ยอมให้ commit ถ้าส่วนคัดกรองของ lead (`<lead`) ยังไม่เสร็จ

---

## 9. อะไรบังคับด้วยโค้ด อะไรเป็นแค่คำสั่ง

ตรงไปตรงมาเรื่องนี้ เพราะ pstack สอนว่ากฎที่เป็นข้อความอาจถูกข้ามได้

| กฎ | บังคับด้วย | ระดับ |
|---|---|---|
| `git commit`, `git push`, `merge`, `rebase` และ `gh pr create` ต้องให้คุณอนุมัติ | ask rule ใน settings (ถามทุกโหมด) + hook `guard_git.py` ดักรูปแบบอื่น เช่น `git -C . commit` หรือ `bash -c "..."` | **โค้ด** |
| ห้าม force-push, `reset --hard`, `clean -f`, `branch -D`, `gh pr merge` และ `commit --no-verify` | deny rule + hook | **โค้ด** |
| งาน verify และ review ปิดไม่ได้ถ้ารายงานยังไม่เสร็จ | hook `gate_reports.py` | **โค้ด** |
| commit ไม่ได้ถ้ารายงานผลทดสอบหรือส่วนคัดกรองของ lead ยังไม่เสร็จ | hook `guard_git.py` (อ่าน `Task:` จากข้อความ commit) | **โค้ด** (ถ้าข้อความไม่มี `Task:` hook จะถามคุณพร้อมแจ้งว่าไม่ได้ตรวจรายงาน) |
| คุณเห็นว่าสิ่งที่จะ commit ตรงกับที่ถูกทดสอบและรีวิวหรือไม่ | hook เทียบ `git write-tree` กับ Revision ในรายงาน และเขียนผลลงใน prompt | **โค้ด** (แจ้งเตือน ไม่ใช่ปฏิเสธ คุณเป็นคนตัดสิน) |
| git และ reviewer ไม่แก้ไฟล์ source | git ถูกตัด Edit และ Write ส่วน reviewer ถูกตัด Edit (ต้องมี Write ไว้เขียนรายงาน) | **บางส่วน** ทั้งคู่ยังมี Bash ซึ่งเขียนไฟล์ได้ (เช่น `echo >`) จึงพึ่งคำสั่งด้วย แต่ git ตรวจ scope ก่อน stage และ hook เทียบ tree ทำให้การแก้ที่หลุดเข้ามาถูกเห็น |
| ข้อความจาก agent ไม่ใช่การอนุมัติของคุณ | Claude Code เอง | **โค้ด** |
| งานเกิน 3 รอบต้องได้ D9 จากคุณ | `gate_reports.py` อ่านช่อง Round | **โค้ด** |
| agent ที่รันคำสั่งเดิมซ้ำโดยไม่คืบหน้าถูกหยุด | `loop_guard.py` | **โค้ด** (จับได้เฉพาะคำสั่งซ้ำ ส่วน loop แบบอื่นใช้งบรอบ) |
| lead เปลี่ยน teammate ที่ติดวนเป็นตัวใหม่ | คำสั่ง + `team_health.py` เตือน | คำสั่ง + ตรวจ |
| กฎสำคัญใน AGENTS.md และ protocol ไม่หายไปจากไฟล์ | `rules.json` + `check_team.py` | **โค้ด** (ป้องกันแค่ไม่ให้ประโยคหาย ไม่ได้บังคับให้ทำตาม) |
| lead ห้ามตัดสินใจแทนคุณ | คำสั่งใน AGENTS.md และ protocol | คำสั่ง |
| checkpoint ครบและอ้างไฟล์ที่มีอยู่จริง และตอนกลับมาเห็นสิ่งที่เปลี่ยนไป | `checkpoint.py` ตรวจ note ตอนบันทึก และเทียบ hash กับสถานะ worktree ตอนอ่าน | **โค้ด** |
| standing decision ห้ามครอบคลุม D7, D8 และ D11 และต้องมีคำพูดของคุณ | `check_team.py` | **โค้ด** (ตรวจรูปแบบ ส่วนการตัดสินว่ารายการใช้ได้กับกรณีไหนยังเป็นวิจารณญาณของ teammate) |
| สำเนาใน `.claude/` ตรงกับ `.agents/` หลัง retro แก้กฎ | `sync_claude.py` + `check_team.py --installed` | **โค้ด** |
| retro แก้เฉพาะแถวที่คุณอนุมัติ | คำสั่ง + commit ต้องให้คุณอนุมัติพร้อมเห็นแถวที่อนุมัติ | คำสั่ง + อนุมัติ |
| analyst ห้ามแก้ source และ qa ห้ามแก้ production code | คำสั่ง (ทั้งคู่ต้องมี Write จึงจำกัดด้วยเครื่องมือไม่ได้) | คำสั่ง |
| แต่ละคนแตะไฟล์คนละชุด | คำสั่ง + git ตรวจ diff เทียบ scope ก่อน stage | คำสั่ง + ตรวจ |
| lead ไม่เขียนโค้ดเอง | คำสั่ง | คำสั่ง |

**ข้อสังเกตเรื่อง hook:** ask rule ใน settings คือกลไกหลัก เอกสารระบุชัดว่ามันถามทุกโหมด ส่วน hook เป็นชั้นที่สองที่ดักรูปแบบคำสั่งที่ ask rule ไม่จับ ผมยังไม่ได้ทดสอบว่าคำตอบ `ask` จาก hook ถามทุกโหมดเหมือน ask rule หรือไม่

---

## 10. นำอะไรมาจาก pstack

| จาก pstack | ใช้ในชุดนี้ที่ |
|---|---|
| Playbook Bug fix, Feature, Refactoring | `workflows/*.md` (ขั้นตอน + ใครทำ + gate) |
| Pause safely, Session pickup, `resume.mjs` | skill `team-checkpoint` + `checkpoint.py` |
| retry ตามประเภทความล้มเหลว (Orchestrate), 3 รอบแล้วหยุด (`babysit`), flaky retry ครั้งเดียว (Babysit), `attack-the-premise` | `protocols/loops.md` + ช่อง Round + `loop_guard.py` + `team_health.py` |
| Orchestrate `preferences.md` + epistemics (คำพูดต้นฉบับพร้อมขอบเขต) | `standing-decisions.md` + ส่วน Standing decisions ใน `decisions.md` |
| `reflect` (3 มุม + synthesizer + อนุมัติทีละแถว + structural ก่อนข้อความ) | skill `team-reflect` + workflow `retro.md` |
| `create-verification-skill`, `maintain-verification-skill` | คัดลอกมาทั้งสองตัว ใช้โดย qa |
| `how`, `why`, `blast-radius` | skill `team-investigate` |
| Bug fix ขั้น binary search + `fix-root-causes` + `attack-the-premise` | skill `team-root-cause` (เพิ่มโหมดให้ analyst ถกกัน) |
| `architect` + design red flags + usage first | skill `team-design-options` |
| `prove-it-works`, `test-behavior-not-implementation`, `tdd`, verdict ของ `swarm` | skill `team-verify` |
| `interrogate` rubric + lead judgment + `deslop` + `no-comments` | skill `team-review` |
| Refactoring "pin the contract first" + starter kit | skill `team-parity` + `parity.py` |
| brief template ของ Orchestrate ("The brief is the product") | `templates/brief.md` |
| `show-me-your-work` (TSV ที่เพิ่มได้อย่างเดียว และกัน formula injection) | `log.tsv` + `log_row.py` |
| `epistemics` (เก็บคำพูดต้นฉบับ และป้าย measured / inferred / guess) | `protocols/decisions.md` + ทุก agent |
| `separate-before-serializing-shared-state` | ทุกคนแตะไฟล์คนละชุด และมี branch หรือ worktree ของตัวเอง |
| ผู้ตรวจไม่ใช่ผู้ทำ และใช้โมเดลต่างกัน | qa/reviewer ใช้ `opus` ส่วน backend ใช้ `sonnet` |
| `encode-lessons-in-structure` | ask rule, hook, `rules.json` และ `check_team.py` |
| test ที่ตรึงกฎ (`skill-rules.test.mjs`) | `rules.json` |
| ทุก check ต้องพิสูจน์ได้ว่า fail ได้จริง (`invariants.test.mjs`) | `tests/test_team_kit.py` ใส่บั๊ก 9 แบบให้ `check_team` จับ |

**สิ่งที่ไม่ได้นำมา และเหตุผล**
- **`never-block-on-the-human` ในส่วนที่ให้ agent ตัดสินใจเองในงานที่ย้อนกลับได้:** ขัดกับความต้องการของคุณ จึงเก็บไว้แค่ส่วน "ข้อเท็จจริงให้รันหาคำตอบ ไม่ต้องถาม"
- **Orchestrate, Autopilot และ Shipping:** ซับซ้อนเกินงานปัจจุบัน และ Agent Teams มีทีมได้ทีมเดียวและซ้อนไม่ได้
- **panel 3 โมเดลในทุกการรีวิว:** แพงเกินไป จึงใช้ reviewer ตัวเดียวที่ใช้โมเดลต่างจากผู้เขียนแทน

---

## 11. เริ่มใช้งานอย่างปลอดภัย

1. **ติดตั้งและตรวจ:** `python3 install.py <project>` แล้วดูว่าได้ `OK`
2. **ให้ทีมสร้าง skill `verify` ก่อนงานแรก:** สั่ง lead ว่า "ให้ qa ใช้ create-verification-skill สร้าง verify skill ของโปรเจกต์นี้" แล้วอนุมัติ (D4) qa จะได้ขับ PHP และ Go จริงได้ตั้งแต่งานแรก
3. **ลองงานที่ไม่ต้องเขียนโค้ดก่อน** (ตามคำแนะนำในเอกสาร Agent Teams) เช่น ให้ analyst กับ qa สืบบั๊กที่รู้คำตอบอยู่แล้ว แล้วดูว่า root cause และการส่งคำขอให้ตัดสินใจทำงานตามที่ออกแบบไว้หรือไม่
4. **ลอง commit gate:** ให้ git commit ไฟล์ทดสอบเล็ก ๆ ใน branch ทดลอง แล้วดูว่า prompt เด้งขึ้นที่ session ของ lead จริง
5. **ลอง migration กับ endpoint ที่อ่านอย่างเดียว 1 ตัว** เป็น pilot
6. **จดค่าใช้จ่าย** จาก `/usage` และดูส่วน Attribution
7. **ปรับกฎจากสิ่งที่เจอ:** หลังจบงาน ให้รัน retro (`workflows/retro.md`) และอนุมัติเฉพาะแถวที่เห็นด้วย คำตอบที่ใช้ซ้ำได้ให้เพิ่มเป็น standing decision

---

## 12. ทดสอบชุดนี้

```bash
cd agent-team-roles
python3 .agents/scripts/check_team.py     # โครงสร้าง ลิงก์ และกฎที่ตรึงไว้
python3 tests/test_hooks.py               # guard_git, commit gate (git repo จริง) และ gate_reports (21 ข้อ)
python3 tests/test_team_kit.py            # new_task, log_row, check_team (ใส่บั๊ก 9 แบบ), install และ vendor (13 ข้อ)
python3 .agents/scripts/vendor_pstack_skills.py --check   # skill ที่คัดลอกจาก pstack ยังตรงกับต้นฉบับ
python3 tests/test_parity.py              # parity.py (8 ข้อ)
python3 tests/test_migration.py           # new_task (program, retire) และ migration_status (4 ข้อ)
python3 tests/test_continuity.py          # checkpoint, standing decisions, sync_claude และ comment ใน template (10 ข้อ)
python3 tests/test_loops.py               # loop_guard, งบรอบใน gate_reports และ team_health (12 ข้อ)
```

---

## 13. ข้อจำกัดที่ควรรู้

- **Agent Teams ยังเป็น experimental:** resume teammate ไม่ได้, task status อาจไม่อัปเดตทันที และ shutdown ช้า (จากเอกสาร)
- **lead อาจลงมือเขียนเองแทนที่จะรอ teammate:** ถ้าเห็นแบบนั้น ให้พิมพ์ "รอ teammate ทำงานให้เสร็จก่อน" ตามที่เอกสารแนะนำ
- **Plan mode:** ถ้า lead อยู่ใน plan mode lead จะอนุมัติแผนของ teammate ให้อัตโนมัติ ชุดนี้จึงไม่ใช้ plan mode เป็นจุดอนุมัติ แต่ใช้ G1 ผ่าน decision protocol แทน
- **ต้นทุน:** ทีม 4-5 คนที่ใช้ `opus` 3 ตัว ใช้ token มาก ดู [เทียบ Agent Teams กับ pstack](../pstack-study-th/PSTACK-VS-AGENT-TEAMS-TH.md) หัวข้อ 5
- **การตัดสินใจทุกเรื่องผ่านคุณทำให้งานช้าลง:** นี่เป็นข้อแลกเปลี่ยนที่ตั้งใจ ถ้าพบว่าถูกถามบ่อยเกินไป ให้ย้ายบางเรื่องจากตาราง "What is a decision" ไปไว้ใน "What is not a decision" ใน `.agents/protocols/decisions.md`
- **ช่อง `skills` ในนิยาม agent ไม่มีผลกับ teammate:** ชุดนี้จึงติดตั้ง skill ไว้ที่ `.claude/skills/` ของโปรเจกต์ ซึ่ง teammate โหลดได้
