"""Путь по картам MUD Mapper (data/world/*.json, без vnum) между комнатами разных зон: по названиям и направлениям.
python tools/mapper_path.py "Город Элендор" "Склад" "Заливные луга" "По краю болота"
Рёбра внутри зоны — по клеткам (x, y) и флагам links; между зонами — по полю to_zone «Зона|на север|id|».
Печатает команды (север/юг/...) и названия комнат по пути; проверять каждый шаг по названию комнаты из MSDP.
"""
import collections
import json
import os
import sys

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "world")
DIRS = {"N": (0, -1, "север"), "S": (0, 1, "юг"), "E": (1, 0, "восток"), "W": (-1, 0, "запад")}
RU = {"на север": "север", "на юг": "юг", "на восток": "восток", "на запад": "запад", "вверх": "вверх", "вниз": "вниз"}


def load(zone):
    return json.load(open(os.path.join(W, zone + ".json"), encoding="utf-8"))["rooms"]


OPP = {"N": "S", "S": "N", "E": "W", "W": "E"}


def orient(rooms):
    """Оси карты в .mm2 бывают обменяны/отражены: из 8 вариантов берём тот, где больше взаимных ссылок (A.N -> B, B.S -> A)."""
    by_xy = {(r["x"], r["y"], r.get("level", 0)): r for r in rooms}
    best, bs = None, -1
    for sw in (0, 1):
        for fx in (1, -1):
            for fy in (1, -1):
                score = 0
                for r in rooms:
                    for k, (dx, dy, _) in DIRS.items():
                        if r["links"].get(k):
                            if sw:
                                dx, dy = dy, dx
                            t = by_xy.get((r["x"] + dx * fx, r["y"] + dy * fy, r.get("level", 0)))
                            if t and t["links"].get(OPP[k]):
                                score += 1
                if score > bs:
                    best, bs = (sw, fx, fy), score
    return best


def graph(zones):
    nodes, edges = {}, collections.defaultdict(list)
    for z in zones:
        rooms = load(z)
        sw, fx, fy = orient(rooms)
        by_xy = {(r["x"], r["y"], r.get("level", 0)): r for r in rooms}
        for r in rooms:
            nodes[(z, r["id"])] = r["name"]
            for k, (dx, dy, ru) in DIRS.items():
                if r["links"].get(k):
                    if sw:
                        dx, dy = dy, dx
                    t = by_xy.get((r["x"] + dx * fx, r["y"] + dy * fy, r.get("level", 0)))
                    if t:
                        edges[(z, r["id"])].append(((z, t["id"]), ru))
            for tz in r.get("to_zone", []):
                zn, d, tid = (tz.split("|") + ["", ""])[:3]
                if zn in zones and tid.isdigit() and d in RU:
                    edges[(z, r["id"])].append(((zn, int(tid)), RU[d]))
    return nodes, edges


def find(nodes, zone, name):
    return [k for k, v in nodes.items() if k[0] == zone and v == name]


def bfs(edges, starts, goals):
    prev, q = {s: None for s in starts}, collections.deque(starts)
    while q:
        v = q.popleft()
        if v in goals:
            path = []
            while prev[v]:
                v, d = prev[v][0], prev[v][1]
                path.append(d)
                v = prev[v][0] if prev[v] else v
            return None
        for t, d in edges[v]:
            if t not in prev:
                prev[t] = (v, d)
                q.append(t)
    return prev


def route(zones, z1, n1, z2, n2, start_id=None):
    nodes, edges = graph(zones)
    starts, goals = find(nodes, z1, n1), set(find(nodes, z2, n2))
    if start_id is not None:
        starts = [s for s in starts if s[1] == start_id] or starts
    prev, q, hit = {s: None for s in starts}, collections.deque(starts), None
    while q:
        v = q.popleft()
        if v in goals:
            hit = v
            break
        for t, d in edges[v]:
            if t not in prev:
                prev[t] = (v, d)
                q.append(t)
    if not hit:
        return None
    path, v = [], hit
    while prev[v]:
        p, d = prev[v]
        path.append((d, nodes[v], v))
        v = p
    return nodes[v], v, path[::-1]


if __name__ == "__main__":
    z1, n1, z2, n2 = sys.argv[1:5]
    zones = sys.argv[5:] or sorted(f[:-5] for f in os.listdir(W) if f.endswith(".json") and not f.startswith("_"))
    res = route(zones, z1, n1, z2, n2)
    if not res:
        sys.exit("пути нет")
    start, sv, path = res
    print(f"старт: {start} {sv}")
    print(" ".join(d for d, _, _ in path))
    print(" | ".join(f"{d}:{n}" for d, n, _ in path))
