p = r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc_watch.py"
s = open(p, encoding="utf-8-sig").read().replace("\r\n", "\n")
def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)
rep("STALL_SEC = 150", "STALL_SEC = 45")
rep("NOLOG_SEC = 10", "NOLOG_SEC = 10          # окно жёлтое\nNOLOG_EVENT_SEC = 30    # событие для Claude")
rep('("SAY", "BOT_START", "BATTLE_BLOCK", "NOLOG")', '("SAY", "BOT_START", "BATTLE_BLOCK")')
rep("        self.nolog_flag = False\n        self.start_time", "        self.nolog_flag = False\n        self.nolog_event = False\n        self.start_time")
rep("        self.nolog_flag = False\n        body = m.group(2)" if False else "        self.last_line = time.time()\n        self.nolog_flag = False\n", "        self.last_line = time.time()\n        self.nolog_flag = False\n        self.nolog_event = False\n")
rep("""        if self.bot_on and not self.nolog_flag and t - self.last_line > NOLOG_SEC:
            self.nolog_flag = True
            add_event("NOLOG", "в логе тишина %d с (связь/JMC?)" % (t - self.last_line), self.ctx(6))""",
"""        if self.bot_on and not self.nolog_flag and t - self.last_line > NOLOG_SEC:
            self.nolog_flag = True
        if self.bot_on and not self.nolog_event and t - self.last_line > NOLOG_EVENT_SEC:
            self.nolog_event = True
            add_event("NOLOG", "в логе тишина %d с (связь/JMC/бот встал?)" % (t - self.last_line), self.ctx(10))""")
open(p, "w", encoding="utf-8", newline="\n").write(s)
import ast; ast.parse(s); print("ok")
