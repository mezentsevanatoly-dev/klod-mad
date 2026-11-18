# -*- coding: utf-8 -*-
"""Плоский маршрут .botp -> V-маршрут симуляцией по графу game.db (старт = вход склада). Использование: python v_sim.py зона старт_vnum"""
import sys, os, re, json, sqlite3
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AREAS = os.path.join(os.path.dirname(ROOT), "JMC БОТ ИНКА", "areas")
zone, start = sys.argv[1], sys.argv[2]
c = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
g = {}
for v, e in c.execute("select vnum,exits from rooms"):
    try: g[str(v)] = {d: str(t) for d, t in json.loads(e).items()}
    except Exception: pass
RU = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
p = os.path.join(AREAS, zone + ".botp")
lines = open(p, encoding="cp1251").read().splitlines()
cur = start; out = []; bad = 0
for i, l in enumerate(lines):
    if l.strip() in RU:
        d = RU[l.strip()]
        nxt = g.get(cur, {}).get(d)
        if not nxt:
            print("ОБРЫВ на строке", i, "комната", cur, "ход", l); bad += 1; out.append(l); continue
        out.append('#if {$MsdpRoomVnum != %s} {#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить};#if {$MsdpRoomVnum == %s} {%s}' % (cur, cur, l.strip()))
        cur = nxt
    else:
        out.append(l)
print("строк", len(lines), "обрывов", bad, "финал", cur)
if bad == 0 and "--write" in sys.argv:
    import shutil; shutil.copy(p, p + ".bak_flat")
    open(p, "w", encoding="cp1251", newline="").write("\r\n".join(out) + "\r\n"); print("записано")