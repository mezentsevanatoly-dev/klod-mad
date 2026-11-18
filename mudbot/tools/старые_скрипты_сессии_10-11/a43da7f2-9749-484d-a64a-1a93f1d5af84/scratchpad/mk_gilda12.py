import json, collections, sqlite3
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
lines = [".триг #scr botCore.BotInZone = false"]
lines += [m for _, m in bfs("115092", "115061")]                    # склад р2 -> стойла Геоланта
lines += [".триг ехать стэдвик"]
lines += vl(bfs("12172", "12163"))                                  # загон Стэдвика -> Дом яростного бойца
lines += [".триг куп 1", ".триг изуч дощ", ".триг уч доп 30", ".триг уч атак 10", ".триг уч дуби 20"]
lines += vl(bfs("12163", "12172"))                                  # обратно в загон
lines += [".триг ехать гео"]
lines += vl(bfs("115061", "115092"))                                # стойла Геоланта -> склад р2
open(r"C:\Users\User\Desktop\Тадия\areas\гильда12.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
hdr = '"Имя моба";"Описание в комнате";"Hp";"MaxHp";"Mp";"MaxMp";"Опыт";"Деньги";"Уровень";"Агрессивность";"Ассистит?";"Умения";"Профессия";"Раса";"Флаги NPC"\r\n'
open(r"C:\Users\User\Desktop\Тадия\areas\гильда12_mob.csv", "wb").write(hdr.encode("cp1251"))
print("строк:", len(lines), "| путь в Стэдвике:", len(bfs("12172", "12163")), "ходов")
