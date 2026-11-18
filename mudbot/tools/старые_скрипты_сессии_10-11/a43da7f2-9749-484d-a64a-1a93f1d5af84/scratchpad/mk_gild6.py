import sqlite3, json, collections
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

S, G = "100076", "100169"
lines = [".триг #scr botCore.BotInZone = false"]
lines += bfs(S, G)
lines += [".триг уч дуби 15", ".триг уч атак 10"]
lines += bfs(G, S)
T = r"C:\Users\User\Desktop\Тадия\areas"
open(T + r"\гильда6.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
hdr = '"Имя моба";"Описание в комнате";"Hp";"MaxHp";"Mp";"MaxMp";"Опыт";"Деньги";"Уровень";"Агрессивность";"Ассистит?";"Умения";"Профессия";"Раса";"Флаги NPC"\r\n'
open(T + r"\гильда6_mob.csv", "wb").write(hdr.encode("cp1251"))
print(len(lines), "строк:", " ".join(lines))
