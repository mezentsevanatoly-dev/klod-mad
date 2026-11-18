import json, sqlite3, collections, shutil
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
def bfs(a, b):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R and t.startswith("114"): p[t] = (v, d); q.append(t)
    out = []; v = b
    while p.get(v): pv, d = p[v]; out.append((pv, RU[d])); v = pv
    assert v == a; return out[::-1]
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
p = r"C:\Users\User\Desktop\Тадия\areas\склад2.botp"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
i = next(k for k, x in enumerate(L) if x == ".триг #scr botCore.BotInZone = false" and k > 60)
path = bfs("114036", "114003") + [("114003", "запад")]
print(path)
shutil.copyfile(p, p + ".bak_exit")
L[i:i] = [V.format(v=v, c=m) for v, m in path]
open(p, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
print("вставлено", len(path), "в", i)
