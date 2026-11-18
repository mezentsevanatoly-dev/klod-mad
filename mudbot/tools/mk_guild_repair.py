# -*- coding: utf-8 -*-
"""Генератор зон гильда_уч и ремонт (р2, Геолант) в JMC БОТ ИНКА\areas: V-маршрут по графу data/game.db.
гильда_уч: склад р2 -> Военная гильдия (115066): уч доп 5; уч атак 5; уч дубин 10; трен тело -> склад.
ремонт: склад р2 -> Оружейный магазин (115016): чин все -> склад."""
import os, sqlite3, json, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BASE = os.path.dirname(ROOT)
AREAS = os.path.join(BASE, "JMC БОТ ИНКА", "areas")
c = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
g = {}
for v, e in c.execute("select vnum,exits from rooms"):
    try:
        g[str(v)] = {d: str(t) for d, t in json.loads(e).items()}
    except Exception:
        pass
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
START = "115092"
HEAD = '"Имя моба";"Описание в комнате";"Hp";"MaxHp";"Mp";"MaxMp";"Опыт";"Деньги";"Уровень";"Агрессивность";"Ассистит?";"Умения";"Профессия";"Раса";"Флаги NPC"'


def bfs(a, b):
    q = collections.deque([a]); prev = {a: None}
    while q:
        v = q.popleft()
        if v == b:
            break
        for d, t in g.get(v, {}).items():
            if t not in prev:
                prev[t] = (v, d); q.append(t)
    if b not in prev:
        return None
    path = []; v = b
    while prev[v]:
        p, d = prev[v]; path.append((p, d)); v = p
    return path[::-1]


def V(room, cmd):
    return '#if {$MsdpRoomVnum != %s} {#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить};#if {$MsdpRoomVnum == %s} {%s}' % (room, room, cmd)


def build(name, target, cmds):
    out = [".триг #scr botCore.BotInZone = false"]
    go = bfs(START, target); back = bfs(target, START)
    assert go and back, name
    out += [V(r, RU[d]) for r, d in go]
    out += [V(target, cm) for cm in cmds]
    out += [V(r, RU[d]) for r, d in back]
    with open(os.path.join(AREAS, name + ".botp"), "w", encoding="cp1251", newline="") as f:
        f.write("\r\n".join(out) + "\r\n")
    with open(os.path.join(AREAS, name + "_mob.csv"), "w", encoding="cp1251", newline="") as f:
        f.write(HEAD + "\r\n")
    print(name, "шагов туда", len(go), "обратно", len(back), "всего строк", len(out))


if __name__ == "__main__":
    build("гильда_уч", "115066", ["уч доп 5", "уч атак 5", "уч дубин 10", "трен тело"])
    build("ремонт", "115016", ["чин все"])

