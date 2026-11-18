import json, collections, sqlite3, re
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
            if t not in p and t in R: p[t] = (v, d); q.append(t)
    out = []; v = b
    while p.get(v): pv, d = p[v]; out.append((pv, RU[d])); v = pv
    assert v == a, (a, b)
    return out[::-1]
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
vl = lambda path: [V.format(v=v, c=m) for v, m in path]
vc = lambda vn, cmd: ".триг " + V.format(v=vn, c=cmd)
REC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\огис_лечеб"
zone = [l.rstrip("\n") for l in open(REC + r"\raw_moves.txt", encoding="utf-8") if l.strip()]
lines = [".триг #scr botCore.BotInZone = false"]
lines += vl(bfs("115092", "115061"))
lines += [vc("115061", "ехать огис"), ".пауза 80"]
lines += vl(bfs("180154", "180048"))
idx_area = len(lines)
lines += [".триг обл с с"]
lines += zone
lines += vl(bfs("180048", "180154"))
lines += [vc("180154", "ехать гео"), ".пауза 80"]
lines += vl(bfs("115061", "115092"))
open(r"C:\Users\User\Desktop\Тадия\areas\леч.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("строк:", len(lines), "| индекс обл:", idx_area, "| зона:", len(zone))
# csv: только животные (без людей)
rows = open(REC + r"\леч_mob_fixed.csv", "rb").read().decode("cp1251").split("\r\n")
out = [rows[0]]
drop = []
for r in rows[1:]:
    if not r.strip(): continue
    nm = r.split(";")[0].strip('"')
    k = c.execute("select kind from mob_cards where name=? and zone like '%Лечебн%'", (nm,)).fetchone()
    if k and k[0] == "человека":
        drop.append(nm); continue
    out.append(r)
open(r"C:\Users\User\Desktop\Тадия\areas\леч_mob.csv", "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
print("csv строк:", len(out) - 1, "| людей убрано:", drop)
q = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(q, "rb").read().decode("cp1251")
a = "/Громилы/, "
assert s.count(a) == 1
s = s.replace(a, a + "/Голубятня/, /^Палата$/, /^ограда\\.$/, /утварью\\./, ")
open(q, "wb").write(s.encode("cp1251"))
g = r"C:\Users\User\Desktop\Тадия\scripts\AreaGuard.js"
t = open(g, "rb").read().decode("cp1251")
if '"леч"' not in t:
    t = t.replace('"привы1": "Дом с привидениями"}', '"привы1": "Дом с привидениями", "леч": "Лечебница для животных"}').replace('"привы1": 1}', '"привы1": 1, "леч": 1}')
    open(g, "wb").write(t.encode("cp1251"))
print("ok")
