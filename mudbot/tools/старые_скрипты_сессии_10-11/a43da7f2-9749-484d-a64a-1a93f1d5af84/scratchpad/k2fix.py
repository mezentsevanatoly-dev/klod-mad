import subprocess, time
p = r"C:\Users\User\Desktop\Тадия\areas\каты2.botp"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
assert L[11].startswith(".триг обл с вн") and "226001" in L[12]
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
L.insert(12, V.format(v="115042", c="вниз"))
open(p, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
J = ["python", "-X", "utf8", r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc.py", "do", "--force"]
for x in ["#scr botCore.enableBot=false", "#scr botCore.loadZone('каты2')", "#scr seekstep=12", "#scr botCore.BotInZone=true", "#scr botCore.enableBot=true", "look краткий"]:
    subprocess.run(J + [x], stdout=subprocess.DEVNULL); time.sleep(2)
print("ok")
