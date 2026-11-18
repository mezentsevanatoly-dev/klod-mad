"""Для каждого лога: найти по графу rooms (game.db), с какой клетки начался лог и в какой клетке пользователь набрал
«область создать». Ходы лога (движение + название клетки прихода) прогоняются по графу от каждой подходящей стартовой
клетки; неудавшиеся ходы (дверь) пропускаются. Результат: data/recon/_entries.json {лог: {start, entry, sw, dir, skipped}}.
"""
import json
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECON = os.path.join(ROOT, "data", "recon")
D = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
L = {"N": "n", "S": "s", "E": "e", "W": "w", "U": "u", "D": "d"}
db = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
R = {}
for v, z, n, e in db.execute("select vnum,zone,name,exits from rooms"):
    ex = json.loads(e) if e and e.startswith("{") else {}
    R[str(v)] = (z, n, {k.upper(): str(x) for k, x in ex.items()})
byname = {}
for v, (z, n, e) in R.items():
    byname.setdefault(n, []).append(v)


def walk(start, steps, maxskip=4):
    cur, skipped, path = start, 0, []
    for st in steps:
        t = R.get(cur, ("", "", {}))[2].get(D[st["move"]])
        if t and t in R and R[t][1] == st["room"]:
            path.append(L[D[st["move"]]])
            cur = t
        else:
            skipped += 1
            if skipped > maxskip:
                return None
    return cur, "".join(path), skipped


def compress(p):
    return "".join(f"{len(g[0])+len(g[1])*0 if False else ''}" for g in []) or re.sub(r"(.)\1+", lambda m: f"{len(m.group(0))}{m.group(1)}", p)


def main():
    res = {}
    for name in sorted(os.listdir(RECON)):
        rp = os.path.join(RECON, name, name + "_route.json")
        if name.startswith("_") or not os.path.exists(rp):
            continue
        steps = json.load(open(rp, encoding="utf-8"))["steps"]
        k = next((i for i, s in enumerate(steps) if s.get("cmd", "").startswith("область создать")), None)
        if k is None:
            res[name] = {"error": "нет области"}
            continue
        pre = [s for s in steps[:k] if "move" in s]
        # убрать лишний хвост до первого узнаваемого отеля: пробуем разные начала (обрезка с головы до 12 ходов)
        best = None
        for cut in range(0, min(14, len(pre))):
            seq = pre[cut:]
            if not seq:
                break
            first_room_candidates = [v for v, (z, n, e) in R.items() if D[seq[0]["move"]][0] in e and e[D[seq[0]["move"]][0]] in R
                                     and R[e[D[seq[0]["move"]][0]]][1] == seq[0]["room"]]
            for s0 in first_room_candidates:
                r = walk(s0, seq)
                if r and (best is None or (r[2], -len(seq)) < (best[3], -len(best[4]))):
                    best = (s0, r[0], r[1], r[2], seq, cut)
            if best and best[3] == 0:
                break
        d = steps[k]["cmd"].split()
        res[name] = ({"error": "не нашла путь по графу"} if not best else
                     {"start": best[0], "start_name": R[best[0]][1], "entry": best[1], "entry_name": R[best[1]][1],
                      "entry_zone": R[best[1]][0], "sw": compress(best[2]), "skipped": best[3], "cut": best[5],
                      "dir": d[2] if len(d) > 2 else "?"})
    json.dump(res, open(os.path.join(RECON, "_entries.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for n, r in res.items():
        print(n, r)


if __name__ == "__main__":
    main()
