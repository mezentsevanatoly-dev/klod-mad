import json, sqlite3, collections, shutil
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
INV = {v: k for k, v in RU.items()}
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
cmds = open(S + r"\port_cmds.txt", encoding="utf-8").read().split("\n")
cur = "100053"; zone = []; bad = []
for k, x in enumerate(cmds):
    if x.startswith(("отпер", "откр")): zone.append((cur, "." + x)); continue
    t = R.get(cur, {}).get(INV[x])
    if t is None: bad.append((k, cur, x)); continue
    zone.append((cur, x)); cur = str(t)
print("конец:", cur, "пропущено:", bad)
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
vl = lambda p: [(".триг " + V.format(v=v, c=m[1:])) if m.startswith(".") else V.format(v=v, c=m) for v, m in p]
lines = [".триг #scr botCore.BotInZone = false"] + vl(bfs("100076", "100053")) + [".триг #scr botCore.BotInZone = true"] + vl(zone) + [".триг #scr botCore.BotInZone = false"] + vl(bfs(cur, "100076"))
p = r"C:\Users\User\Desktop\Тадия\areas\порт.botp"
shutil.copyfile(p, p + ".bak_plain")
open(p, "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("строк", len(lines))
