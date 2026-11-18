import shutil
sp = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\AreaGuard.js"
T = r"C:\Users\User\Desktop\Тадия"
src = open(sp, encoding="utf-8").read().replace("\r\n", "\n").replace("\n", "\r\n")
open(T + r"\scripts\AreaGuard.js", "wb").write(src.encode("cp1251"))
p = T + r"\settings\дкаре.js"
shutil.copyfile(p, p + ".bak_ag")
s = open(p, "rb").read().decode("cp1251")
a = 'include("scripts/BotFix.js");'
assert s.count(a) == 1
if "AreaGuard" not in s:
    s = s.replace(a, a + '\r\ninclude("scripts/AreaGuard.js");     // область: проверка обл, удаление, ожидание таймера')
open(p, "wb").write(s.encode("cp1251"))

# watcher: AREA notes
w = r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc_watch.py"
t = open(w, encoding="utf-8-sig").read().replace("\r\n", "\n")
def rep(a, b):
    global t
    assert t.count(a) == 1, a
    t = t.replace(a, b)
rep("        self.last_progress = time.time()\n        self.last_line = time.time()\n        self.stall_flag = False\n        self.nolog_flag = False",
    "        self.last_progress = time.time()\n        self.last_line = time.time()\n        self.paused_until = 0\n        self.stall_flag = False\n        self.nolog_flag = False")
rep('            elif body.startswith("## MOVE_BLOCKED_BATTLE"):',
    '            elif body.startswith("## AREA"):\n'
    '                self.last_progress = time.time()\n'
    '                self.stall_flag = False\n'
    '                mm = re.search(r"AREA_WAIT secs=(\\d+)", body)\n'
    '                if mm:\n'
    '                    self.paused_until = time.time() + int(mm.group(1)) + 20\n'
    '                add_event("AREA", body[3:], self.ctx(4))\n'
    '            elif body.startswith("## MOVE_BLOCKED_BATTLE"):')
rep("        if self.bot_on and not self.stall_flag and t - self.last_progress > STALL_SEC:",
    "        paused = t < self.paused_until\n        if self.bot_on and not paused and not self.stall_flag and t - self.last_progress > STALL_SEC:")
rep("        if self.bot_on and not self.nolog_flag and t - self.last_line > NOLOG_SEC:", "        if self.bot_on and not paused and not self.nolog_flag and t - self.last_line > NOLOG_SEC:")
rep("        if self.bot_on and not self.nolog_event and t - self.last_line > NOLOG_EVENT_SEC:", "        if self.bot_on and not paused and not self.nolog_event and t - self.last_line > NOLOG_EVENT_SEC:")
rep('("SAY", "BOT_START", "BATTLE_BLOCK")', '("SAY", "BOT_START", "BATTLE_BLOCK", "AREA")')
open(w, "w", encoding="utf-8", newline="\n").write(t)
import ast; ast.parse(t)
print("ok")
