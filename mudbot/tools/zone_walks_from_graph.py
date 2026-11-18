"""Спидволки до ВСЕХ зон из графа rooms (без игры и без команды `путь`).

Клетка входа зоны Z = комната вне Z, из которой есть выход в комнату Z (и она ближе всего к площади города).
Хабы (rest room): р1 Элендор 100009, р2 Геолант 115039, р3 Фелонад 198005, р4 Огис 180096 (центральные площади).
Пишет в speedwalks (БД) и speedwalks.txt: <хаб>-<Зона>_область и <Зона>_область-<хаб> (обратно).
  python tools/zone_walks_from_graph.py            все зоны
  python tools/zone_walks_from_graph.py "Дом с привидениями" ...
"""
import json
import os
import sqlite3
import sys
from collections import deque

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
import zone_entrances as ze

HUBS = {"элен_цп": "100009", "гео_цп": "115039", "фело_цп": "198005", "огис_цп": "180096"}


def load():
    zone, g = {}, {}
    for v, z, ex in sqlite3.connect(ze.zs.DB).execute("select vnum,zone,exits from rooms"):
        zone[v] = z
        try:
            g[v] = json.loads(ex)
        except Exception:
            g[v] = {}
    return zone, g


def dist_from(g, a):
    prev = {a: None}
    q = deque([a])
    while q:
        v = q.popleft()
        for d, n in g.get(v, {}).items():
            if n not in prev:
                prev[n] = (v, d)
                q.append(n)
    return prev


def path(prev, b):
    out = []
    while prev[b]:
        v, d = prev[b]
        out.append(d)
        b = v
    return out[::-1]


def main(only):
    zone, g = load()
    prevs = {h: dist_from(g, v) for h, v in HUBS.items()}
    best = {}            # зона -> (длина, хаб, клетка входа, направление, путь)
    for a, ex in g.items():
        for d, b in ex.items():
            za, zb = zone.get(a), zone.get(b)
            if not zb or za == zb or (only and zb not in only):
                continue
            for h, pv in prevs.items():
                if a in pv:
                    p = path(pv, a)
                    if zb not in best or len(p) < best[zb][0]:
                        best[zb] = (len(p), h, a, d, p)
    for z, (n, h, a, d, p) in sorted(best.items(), key=lambda x: x[1][0]):
        back = [ze.OPP[x] for x in reversed(p)]
        zn = z.replace(" ", "_")
        ze.save(f"{h}-{zn}_область", ze.compress(p), a, f"клетка создания области «{z}»: {zone[a]} / {g and a}; выход в зону: {d}; из графа rooms")
        ze.save(f"{zn}_область-{h}", ze.compress(back), HUBS[h], f"обратно к площади ({h})")
        print(f"{z}: {h} {ze.compress(p)} ({n}) вход {a} [{zone[a]}] напр {d} | обратно {ze.compress(back)}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
