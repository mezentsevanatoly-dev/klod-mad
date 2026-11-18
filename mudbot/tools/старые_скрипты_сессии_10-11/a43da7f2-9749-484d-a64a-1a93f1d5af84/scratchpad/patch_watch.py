p = r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc_watch.py"
s = open(p, encoding="utf-8-sig").read().replace("\r\n", "\n")

def rep(a, b):
    global s
    assert s.count(a) == 1, a
    s = s.replace(a, b)

rep("def add_event(typ, text, ctx=None):\n", "QUIET = False\n\n\ndef add_event(typ, text, ctx=None):\n    if QUIET:\n        return None\n")
rep("        self.pos = os.path.getsize(LOG) if os.path.exists(LOG) else 0\n", "        self.pos = 0\n")
rep("        self.first_vn = None\n\n    def feed(self):",
    "        self.first_vn = None\n"
    "        # восстановить состояние бота по хвосту лога (без событий)\n"
    "        global QUIET\n"
    "        if os.path.exists(LOG):\n"
    "            self.pos = max(0, os.path.getsize(LOG) - 400000)\n"
    "            QUIET = True\n"
    "            try:\n"
    "                self.feed(skip_first=True)\n"
    "            finally:\n"
    "                QUIET = False\n"
    "            self.last_progress = self.last_line = time.time()\n\n"
    "    def feed(self, skip_first=False):")
rep("        for raw in data[:cut].decode(\"cp1251\", errors=\"replace\").replace(\"\\r\", \"\").split(\"\\n\"):\n            self.line(raw)",
    "        rows = data[:cut].decode(\"cp1251\", errors=\"replace\").replace(\"\\r\", \"\").split(\"\\n\")\n"
    "        if skip_first:\n            rows = rows[1:]\n"
    "        for raw in rows:\n            self.line(raw)")
open(p, "w", encoding="utf-8", newline="\n").write(s)
import ast; ast.parse(s); print("ok")
