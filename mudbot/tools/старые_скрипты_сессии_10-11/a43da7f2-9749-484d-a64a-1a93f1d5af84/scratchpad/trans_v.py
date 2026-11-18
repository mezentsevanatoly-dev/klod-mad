import json, sqlite3, collections, shutil
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
def bfs(a, b):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R: p[t] = (v, d); q.append(t)
    assert b in p, (a, b)
    out = []; v = b
    while p.get(v): pv, d = p[v]; out.append((pv, RU[d])); v = pv
    return out[::-1]
A = r"C:\Users\User\Desktop\Тадия\areas\%s.botp"
tail = [".триг кз :колбы прозр", ".триг кз :колбы насыщ"]
# р2: Элендор склад -> Геолант холл 115050 (рерент) -> склад
p2 = bfs("100076", "115050")
L2 = [".триг #scr botCore.BotInZone = false"] + [V.format(v=v, c=m) for v, m in p2] + [".триг рерент"] + [V.format(v="115050", c="вверх"), V.format(v="115089", c="восток")] + tail
shutil.copyfile(A % "переход_р2", A % "переход_р2" + ".bak_plainv")
open(A % "переход_р2", "wb").write(("\r\n".join(L2) + "\r\n").encode("cp1251"))
print("р2", len(p2), len(L2))
# р1: Геолант склад -> Элендор склад
p1 = bfs("115092", "100076")
L1 = [".триг #scr botCore.BotInZone = false"] + [V.format(v=v, c=m) for v, m in p1] + tail
shutil.copyfile(A % "переход_р1", A % "переход_р1" + ".bak_plainv")
open(A % "переход_р1", "wb").write(("\r\n".join(L1) + "\r\n").encode("cp1251"))
print("р1", len(p1), len(L1))
