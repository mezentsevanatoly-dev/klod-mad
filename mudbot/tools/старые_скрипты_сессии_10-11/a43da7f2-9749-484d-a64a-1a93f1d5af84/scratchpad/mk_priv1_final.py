import json, collections, sqlite3, shutil
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
N = {str(v): n for v, n in c.execute("select vnum,name from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
OPP = {"север": "юг", "юг": "север", "восток": "запад", "запад": "восток", "вверх": "вниз", "вниз": "вверх"}

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
    assert v == a, (a, b)
    return out[::-1]

P = json.load(open(r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\привы1\raw_path.json", encoding="utf-8"))
ends = [i for i, (v, m) in enumerate(P) if i > 0 and str(R[v][{x: k for k, x in RU.items()}[m]]) == "122011"]
cut = P[: ends[-1] + 1]
zone = [(v, m) for v, m in cut]
seen = {v for v, _ in zone}
Z = {v for v in R if v.startswith("135")}
print("ходов зоны:", len(zone), "| клеток 135xxx в БД:", len(Z), "| посещено:", len(seen & Z))
appr = bfs("115092", "122011")
print("подход от склада р2 до 122011:", len(appr), "ходов:", [m for _, m in appr])
back = bfs("122011", "115092")
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
lines = [".триг #scr botCore.BotInZone = false"] + [m for _, m in appr] + [".триг обл с в"] + [V.format(v=v, c=m) for v, m in zone] + [m for _, m in back]
T = r"C:\Users\User\Desktop\Тадия\areas\привы1.botp"
shutil.copyfile(T, T + ".bak_final")
open(T, "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("botp строк:", len(lines), "| индекс обл:", 1 + len(appr), "| первый V-ход:", zone[0], "| последний:", zone[-1])
