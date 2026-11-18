import subprocess, time, re
p = r"C:\Users\User\Desktop\Тадия\areas\ель.botp"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
assert "== 132237} {запад}" in L[127] and "== 132235} {север}" in L[128]
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
L.insert(128, V.format(v="132236", c="запад"))
open(p, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
J = ["python", "-X", "utf8", r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc.py", "do", "--force"]
for x in ["#scr botCore.enableBot=false", "#scr botCore.loadZone('ель')", "#scr seekstep=128", "#scr botCore.BotInZone=true", "#scr botCore.enableBot=true", "look краткий"]:
    subprocess.run(J + [x], stdout=subprocess.DEVNULL); time.sleep(2)
print("ok")
