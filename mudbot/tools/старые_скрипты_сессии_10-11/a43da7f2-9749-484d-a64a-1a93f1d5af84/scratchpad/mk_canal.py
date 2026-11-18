import json, collections, sqlite3
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

REC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\канал"
T = r"C:\Users\User\Desktop\Тадия\areas"
Q = json.load(open(REC + r"\raw_path_cut.json", encoding="utf-8"))
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
lines = [".триг #scr botCore.BotInZone = false"] + bfs("100076", "100121") + [".триг обл с вн"] + [V.format(v=v, c=m) for v, m in Q] + bfs("100121", "100076")
open(T + r"\канал.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("botp строк:", len(lines), "| дорога туда:", bfs("100076", "100121"), "| обратно:", bfs("100121", "100076"))

rows = open(REC + r"\канал_mob_fixed.csv", "rb").read().decode("cp1251").split("\r\n")
orig = open(REC + r"\рр_каналV_mob.csv", "rb").read().decode("cp1251").split("\r\n")
out = [rows[0]]
for r in rows[1:]:
    if not r.strip(): continue
    if r.startswith('"Агрессивный мох";') and ("бросается" in r or "попытался" in r or "принялся" in r):
        continue                      # это боевые сообщения, не строка комнаты
    out.append(r)
mouse = next(r for r in orig if r.startswith('"Маленькая мышка";')).split(";")
mouse[1] = '"Мышка пробегает вдоль стены в поисках пищи. "'
out.append(";".join(mouse))
open(T + r"\канал_mob.csv", "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
print("csv строк:", len(out) - 1)
