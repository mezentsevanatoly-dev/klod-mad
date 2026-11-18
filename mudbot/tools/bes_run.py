"""Тоннель бесов (3 этажа) по логу пользователя: этаж 1 — убить всех, потом круг по коридору (без комнат) -> телепорт на 2 этаж;
этаж 2 — то же; этаж 3 — просто убить всех. python -X utf8 tools/bes_run.py [run|build]
run   — создать область, пройти этажи (mapfight с --avoid на клетки-обманки), круги, проверить прибытие; запись в out.log
build — собрать V/plain/csv/md по клеткам боя за историю out.log (без игры)
Телепорт: 160016 восток -> 160023 (2 этаж), 160034 юг -> 160038 (3 этаж); клетки 160017 и 160035 по MSDP — обманки.
"""
import os
import re
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recon_all as R  # noqa: E402

NAME = "бесы"
ENTRY = "105003"
RING1 = ["восток", "восток", "север", "север", "север", "север", "запад", "запад", "запад", "запад", "запад", "юг", "юг",
         "восток", "юг", "юг", "восток"]                                     # от Развилки 160002 до телепорта на 160023
RING2 = ["восток"] * 5 + ["север", "север", "запад", "запад", "север"] + ["запад"] * 4 + ["юг"]   # от 160023 до телепорта на 160038
JUMPS = {("160016", "E"): "160023", ("160034", "S"): "160038"}               # реальные переходы-телепорты
FAKE = {("160016", "E"), ("160034", "S")}                                    # эти рёбра MSDP не использовать при обходе по графу
START = {1: "160002", 2: "160023", 3: "160038"}
D2R = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
R2D = {v: k for k, v in D2R.items()}


def floor_of(v):
    n = int(v)
    if n <= 160019 or n in (160068, 160069):
        return 1
    if n <= 160037 or n in (160070, 160071, 160072, 160082):
        return 2
    return 3


def say(*a):
    R.say("[бесы]", *a)


def ring(moves, expect):
    for m in moves:
        R.cmd(m)
    c = R.cur()
    say("круг пройден, клетка", c.get("vnum"), c.get("name"), "ожидали", expect)
    return c.get("vnum") == expect


def run():
    R.feed_needs()
    if not R.go(ENTRY):
        return say("не дошла до входа")
    out = R.cmd("область создать с|6")
    say("область:", out.strip().splitlines()[-2] if "\n" in out.strip() else out.strip())
    R.cmd("север|2")
    R.cmd("север|2")
    if R.cur().get("vnum") != "160002":
        return say("не в Развилке 160002, стоп")
    for f, avoid, rg, tp in ((1, "160017", RING1, "160023"), (2, "160035", RING2, "160038")):
        args = ["--avoid", avoid]
        R.EXTRA_ARGS[NAME] = args
        res = R.run_map(NAME)
        say(f"этаж {f}: зачистка {res}")
        if res == "dead":
            return
        R.go(START[f])
        if not ring(rg, tp):
            return say(f"телепорт с этажа {f} не сработал, стоп")
    R.EXTRA_ARGS[NAME] = []
    say("этаж 3: зачистка", R.run_map(NAME))


def comp(g, s):
    seen, st = {s}, [s]
    while st:
        v = st.pop()
        for d, t in g[v][2].items():
            if (v, d) in FAKE or t not in g or t in seen:
                continue
            seen.add(t)
            st.append(t)
    return seen


def bfs(g, a, b):
    from collections import deque
    prev, q = {a: None}, deque([a])
    while q:
        v = q.popleft()
        if v == b:
            break
        for d, t in g[v][2].items():
            if (v, d) in FAKE or t not in g or t in prev:
                continue
            prev[t] = (v, d)
            q.append(t)
    if b not in prev:
        return None
    p, v = [], b
    while prev[v]:
        v, d = prev[v]
        p.append(d)
    return p[::-1]


def build():
    g = R.mkv.graph(R.OUTLOG)
    kills = R.kills_in_area("Тоннель бесов")
    moves, cell = [], None       # (клетка, команда)

    def walk(path, c):
        for d in path:
            moves.append((c, D2R[d]))
            c = g[c][2][d]
        return c

    # подход от Центрального зала Геоланта 115050
    ap = R.bfs(g, "115050", ENTRY)
    if ap is None:
        return say("нет подхода от 115050 в графе")
    c = "115050"
    for d in ap:
        moves.append((c, D2R[d]))
        c = g[c][2][d]
    area_idx = len(moves)
    c = walk(["N", "N"], "105003") if False else c
    c = ENTRY
    c = walk(["N", "N"], c)                        # 160001, 160002
    for f, rg in ((1, RING1), (2, RING2), (3, None)):
        s = START[f]
        if f > 1 and c != s:
            return say("цепочка потеряна на этаже", f)
        fl = comp(g, s)
        todo = {v: n for v, n in kills.items() if v in fl and floor_of(v) == f}
        pos = s
        while todo:
            best = None
            for v in todo:
                p = bfs(g, pos, v) if v != pos else []
                if p is not None and (best is None or len(p) < len(best[1])):
                    best = (v, p)
            if best is None:
                break
            pos = walk(best[1], pos)
            todo.pop(best[0])
        if rg:                                      # вернуться на старт этажа и пройти круг по коридору
            back = bfs(g, pos, s)
            pos = walk(back or [], pos)
            for m in rg:
                moves.append((pos, m))
                d = R2D[m]
                pos = JUMPS.get((pos, d)) or g[pos][2][d]
        c = pos
    # V
    lines = []
    for i, (cell, m) in enumerate(moves):
        if i == area_idx:
            lines.append(".триг обл с с")
        lines.append(R.mkv.V.format(v=cell, cmd=m))
    d = os.path.join(R.RECON, NAME)
    open(os.path.join(d, f"рр_{NAME}V.botp"), "w", encoding="cp1251", newline="\r\n").write("\n".join(lines) + "\n")
    plain = [(re.search(r"== \d+\} \{(.*)\}$", l).group(1) if l.startswith("#if") else l) for l in lines]
    open(os.path.join(d, f"рр_{NAME}.botp"), "w", encoding="cp1251", newline="\r\n").write("\n".join(plain) + "\n")
    nm, dropped = R.finish_csv(NAME)
    say("V собран:", len(lines), "строк; клеток боя", len(kills), "csv", nm, "выше уровня:", dropped, "конец", c)


if __name__ == "__main__":
    {"run": run, "build": build}[sys.argv[1] if len(sys.argv) > 1 else "run"]()
