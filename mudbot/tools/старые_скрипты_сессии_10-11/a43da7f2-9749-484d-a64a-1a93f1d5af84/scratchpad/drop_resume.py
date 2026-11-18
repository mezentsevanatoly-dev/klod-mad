import sys, subprocess, time, re
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
step = int(sys.argv[1])          # шаг бота, на котором команда не прошла
k = step - 17
cmds = open(S + r"\port_cmds.txt", encoding="utf-8").read().split("\n")
print("удаляю k=%d: %s (соседи %s | %s)" % (k, cmds[k], cmds[k - 1], cmds[k + 1]))
del cmds[k]
open(S + r"\port_cmds.txt", "w", encoding="utf-8", newline="").write("\n".join(cmds))
subprocess.run(["python", "-X", "utf8", S + r"\mk_port3.py"], check=True)
J = ["python", "-X", "utf8", r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc.py", "do", "--force"]
for x in ["#scr botCore.enableBot=false", "#scr botCore.loadZone('порт')", "#scr seekstep=%d" % step, "#scr botCore.BotInZone=true", "#scr botCore.enableBot=true", "look краткий"]:
    subprocess.run(J + [x], stdout=subprocess.DEVNULL); time.sleep(2)
