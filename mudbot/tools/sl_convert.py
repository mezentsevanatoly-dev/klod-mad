"""Маршрут Чвырлы «Слава» (рр2_сл*, без vnum) + наша разведка зоны (areas/msdp/<Зона>.json, реальные vnum) -> .botp с vnum.

python tools/sl_convert.py <botp_Чвырлы> <зона.json> <выход.botp> [--from-line N] [--to-line M]

Маршрут Чвырлы: строки «до создания области» — дорога от комнаты отдыха (рр2 = Геолант, Центральный зал 115050), одна
команда на строку; строка с «обл с … +3;…» — создание; дальше — маршрут по зоне (в нём `.триг` — квесты/действия).
Мы берём только часть после создания и «прогоняем» её по графу выходов нашей разведки, ставя перед каждой строкой vnum клетки.
Вход: у стартовой комнаты зоны есть выход наружу (в соседнюю зону) — это клетка, где создаётся область, и направление входа.
Результат пишется в cp1251, как у Чвырлы (botp_walk.load_steps читает так же).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from explore_msdp import CMD  # noqa: E402

RU = {v: k for k, v in CMD.items()}               # «север» -> N
OPP = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}
CRE = re.compile(r"созд|обл с ")


def split_route(lines, from_line=None, to_line=None):
    cre = next((i for i, l in enumerate(lines) if l.startswith(".триг") and CRE.search(l)), None)
    if cre is None:
        raise SystemExit("в маршруте нет строки создания области")
    a = (from_line - 1) if from_line else cre + 1
    fin = [i for i, l in enumerate(lines) if re.search(r"BotInZone = false|реколим", l)]
    b = (to_line) if to_line else (fin[-1] if fin else len(lines))
    return cre, lines[a:b]


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    botp, zone_json, out = args[:3]
    fl = int(sys.argv[sys.argv.index("--from-line") + 1]) if "--from-line" in sys.argv else None
    tl = int(sys.argv[sys.argv.index("--to-line") + 1]) if "--to-line" in sys.argv else None
    lines = open(botp, encoding="cp1251", errors="replace").read().splitlines()
    cre, route = split_route(lines, fl, tl)
    z = json.load(open(zone_json, encoding="utf-8"))
    rooms = z["rooms"]
    start = str(z["start"])
    outer, into = None, None
    for d, t in rooms[start]["exits"].items():     # выход из стартовой комнаты наружу — это вход, клетка создания области
        if str(t) not in rooms:
            outer, into = str(t), OPP[d]
    if outer is None:
        raise SystemExit(f"у стартовой комнаты {start} нет выхода наружу зоны")
    graph = {k: {d: str(t) for d, t in r["exits"].items()} for k, r in rooms.items()}
    graph[outer] = {into: start}
    cur, errors, moves, cut = outer, [], 0, len(route)
    for i, l in enumerate(route):
        s = l.strip()
        if not s:
            continue
        cmds = [c.strip().replace("подкр ", "") for c in (s[5:] if s.startswith(".триг") else s).split(";")]
        leave = False
        for c in cmds:
            d = RU.get(c)
            if not d:
                continue
            nxt = graph.get(cur, {}).get(d)
            if nxt is None:
                if cur == outer:                    # дальше — выход из зоны и «дорога домой» (в клетках вне зоны выходов у нас нет)
                    leave = True
                else:
                    errors.append(f"строка {i + 1}: из {cur} {c} — нет выхода")
                break
            cur, moves = nxt, moves + 1
        if leave:
            cut = i
            break
        if errors:
            break
    route = route[:cut]
    # второй проход: расставить vnum (позиция до строки)
    cur, res = outer, ["#if {$MsdpRoomVnum ==%s} {#var SumReset 0}" % outer]
    for i, l in enumerate(route):
        s = l.strip()
        if not s:
            continue
        if s.startswith(".триг"):
            res.append(s)
        else:
            res.append("#if {$MsdpRoomVnum ==%s} {%s}" % (cur, s))
        for c in [c.strip().replace("подкр ", "") for c in (s[5:] if s.startswith(".триг") else s).split(";")]:
            d = RU.get(c)
            if d and graph.get(cur, {}).get(d):
                cur = graph[cur][d]
    open(out, "w", encoding="cp1251", newline="\r\n", errors="replace").write("\n".join(res) + "\n")
    print(f"зона {z['area']}: вход из {outer} направление {into}; строк маршрута {len(route)}, шагов-движений {moves}, "
          f"записано {len(res)} строк -> {out}")
    if errors:
        print("ОШИБКИ:", *errors, sep="\n  ")
        sys.exit(1)


if __name__ == "__main__":
    main()
