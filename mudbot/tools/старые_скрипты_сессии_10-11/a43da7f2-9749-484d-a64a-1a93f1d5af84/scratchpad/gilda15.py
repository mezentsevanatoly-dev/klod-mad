T = r"C:\Users\User\Desktop\Тадия\areas"
L = open(T + r"\гильда12.botp", "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
idx = [i for i, l in enumerate(L) if l.endswith("{куп 1}") or l.endswith("{изуч дощ}") or l.endswith("{уч доп 30}") or l.endswith("{уч атак 10}") or l.endswith("{уч дуби 20}")]
assert len(idx) == 5, idx
new = [".триг " + V.format(v="12163", c=c) for c in ("уч атак 21", "уч доп 20", "уч дуби 30")]
L[idx[0]:idx[-1] + 1] = new
open(T + r"\гильда15.botp", "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
import shutil; shutil.copyfile(T + r"\гильда12_mob.csv", T + r"\гильда15_mob.csv")
print("гильда15 строк:", len(L))
