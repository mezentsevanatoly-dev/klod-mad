import shutil
p = r"C:\Users\User\Desktop\Тадия\areas\привы2.botp"
shutil.copyfile(p, p + ".bak_door")
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
assert "135028} {юг}" in L[46], L[46][-60:]
L[46:46] = [".триг " + V.format(v="135028", c="отпер две юг"), ".триг " + V.format(v="135028", c="откр две юг")]
open(p, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
print("ok", len(L))
