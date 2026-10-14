# คู่มือติดตั้งและใช้งาน pstack (ภาษาไทย)

pstack คือชุดสกิล (skill stack) สำหรับ AI coding agent ต้นฉบับโดย Lauren Tan และพอร์ตมาใช้กับ Claude Code, Codex, Pi และ agent อื่นโดย Michael Denyer ช่วยให้ agent ทำงานกระชับ เรียบง่าย และตรวจสอบผลได้จริง

> โฟลเดอร์ `pstack-claude-main` ที่ดาวน์โหลดมาคือซอร์สของปลั๊กอิน ไม่ต้องรันในโฟลเดอร์นี้โดยตรง ให้ติดตั้งแล้วไปใช้ในโปรเจกต์จริงของคุณ

---

## 1. ติดตั้ง

### Claude Code (แนะนำ)

พิมพ์ใน Claude Code:

```text
/plugin marketplace add michael-denyer/pstack-claude
/plugin install pstack@pstack-claude
```

ปลั๊กอินจะติดตั้ง hook ที่ทำให้ Claude เรียก `poteto-mode` เองโดยอัตโนมัติเมื่อ
- งานแตะมากกว่าหนึ่งไฟล์ หรือเปลี่ยน signature ที่ไฟล์อื่นเรียกใช้
- งานเกี่ยวกับการออกแบบหรือสถาปัตยกรรม
- เป็นบั๊กที่ยังไม่รู้สาเหตุ หรือปัญหาประสิทธิภาพ

### Codex

รันใน terminal:

```shell
codex plugin marketplace add michael-denyer/pstack-claude
codex plugin add pstack@pstack-claude
```

จากนั้น Codex จะขอให้ trust hook ผ่านคำสั่ง `/hooks` ต้องอนุมัติก่อน hook ถึงจะทำงาน

### Pi

```shell
pi install git:github.com/michael-denyer/pstack-claude
```

เรียกสกิลด้วย `/skill:<ชื่อสกิล>`

### Prime Agent / opencode / Gemini CLI (ติดตั้งเฉพาะสกิล)

วิธี A: clone แล้วทำ symlink

```shell
git clone https://github.com/michael-denyer/pstack-claude
cd pstack-claude
mkdir -p ~/.agents/skills
for s in plugins/pstack/skills/*/; do
  target=~/.agents/skills/"$(basename "$s")"
  test -e "$target" || test -L "$target" || ln -s "$(pwd)/$s" "$target"
done
```

- ต้องเก็บโฟลเดอร์ที่ clone ไว้ที่เดิม เพราะ symlink ชี้ไปที่นั่น
- อัปเดตด้วย `git pull` ในโฟลเดอร์นั้น
- ถอนการติดตั้งโดยลบ link ที่ `~/.agents/skills/<ชื่อสกิล>`
- ถ้าปลายทางมีอยู่แล้ว สคริปต์จะข้าม ให้ตรวจดูก่อนเขียนทับ

วิธี B: ใช้ skills CLI โดยไม่ต้องเก็บ clone

```shell
npx skills add https://github.com/michael-denyer/pstack-claude/tree/main/plugins/pstack/skills --skill "*" --agent "*" --yes
```

หมายเหตุ: ใน Gemini CLI ใช้ `/skills list` เพื่อตรวจว่าเจอสกิลหรือไม่ และ `/skills reload` หลังแก้ไข การรองรับ Prime Agent และ Gemini CLI ตามเอกสารของโปรเจกต์ยังไม่ได้ทดสอบกับ session จริง

---

## 2. ตั้งค่าครั้งแรก

รัน `setup-pstack` (ใน Claude Code พิมพ์ `/pstack:setup-pstack`) เพื่อ
- เลือกโมเดลที่ใช้ในแต่ละบทบาท (role) เช่น `arena runners`, `how critics`, `swarm workers`
- กำหนดระดับ reasoning effort ต่อบทบาท เช่น `arena runners: opus @xhigh, fable @max`
- เปิดหรือปิดการ route อัตโนมัติ

