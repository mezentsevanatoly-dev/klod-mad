import sys, subprocess, time, re
step = int(sys.argv[1]); name = sys.argv[2] if len(sys.argv) > 2 else "гоблины"
p = r"C:\Users\User\Desktop\Тадия\areas\%s.botp" % name
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
print("удаляю шаг %d: %r (соседи %r | %r)" % (step, L[step], L[step - 1], L[step + 1]))
del L[step]
open(p, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
J = ["python", "-X", "utf8", r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc.py", "do", "--force"]
for x in ["#scr botCore.enableBot=false", "#scr botCore.loadZone('%s')" % name, "#scr seekstep=%d" % step, "#scr botCore.BotInZone=true", "#scr botCore.enableBot=true", "look краткий"]:
    subprocess.run(J + [x], stdout=subprocess.DEVNULL); time.sleep(2)
