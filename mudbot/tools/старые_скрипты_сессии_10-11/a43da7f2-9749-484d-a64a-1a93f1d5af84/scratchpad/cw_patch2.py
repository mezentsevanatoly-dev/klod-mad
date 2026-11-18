p = r"C:\Users\User\Desktop\Клод мад\mudbot\tools\chainwatch.py"
s = open(p, encoding="utf-8").read()
if "pnp_release" not in s:
    s = s.replace('''    buf += chunk
''', '''    buf += chunk
    if "Вы усердно помолились" in chunk:     # pnp_release: ложная проверка на присутствие -> снимаем паузу
        time.sleep(3)
        for x in ["#scr botCore.waitFlag=false", "#scr wTimerCount=0", "#scr jmc.killTimer(100)", "look краткий"]:
            subprocess.run(J + [x], stdout=subprocess.DEVNULL); time.sleep(1)
        note("ПнП-пауза снята (молитва)")
''', 1)
open(p, "w", encoding="utf-8").write(s)
import ast; ast.parse(s); print("ok")