สกิลจะอ่านค่าจากไฟล์ override ชื่อ `pstack-models.md` ซึ่ง `setup-pstack` เป็นคนเขียนให้ ถ้าไม่ตั้งค่า จะใช้ค่าเริ่มต้นของปลั๊กอิน (เช่น feature และ refactoring ใช้ `opus`, bug-fix และ perf-issue ใช้ `fable`)

---

## 3. เริ่มใช้งาน

วิธีที่ง่ายที่สุดคือบอกเป้าหมายให้ `poteto-mode` ซึ่งจะเลือก playbook และสกิลย่อยให้เอง

```text
Use poteto-mode to fix the search filter resetting when I change pages.
```

ตัวอย่างกรณีบั๊ก: มัน reproduce ปัญหา, ใช้ `how` และ `why` สืบสวน, มอบหมายการแก้, แล้วรันเคสที่พังซ้ำ ถ้าการแก้ข้ามขอบเขตของฟังก์ชัน มันจะเรียก `architect` ก่อนลงมือ สิ่งที่คุณได้รับคือโค้ดที่แก้แล้วพร้อมหลักฐานก่อนและหลังแก้

ถ้ารู้อยู่แล้วว่าต้องการอะไร เรียกสกิลตรงได้เลย เช่น `pstack:tdd`, `pstack:architect`, `pstack:how`, `pstack:why`, `pstack:arena`, `pstack:interrogate`

---

## 4. Playbooks ใน poteto-mode

| ประเภทงาน | Playbook |
|---|---|
| ถาม/สืบค้น (อ่านอย่างเดียว) | Investigation, Runtime forensics, Trace forensics |
| แก้ไข/ปรับปรุง | Bug fix, Perf issue, Hillclimb (ไล่ปรับ metric เดียวอย่างเป็นระบบ) |
| สร้าง/ปรับโครงสร้าง | Feature, Refactoring, Prototype, Visual parity |
| งาน PR | Opening a PR, Babysit, Shipping |
| งานใหญ่/รันยาว | Autonomous run, Orchestrate, Autopilot-full, Autopilot-stack, Multi-phase plan, `figure-it-out` |
| งานจัดการ | Session pickup, Pause safely, Worktree cleanup, Authoring a skill, Eval |

ถ้าไม่มี playbook ไหนเข้ากับงาน `figure-it-out` จะออกแบบ playbook เฉพาะงานให้

โปรเจกต์ของคุณเพิ่ม playbook เองได้ที่ `.agents/playbooks/*.md` โดยใน frontmatter ระบุ `extends` และ `when`

---

## 5. สกิลที่เรียกตรงได้

