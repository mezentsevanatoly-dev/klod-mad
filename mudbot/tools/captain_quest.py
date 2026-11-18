"""Квест капитана эльфийского судна (Деревня рыбаков): найти бродящего капитана, `г видел`, `груп все`, довести до «Сокровищницы»
(высокий некромант), добить некроманта. Только нужные команды (триггеры бота сами открывают двери и подбирают лут).
  python tools/captain_quest.py
"""
import json
import os
import re
import sqlite3
import sys
import time
from collections import deque

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
import zone_survey as zs
import zone_entrances as ze

DB = os.path.join(HERE, "data", "game.db")
BLOCK = {"117012", "117013"}                         # проход под ковром: сначала ищем капитана в деревне


def say(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def text_here():
    o = zs.cmd(["смотреть"], 2.2)
    return o


def village_rooms(start):
    g = ze.graph()
    seen, order, q = {start}, [], deque([start])
    while q:
        v = q.popleft()
        order.append(v)
        for d, w in g.get(v, {}).items():
            if w not in seen and w not in BLOCK and w in g and w.startswith("1170") or (w not in seen and w.startswith("1170") and w not in BLOCK and w in g):
                seen.add(w)
                q.append(w)
    return order


def find_captain():
    cur = zs.where()[0]
    o = text_here()
    if "капитан эльфийского судна стоит здесь" in o:
        return True
    order = village_rooms("117016")                    # только деревня: BFS от «Мощеной дороги» без прохода под ковром (подвал в список не попадает)
    say("комнат деревни для поиска:", len(order))
    for k, v in enumerate(order[:80]):
        if not zs.walk_to(v):
            continue
        o = text_here()
        if "капитан эльфийского судна стоит здесь" in o:
            say("капитан найден в", zs.where())
            return True
    return False


def main():
    say("старт:", zs.where())
    if not find_captain():
        say("капитана не нашла за один проход — стоп")
        return
    o = zs.cmd(["г видел", "груп все"], 3)
    ok = "следует за вами" in o or "принят в вашу группу" in o
    say("капитан в группе:", ok)
    if not ok:
        say("не взяла капитана — стоп")
        return
    c = sqlite3.connect(DB)
    tr = c.execute("select vnum from rooms where zone='Деревня рыбаков' and name='Сокровищница'").fetchall()
    say("сокровищница:", tr)
    if not tr:
        return
    tgt = tr[0][0]
    ze_graph = ze.graph()
    p = ze.bfs(ze_graph, zs.where()[0], tgt)
    say("путь до сокровищницы шагов:", len(p) if p else None)
    if not p:
        return
    ok = zs.walk_to(tgt)
    say("в сокровищнице:", ok, zs.where())
    o = zs.cmd(["смотреть", "группа"], 3)
    say("в комнате:", [l.strip()[:60] for l in o.split("\n") if re.search(r"некромант|капитан|Капитан", l)])


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
