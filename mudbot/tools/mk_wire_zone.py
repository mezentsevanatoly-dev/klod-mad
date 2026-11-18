# -*- coding: utf-8 -*-
"""Подключает готовый V-маршрут зоны (старт в городе Геолант) к кругу Айлины: склад р2 (115092) -> старт маршрута (BFS по game.db) + тело маршрута
+ возврат (BFS от клетки конца) на склад. Пишет areas Айлины <имя>.botp и <имя>_mob.csv (cp1251). Исходники НЕ меняет.
  python -X utf8 tools/mk_wire_zone.py <имя> <src.botp> <src_mob.csv>"""
import os, re, sys, json, sqlite3, collections, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
AREAS = os.path.join(BASE, "JMC БОТ АЙЛИНА", "areas")
HOME = "115092"
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
c = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
G = {}
for v, e in c.execute("select vnum,exits from rooms"):
    try:
        G[str(v)] = {d: str(t) for d, t in json.loads(e or "{}").items()}
    except Exception:
        G[str(v)] = {}


def bfs(src, dst):
    prev = {src: None}; q = collections.deque([src])
    while q:
        v = q.popleft()
        if v == dst:
            break
        for d, t in G.get(v, {}).items():
            if t not in prev:
                prev[t] = (v, d); q.append(t)
    if dst not in prev:
        raise SystemExit("нет пути %s -> %s" % (src, dst))
    out = []; v = dst
    while prev[v]:
        p, d = prev[v]; out.append((p, RU[d])); v = p
    out.reverse()
    return out


def vline(vn, cmd):
    return "#if {$MsdpRoomVnum != %s} {#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить};#if {$MsdpRoomVnum == %s} {%s}" % (vn, vn, cmd)


name, src, mob = sys.argv[1], sys.argv[2], sys.argv[3]
body = open(src, "rb").read().decode("cp1251").splitlines()
body = [x for x in body if x.strip()]
first = re.search(r"== (\d+)\}", body[0])
if not first:
    raise SystemExit("первая строка не V")
start = first.group(1)
last = None
for x in reversed(body):
    m = re.search(r"== (\d+)\} \{([^}]*)\}\s*$", x)
    if m:
        last = m; break
lvn, lcmd = last.group(1), last.group(2).strip()
DIR = {"север": "N", "юг": "S", "запад": "W", "восток": "E", "вверх": "U", "вниз": "D"}
end = G.get(lvn, {}).get(DIR.get(lcmd, ""), lvn)
pre = bfs(HOME, start) if start != HOME else []
post = bfs(end, HOME) if end != HOME else []
lines = [".триг #scr botCore.BotInZone = false"] + [vline(v, d) for v, d in pre] + [x for x in body if not x.startswith(".триг #scr botCore.BotInZone = false") or True] + [vline(v, d) for v, d in post] + [".триг #scr botCore.BotInZone = false"]
os.makedirs(AREAS, exist_ok=True)
dst = os.path.join(AREAS, name + ".botp")
if os.path.exists(dst):
    shutil.copy(dst, dst + ".bak_wire")
open(dst, "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251", "replace"))
shutil.copy(mob, os.path.join(AREAS, name + "_mob.csv"))
print(name, ": старт", start, "(склад->старт шагов %d), конец тела %s -> %s (назад шагов %d), всего строк %d" % (len(pre), lvn, end, len(post), len(lines)))
