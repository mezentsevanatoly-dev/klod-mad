import json, collections, sqlite3, shutil
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
INV = {v: k for k, v in RU.items()}
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
def bfs(a, b, pref=None):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R and (pref is None or t.startswith(pref) or t == b): p[t] = (v, d); q.append(t)
    assert b in p, (a, b)
    out = []; v = b
    while p.get(v): pv, d = p[v]; out.append((pv, RU[d])); v = pv
    return out[::-1]
zone = json.load(open(S + r"\k2_v.json", encoding="utf-8"))
zone = [z for z in zone if not z.startswith(".пауза 8") or True]
# последний ход зоны: 'вверх' из 226028 -> ?
last = zone[-1]; import re
m = re.search(r"== (\d+)\} \{([^}]*)\}$", last)
cell, mv = m.group(1), m.group(2)
nxt = str(R.get(cell, {}).get(INV[mv], "226025"))
print("после последнего хода:", cell, mv, "->", nxt)
appr = bfs("115092", "115042")
back = bfs(nxt, "226001", "226")
home = bfs("115042", "115092")
lines = [".триг #scr botCore.BotInZone = false"] + [V.format(v=v, c=m) for v, m in appr] + [".триг обл с вн"] + zone + [V.format(v=v, c=m) for v, m in back] + [V.format(v="226001", c="вверх")] + [".триг #scr botCore.BotInZone = false"] + [V.format(v=v, c=m) for v, m in home]
p = r"C:\Users\User\Desktop\Тадия\areas\каты2.botp"
shutil.copyfile(p, p + ".bak_old")
open(p, "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("каты2.botp строк", len(lines), "подход", len(appr), "зона", len(zone), "назад", len(back), "домой", len(home))
