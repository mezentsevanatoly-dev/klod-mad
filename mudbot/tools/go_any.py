"""Довести Айлину по общему графу (эксплор + game.db, как в route_check): go_any.py <клетка> [--dry]
Путь BFS, шлётся кусками по 10 шагов, после каждого куска сверка клетки; сбилась — пересчитать от текущей."""
import os, sys, time, collections
os.environ.setdefault("JMC_TARGET", r"C:\Users\User\Desktop\Клод мад\JMC БОТ АЙЛИНА")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jmc, route_check as rc
from where import where
G, names, zones = rc.graph()


def path(a, b):
    prev = {a: None}; q = collections.deque([a])
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in G.get(v, {}).items():
            if t not in prev: prev[t] = (v, d); q.append(t)
    if b not in prev: return None
    out = []; v = b
    while prev[v]: v, d = prev[v]; out.append(d)
    return out[::-1]


target = sys.argv[1]
for attempt in range(8):
    cur = where()[0]
    if cur == target: print("на месте", target); sys.exit(0)
    p = path(cur, target)
    if p is None: print("нет пути из", cur, "в", target); sys.exit(1)
    print("из", cur, "шагов", len(p), flush=True)
    if "--dry" in sys.argv: print(" ".join(rc.WORD[d] for d in p)); sys.exit(0)
    chunk = p[:10]
    jmc.type_line(";".join(rc.WORD[d] for d in chunk), force=True)
    time.sleep(1 + len(chunk) * 0.4)
print("сейчас", where())