| กลุ่ม | สกิล | ใช้เมื่อ |
|---|---|---|
| ทำความเข้าใจ | `how` | อยากรู้ว่าโค้ดทำงานอย่างไร หรือควรวางโค้ดไว้ที่ไหน |
| | `why` | อยากรู้เหตุผลการออกแบบ หรือสาเหตุของ regression |
| | `teach` | อยากเข้าใจงานชิ้นหนึ่งอย่างลึก |
| | `recall` | ให้สรุปบริบทงานล่าสุดของคุณ |
| | `bro` | ให้เล่าข้อความล่าสุดใหม่ด้วยภาษาคนธรรมดา |
| ออกแบบ | `architect` | ร่าง type, signature และโครงสร้างโมดูลก่อนเขียนโค้ด |
| | `arena` | ให้หลายตัวทำงานเดียวกัน แล้วเลือกและผสมส่วนที่ดีที่สุด |
| | `swarm` | แตกงานให้ worker ขนานกัน แล้วรวมเป็นรายงานเดียว |
| รีวิว/ตรวจสอบ | `interrogate` | ให้หลายโมเดลช่วยโต้แย้งและหาจุดบอด |
| | `blast-radius` | หาว่าการเปลี่ยนแปลงกระทบส่วนอื่นอย่างไร |
| | `thermo-nuclear-code-quality-review` | รีวิวความดูแลรักษาได้แบบเข้มงวด |
| | `benchmark-checklist` | ตรวจความน่าเชื่อถือของผล benchmark |
| คุณภาพโค้ด | `tdd` | ต้องการ test ที่ล้มก่อนแล้วค่อยแก้ |
| | `deslop`, `unslop` | ลบร่องรอย AI ออกจากโค้ดและข้อความ |
| | `no-comments` | หาและแก้ comment ที่ไม่จำเป็น |
| | `typescript-best-practices` | เมื่อแก้ไฟล์ .ts/.tsx |
| | `technical-writing` | เขียนหรือรีวิวเอกสารเทคนิค |
| PR และ CI | `babysit` | ดู PR ที่เปิดแล้ว แก้ CI และคอมเมนต์ จน merge ได้ |
| | `fix-ci` | หา check ที่ล้มและแก้ |
| | `fix-merge-conflicts` | แก้ conflict แล้วตรวจ build/test |
| | `get-pr-comments` | สรุปคอมเมนต์รีวิวของ PR |
| | `make-pr-easy-to-review` | จัดประวัติ commit และคำอธิบาย PR |
| | `what-did-i-get-done` | สรุป commit ของคุณในช่วงเวลาที่ต้องการ |
| ปรับแต่งตัวเอง | `automate-me` | เก็บสไตล์การทำงานของคุณเป็นสกิลส่วนตัว |
| | `reflect` | สรุปบทเรียนจาก transcript แล้วเสนอแก้สกิล |
| | `create-verification-skill` | สร้างสกิลที่ขับแอปเหมือนผู้ใช้เพื่อตรวจงาน |
| | `maintain-verification-skill` | ตรวจและดูแลสกิลข้างต้นให้ถูกต้อง |
| | `show-me-your-work` | บันทึกการตัดสินใจเป็นไฟล์ TSV ให้ตรวจย้อนหลังได้ |
| | `setup-pstack` | ตั้งค่าโมเดลและ routing |

นอกจากนี้มีสกิล `principle-*` ประมาณ 20 ตัว เป็นหลักคิดที่ agent หยิบมาใช้เองตามสถานการณ์ เช่น `fix-root-causes`, `prove-it-works`, `laziness-protocol`, `type-system-discipline` ปกติไม่ต้องเรียกเอง

---

## 6. ข้อควรรู้

- **ค่าใช้จ่าย:** `arena`, `interrogate`, `swarm`, `how` เรียกหลายโมเดลหรือ subagent พร้อมกัน จึงใช้ token มากกว่าปกติ ควรใช้กับงานที่คุ้ม
- **ความเป็นส่วนตัว:** pstack ไม่มี server และไม่มี telemetry แต่สิ่งที่สกิลสั่งให้ agent อ่าน เช่น transcript จะถูกส่งไปที่ผู้ให้บริการโมเดลของคุณ เครื่องมือ PR ใช้การล็อกอิน GitHub CLI (`gh`) ของคุณ
- **งานเล็ก:** แก้ไฟล์เดียวที่รู้ทางแก้ชัดเจน หรือแค่ถามคำถาม ไม่ต้องผ่าน poteto-mode ให้สั่ง agent ทำตรง ๆ ได้
- **ลำดับความสำคัญ:** คำสั่งของคุณใน CLAUDE.md, AGENTS.md หรือที่พิมพ์ตรง ๆ มาก่อนกฎของ pstack เสมอ

---

## 7. อ้างอิง

- ภาพรวม: `README.md`
- รายการสกิลและ slash command: `docs/reference.md`
- รายละเอียด playbook: `plugins/pstack/skills/poteto-mode/SKILL.md`
- ศัพท์ที่ใช้ในโปรเจกต์: `CONTEXT.md`
- ต้นฉบับ: https://github.com/michael-denyer/pstack-claude
