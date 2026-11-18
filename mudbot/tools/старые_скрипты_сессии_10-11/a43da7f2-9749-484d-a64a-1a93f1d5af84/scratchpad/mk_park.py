import sqlite3, json, collections, shutil
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {r[0]: json.loads(r[1] or "{}") for r in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}

def bfs(a, b):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R:
                p[t] = (v, d); q.append(t)
    out = []; v = b
    while p.get(v):
        pv, d = p[v]; out.append(RU[d]); v = pv
    assert v == a, (a, b)
    return out[::-1]

SRC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\парк"
T = r"C:\Users\User\Desktop\Тадия\areas"
V = [x for x in open(SRC + r"\рр_паркV.botp", "rb").read().decode("cp1251").splitlines() if x.strip()]
lines = [".триг #scr botCore.BotInZone = false"] + bfs("100076", "100009") + V + bfs("100009", "100076")
open(T + r"\парк.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
shutil.copyfile(SRC + r"\рр_паркV_mob.csv", T + r"\парк_mob.csv")
print(len(lines), "строк; префикс", bfs("100076", "100009"), "суффикс", bfs("100009", "100076"))
