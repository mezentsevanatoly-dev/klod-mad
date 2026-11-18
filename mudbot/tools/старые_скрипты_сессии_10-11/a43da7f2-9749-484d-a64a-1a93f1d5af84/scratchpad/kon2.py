import json, re, sqlite3, collections, shutil
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
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
    out = []; v = b
    while p.get(v): pv, d = p[v]; out.append((pv, RU[d])); v = pv
    return out[::-1]
g = open(r"C:\Users\User\Desktop\Тадия\areas\гильда15.botp", "rb").read().decode("cp1251").split("\r\n")
g = [x for x in g if x != ""]
i1 = next(i for i, x in enumerate(g) if "ехать стэдвик" in x)
i2 = next(i for i, x in enumerate(g) if "ехать гео" in x)
head = g[:i1 + 2]; head[i1] = head[i1].replace("ехать стэдвик", "ехать огис")
tail = g[i2 + 2:]
sim = json.load(open(S + r"\sim_огис_конюшни.json", encoding="utf-8"))
# sim[0] = (180025,'запад') входит в конюшни; ей предшествует создание области
cells = sim
appr = bfs("180154", "180025")
zone = [V.format(v=v, c=m) if not m.startswith(".") else ".триг " + V.format(v=v, c=m[1:]) for v, m in cells]
# выход: последняя клетка -> 181001 -> 'восток' -> 180025 -> 180154
last = cells[-1][0]; lastnext = str(R[last].get({"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}[cells[-1][1]]))
back = bfs("181001", "180154")
mid = [".триг #scr botCore.BotInZone = false"] + [V.format(v=v, c=m) for v, m in appr] + [".триг обл с запа"] + zone + [".триг #scr botCore.BotInZone = false"] + [V.format(v=v, c=m) for v, m in back]
mid.append(g[i2].replace("12172", "180154"))
lines = head + mid + [g[i2 + 1]] + tail
open(r"C:\Users\User\Desktop\Тадия\areas\конюшни.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("строк", len(lines), "подход", len(appr), "зона", len(zone), "первый шаг зоны", cells[0], "последний", cells[-1], lastnext)
print(g[i1][:120]); print(g[i2][:140]); print(g[i2+1])
