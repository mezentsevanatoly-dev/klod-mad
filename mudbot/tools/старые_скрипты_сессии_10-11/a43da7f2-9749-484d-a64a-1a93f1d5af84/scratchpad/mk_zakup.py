import json, collections, sqlite3, re
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
N = {str(v): (z, n) for v, z, n in c.execute("select vnum,zone,name from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
D = {"N": "n", "S": "s", "E": "e", "W": "w", "U": "u", "D": "d"}
def bfs(a, b):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R: p[t] = (v, d); q.append(t)
    if b not in p: raise SystemExit("нет пути %s -> %s" % (a, b))
    out = []; v = b
    while p[v]: pv, d = p[v]; out.append((pv, RU[d], D[d])); v = pv
    return out[::-1]
def comp(s): return re.sub(r"(.)\1+", lambda m: str(len(m.group(0))) + m.group(1), s)
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
vl = lambda path: [V.format(v=v, c=m) for v, m, _ in path]
vc = lambda vn, cmd: ".триг " + V.format(v=vn, c=cmd)
print("шатёр:", N.get("169042"))
a = bfs("100076", "100075"); b = bfs("100075", "169042"); d = bfs("169042", "100076")
print("склад->банк:", comp("".join(x[2] for x in a)), "| банк->шатёр:", comp("".join(x[2] for x in b)), len(b), "| шатёр->склад:", comp("".join(x[2] for x in d)), len(d))
lines = [".триг #scr botCore.BotInZone = false"] + vl(a) + [vc("100075", "снять 55555")] + vl(b)
lines += [vc("169042", "куп насыщ 10"), vc("169042", "куп насыщ 10")]
lines += vl(d)
lines += [vc("100076", "осуш насыщ"), vc("100076", "осуш насыщ"), vc("100076", "кс :колбы все.насыщ")]
open(r"C:\Users\User\Desktop\Тадия\areas\закупка_насыщ.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
hdr = '"Имя моба";"Описание в комнате";"Hp";"MaxHp";"Mp";"MaxMp";"Опыт";"Деньги";"Уровень";"Агрессивность";"Ассистит?";"Умения";"Профессия";"Раса";"Флаги NPC"\r\n'
open(r"C:\Users\User\Desktop\Тадия\areas\закупка_насыщ_mob.csv", "wb").write(hdr.encode("cp1251"))
print("строк:", len(lines))
# спидволки в speedwalks.txt
import os
sw = r"C:\Users\User\Desktop\Клод мад\mudbot\speedwalks.txt"
old = open(sw, encoding="utf-8").read().splitlines()
keep = [l for l in old if not l.startswith(("р1_склад-банк", "банк-шатёр", "шатёр-р1_склад"))]
keep += ["# закупка настоек: склад р1 -> банк -> шатёр -> склад р1", "р1_склад-банк = %s @ 100075" % comp("".join(x[2] for x in a)),
         "банк-шатёр = %s @ 169042" % comp("".join(x[2] for x in b)), "шатёр-р1_склад = %s @ 100076" % comp("".join(x[2] for x in d))]
open(sw, "w", encoding="utf-8").write("\n".join(keep) + "\n")
