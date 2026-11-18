"""Прогнать маршрут Чвырлы без номеров клеток (только команды) по карте MUD Mapper: из каких клеток какие vnum.

python tools/mm_sim.py <зона> <botp> <с_строки> <по_строку> <id_старта> [vnum_базы]
Карта data/world/<зона>.json: клетки id,x,y,level,links{N,S,E,W,U,D}. Сосед по выходу — клетка со смещением координат
(N: y-1, S: y+1, E: x+1, W: x-1; U/D — этаж ±1). Печатает путь vnum и ошибки (выход есть в links, а клетки нет и т.п.).
"""
import itertools
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RU = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
VEC = {"N": (0, -1, 0), "S": (0, 1, 0), "E": (1, 0, 0), "W": (-1, 0, 0), "U": (0, 0, 1), "D": (0, 0, -1)}


def load(zone):
    rooms = json.load(open(os.path.join(ROOT, "data", "world", zone + ".json"), encoding="utf-8"))["rooms"]
    by_pos = {(r["x"], r["y"], r["level"]): r for r in rooms}
    return {r["id"]: r for r in rooms}, by_pos


def neighbor(r, d, by_pos, flip):
    dx, dy, dz = VEC[d]
    sw, fx, fy = flip                      # 8 вариантов осей: обмен x/y и отражения
    if sw:
        dx, dy = dy, dx
    dx, dy = (-dx if fx else dx), (-dy if fy else dy)
    return by_pos.get((r["x"] + dx, r["y"] + dy, r["level"] + dz))


def commands(path, a, b):
    out = []
    for i, l in enumerate(open(path, encoding="cp1251").read().splitlines()[a - 1:b], a):
        l = l.strip()
        if l.startswith(".триг"):
            l = l[5:].strip()
        for c in l.split(";"):
            c = c.strip().replace("подкр ", "")
            if c in RU:
                out.append((i, RU[c], c))
            elif c and not c.startswith(("#", "ждать", "г ", "гг", "кол", "к ", "триг")):
                out.append((i, None, c))
    return out


def main():
    zone, botp, a, b, start = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    base = int(sys.argv[6]) if len(sys.argv) > 6 else 0
    rooms, by_pos = load(zone)
    cmds = commands(botp, a, b)
    best = None
    for flip in itertools.product((False, True), repeat=3):
        cur, errs, trail = rooms[start], 0, []
        for i, d, c in cmds:
            if d is None:
                trail.append((i, c, None))
                continue
            n = neighbor(cur, d, by_pos, flip) if cur["links"].get(d) else None
            if n is None:
                errs += 1
                trail.append((i, f"!!{c}", cur["id"]))
                continue
            cur = n
            trail.append((i, c, cur["id"]))
        if best is None or errs < best[0]:
            best = (errs, flip, trail)
    errs, flip, trail = best
    print(f"ошибок: {errs}, y-инверсия: {flip}")
    for i, c, rid in trail:
        print(f"[{i}] {c} -> {rid + base if rid else ''} {rooms[rid]['name'] if rid else ''}")


if __name__ == "__main__":
    main()
