w = r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc_watch.py"
t = open(w, encoding="utf-8-sig").read().replace("\r\n", "\n")
a = "        k = KILL.match(body)\n"
assert t.count(a) == 1
t = t.replace(a, "        if \"Вы присели и дали отдохнуть\" in body:      # бот отдыхает (мало мувов): паузу не считаем застоем\n            self.paused_until = max(self.paused_until, time.time() + 40)\n            self.last_progress = time.time()\n" + a)
open(w, "w", encoding="utf-8", newline="\n").write(t)
import ast; ast.parse(t); print("ok")
