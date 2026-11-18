"""Квест-маршрут из короткого сценария (DSL) + наша карта зоны -> .botp с vnum; команды квеста дублируются группе («гг !…»).

python tools/quest_route.py <сценарий.txt> <зона.json> <выход.botp>
Строки сценария (# — комментарий):
  start <vnum>                   — где стоим сейчас (клетка первого шага)
  go <vnum>                      — дойти до комнаты кратчайшим путём по карте зоны (боевые клетки бот чистит сам)
  move <направление> <vnum>      — шаг, которого нет на карте (скрытый выход, вход вне разведки): север/юг/…; после него мы в <vnum>
  warp <команда> -> <vnum>       — команда, меняющая комнату не выходом (плыть корабль, войти портал); после неё мы в <vnum>
  do <команда; команда>          — команды в текущей комнате
  dup <команда>                  — команда и тут же «гг !<команда>» (квестовые действия, чтобы то же сделали остальные)
  dupwarp <команда> -> <vnum>    — как warp, но с дублированием группе
По просьбе пользователя группе дублируются квестовые команды (дать, плыть, взять останки, г да …), но не «войти», «установить» и подобные.
"""
import json
import os
import re
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from explore_msdp import CMD  # noqa: E402

RU = {k: v for k, v in CMD.items()}               # «N» -> «север»


def bfs(graph, a, b):
    prev, q = {a: None}, deque([a])
    while q:
        v = q.popleft()
        if v == b:
            out = []
            while prev[v]:
                v, d = prev[v]
                out.append(d)
            return out[::-1]
        for d, t in graph.get(v, {}).items():
            if t not in prev and t in graph:
                prev[t] = (v, d)
                q.append(t)
    return None


def main():
    scen, zone_json, out = sys.argv[1:4]
    z = json.load(open(zone_json, encoding="utf-8"))
    graph = {k: {d: str(t) for d, t in r["exits"].items() if d in RU} for k, r in z["rooms"].items()}
    dt = {k for k, r in z["rooms"].items() if r.get("dt_hint")}
    res, cur, errors = [], None, []
    for n, raw in enumerate(open(scen, encoding="utf-8-sig").read().splitlines(), 1):
        s = raw.split("#", 1)[0].strip()
        if not s:
            continue
        cmd, _, rest = s.partition(" ")
        rest = rest.strip()
        if cmd == "start":
            cur = rest
            res.append("#if {$MsdpRoomVnum ==%s} {#var SumReset 0}" % cur)
        elif cmd == "go":
            p = bfs(graph, cur, rest)
            if p is None:
                errors.append(f"строка {n}: нет пути {cur} -> {rest}")
                continue
            for d in p:
                nxt = graph[cur][d]
                if nxt in dt:
                    errors.append(f"строка {n}: путь идёт через ДТ-комнату {nxt}")
                res.append("#if {$MsdpRoomVnum ==%s} {%s}" % (cur, RU[d]))
                cur = nxt
        elif cmd == "move":
            d, vn = rest.split()
            res.append("#if {$MsdpRoomVnum ==%s} {%s}" % (cur, d))
            cur = vn
        elif cmd in ("warp", "dupwarp"):
            c, vn = [x.strip() for x in rest.split("->")]
            line = f"{c};гг !{c}" if cmd == "dupwarp" else c
            res.append("#if {$MsdpRoomVnum ==%s} {%s}" % (cur, line))
            cur = vn
        elif cmd == "do":
            res.append("#if {$MsdpRoomVnum ==%s} {%s}" % (cur, rest))
        elif cmd == "dup":
            res.append("#if {$MsdpRoomVnum ==%s} {%s;гг !%s}" % (cur, rest, rest))
        else:
            errors.append(f"строка {n}: неизвестная команда сценария «{cmd}»")
    open(out, "w", encoding="cp1251", newline="\r\n", errors="replace").write("\n".join(res) + "\n")
    print(f"записано {len(res)} строк -> {out}; последняя клетка {cur}")
    if errors:
        print("ОШИБКИ:", *errors, sep="\n  ")
        sys.exit(1)


if __name__ == "__main__":
    main()
