import json, collections, sqlite3, shutil, re
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
    assert v == a, (a, b)
    return out[::-1]
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
vl = lambda path: [V.format(v=v, c=m) for v, m in path]
REC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\каналгео1"
P = json.load(open(REC + r"\raw_path.json", encoding="utf-8"))
ends = [i for i, (v, m) in enumerate(P) if i > 0 and str(R[v][INV[m]]) == "115042"]
cut = P[: ends[-1] + 1]
Z = {v for v in R if v.startswith("226")}
seen = {v for v, _ in cut}
print("ходов зоны:", len(cut), "| первый:", cut[0], "| последний:", cut[-1], "| клеток 226xxx в БД:", len(Z), "| посещено:", len(seen & Z))
appr = bfs("115092", "115042")
lines = [".триг #scr botCore.BotInZone = false"] + vl(appr) + [".триг обл с вн"] + vl(cut) + vl(bfs("115042", "115092"))
open(r"C:\Users\User\Desktop\Тадия\areas\каты1.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("botp строк:", len(lines), "| подход:", len(appr), "| индекс обл:", 1 + len(appr))
