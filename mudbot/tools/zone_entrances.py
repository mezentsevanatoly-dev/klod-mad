"""Спидволки от Центральной площади Элендора до входа в каждую зону и обратно (в data/game.db + speedwalks.txt).

Вход определяется игрой: `путь вход в зону <имя>` -> комната, где виден `[Зона, <напр>: <Зона>]`.
Маршрут считается поиском в ширину по графу rooms (exits из MSDP), поэтому ходить для этого не нужно,
кроме одного вызова `путь`, чтобы узнать комнату входа.
  python tools/zone_entrances.py                 все зоны из zone_survey.ZONES
  python tools/zone_entrances.py "Парк" ...      только указанные
"""
import json
import os
import re
import sqlite3
import sys
from collections import deque

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
import zone_survey as zs

HUB = "100009"                 # Центральная площадь Элендора
HUBNAME = "элен_цп"
OPP = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}
SW = os.path.join(HERE, "speedwalks.txt")


def graph():
    g = {}
    for v, ex in sqlite3.connect(zs.DB).execute("select vnum, exits from rooms"):
        try:
            g[v] = json.loads(ex)
        except Exception:
            pass
    return g


def bfs(g, a, b):
    prev = {a: None}
    q = deque([a])
    while q:
        v = q.popleft()
        if v == b:
            break
        for d, n in g.get(v, {}).items():
            if n not in prev:
                prev[n] = (v, d)
                q.append(n)
    if b not in prev:
        return None
    out = []
    while prev[b]:
        v, d = prev[b]
        out.append(d)
        b = v
    return out[::-1]


def compress(dirs):
    s = ""
    i = 0
    while i < len(dirs):
        j = i
        while j < len(dirs) and dirs[j] == dirs[i]:
            j += 1
        s += (str(j - i) if j - i > 1 else "") + dirs[i].lower()
        i = j
    return s


def save(name, path, end, note):
    c = sqlite3.connect(zs.DB, timeout=20)
    c.execute("delete from speedwalks where name=?", (name,))
    c.execute("insert into speedwalks (name,path,end_vnum,note) values (?,?,?,?)", (name, path, end, note))
    c.commit()
    c.close()
    with open(SW, "a", encoding="utf-8") as f:
        f.write(f"{name} {path}\n")


def main(only):
    g = graph()
    for zone, entrance, need_area, _ in zs.ZONES:
        if only and zone not in only or zone == "Мад школа":
            continue
        if not zs.go_home():
            zs.say("нет дома — стоп")
            return
        zs.cmd([f"путь вход в зону {entrance}"], 60)
        v, area, name = zs.where()
        o = zs.cmd(["смотреть"], 2)
        m = re.search(r"\[Зона, (?:на )?([а-я]+): " + re.escape(zone) + r",? ?(ур\. ?[\d-]+)?", o)
        if not v or not m:
            zs.say(f"{zone}: вход не найден (комната {v} {name})")
            continue
        fwd = bfs(g, HUB, v)
        if fwd is None:
            zs.say(f"{zone}: вход {v} недостижим из площади по графу")
            continue
        back = [OPP[d] for d in reversed(fwd)]
        base = f"{HUBNAME}-{zone.replace(' ', '_')}"
        note = f"до входа в зону «{zone}» ({m.group(2) or ''}); комната {v} {name}; выход в зону: {m.group(1)}; считано по графу rooms"
        save(base + "_вход", compress(fwd), v, note)
        save(base + "_вход_обратно", compress(back), HUB, "обратно от входа в зону к Центральной площади")
        zs.say(f"{zone}: {compress(fwd)} | обратно {compress(back)} | вход {v} {m.group(1)} {m.group(2) or ''}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
