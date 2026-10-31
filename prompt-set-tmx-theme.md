ช่วยตั้ง theme แบบ hacker (ตัวอักษรเขียวบนพื้นดำ) ให้ทั้ง terminal และ tmux ใช้สีเดียวกัน

ขั้นตอน:
1. เช็คก่อนว่าใช้ terminal ตัวไหน (ถ้าอยู่ใน tmux ให้ดู `tmux show-environment -g TERM_PROGRAM`) แล้วเช็คว่ามี tmux และมี ~/.tmux.conf อยู่แล้วหรือไม่
   - ถ้ายังไม่มี tmux ให้ติดตั้งด้วย `brew install tmux`
   - ถ้ามี ~/.tmux.conf อยู่แล้ว ให้ backup เป็น ~/.tmux.conf.bak ก่อนเขียนทับ

2. ตั้งค่า terminal
   - ถ้าเป็น Terminal.app ให้จด profile ที่ใช้อยู่ตอนนี้ไว้ก่อน (เอาไว้ย้อนกลับ) แล้วรัน:
     defaults write com.apple.Terminal "Default Window Settings" -string "Homebrew"
     defaults write com.apple.Terminal "Startup Window Settings" -string "Homebrew"
     osascript -e 'tell application "Terminal" to set current settings of every tab of every window to settings set "Homebrew"'
   - ถ้าเป็นโปรแกรมอื่น (iTerm2, Ghostty, WezTerm, Alacritty) ให้ตั้ง background #000000, foreground #28FE14, cursor #38FE27 ในไฟล์ config ของโปรแกรมนั้น

3. เขียน ~/.tmux.conf ตามนี้:

# ── Hacker theme: green on black (matches Terminal.app "Homebrew" profile) ──
set -g default-terminal "tmux-256color"
set -g mouse on
set -g status-interval 5

# pane background / text
set -g window-style        'fg=colour34,bg=black'
set -g window-active-style 'fg=colour46,bg=black'

# pane borders
set -g pane-border-style        'fg=colour22'
set -g pane-active-border-style 'fg=colour46'

# status bar
set -g status-position bottom
set -g status-style 'bg=black,fg=colour46'
set -g status-left-length 30
set -g status-left  '#[fg=black,bg=colour46,bold] [#S] #[default] '
set -g status-right '#[fg=colour34]#(whoami)@#h #[fg=colour46,bold]%H:%M:%S '
set -g window-status-format         '#[fg=colour28] #I:#W '
set -g window-status-current-format '#[fg=black,bg=colour46,bold] #I:#W '
set -g window-status-separator ''

# messages, command prompt, copy mode
set -g message-style         'bg=black,fg=colour46,bold'
set -g message-command-style 'bg=black,fg=colour46'
set -g mode-style            'bg=colour46,fg=black'
set -g clock-mode-colour colour46

4. ถ้ามี tmux เปิดอยู่ ให้รัน `tmux source-file ~/.tmux.conf`

5. สรุปให้ฟังว่าเปลี่ยนอะไรไปบ้าง และบอกคำสั่งสำหรับย้อนกลับไปใช้ค่าเดิม

ถ้าเครื่องนั้นไม่มี Claude Code ก็ทำตามขั้นตอนในกล่องเองได้เลย ขั้นที่ 2 กับ 3 คือส่วนที่เปลี่ยนสีจริง