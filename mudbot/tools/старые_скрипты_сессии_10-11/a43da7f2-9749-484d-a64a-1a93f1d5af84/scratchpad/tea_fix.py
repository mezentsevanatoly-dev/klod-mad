import subprocess, time
p = r"C:\Users\User\Desktop\Тадия\areas\чайный_домик.botp"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
assert "отпер две" in L[37] and "откр две" in L[38] and "131019} {север}" in L[36]
d1 = L[37].replace("131026", "131019"); d2 = L[38].replace("131026", "131019")
L[36:39] = [d1, d2, L[36]]
open(p, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
J = ["python", "-X", "utf8", r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc.py", "do", "--force"]
for x in ["#scr botCore.enableBot=false", "#scr botCore.loadZone('чайный_домик')", "#scr seekstep=36", "#scr botCore.BotInZone=true", "#scr botCore.enableBot=true", "look краткий"]:
    subprocess.run(J + [x], stdout=subprocess.DEVNULL); time.sleep(2)
print("ok")
