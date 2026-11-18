# -*- coding: utf-8 -*-
"""Список мобов с опытом из mob_kills (3 недели логов пользователя) и расчёт для Кимпи.
exp за моба = min(цена моба, потолок уровня персонажа). Цена моба = максимум, виденный в логах на уровне, где потолок >= цены
(берём максимум по всем убийствам этого моба на уровнях >= 23; иначе максимум вообще).
Пишет data/мобы_экспа_список.csv и печатает анализ по зонам для уровней Кимпи 22..29."""
import sqlite3, os, io, sys, csv, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
c = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
CAP = {22: 79211, 23: 138666, 24: 243591, 25: 429233}
for l in range(26, 31):
    CAP[l] = int(CAP[l - 1] * 1.75)
DSU = {22: 4250084, 23: 6256287, 24: 16758904, 25: 24943830}
for l in range(26, 30):
    DSU[l] = int(DSU[l - 1] * 1.5)
mobs = collections.defaultdict(lambda: {"lv": 0, "zones": collections.Counter(), "obs": []})
def _i(x):
    try:
        return int(str(x).strip())
    except Exception:
        return 0
for zone, name, ml, my, exp in c.execute("select zone,name,mob_level,my_level,exp from mob_kills where exp>0"):
    ml, my, exp = _i(ml), _i(my), _i(exp)
    m = mobs[name]
    m["lv"] = max(m["lv"], ml or 0)
    m["zones"][zone] += 1
    m["obs"].append((my or 0, exp))
rows = []
for n, m in mobs.items():
    hi = [e for (my, e) in m["obs"] if my >= 23]
    base = max(hi) if hi else max(e for (my, e) in m["obs"])
    z = m["zones"].most_common(1)[0][0]
    rows.append((z, n, m["lv"], base, len(m["obs"])))
rows.sort(key=lambda r: (r[0], -r[3]))
out = os.path.join(ROOT, "data", "мобы_экспа_список.csv")
with open(out, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["зона", "моб", "ур.моба", "цена(опыт)", "убийств в логах"])
    w.writerows(rows)
print("мобов в списке:", len(rows), "->", out)
byz = collections.defaultdict(list)
for z, n, lv, b, k in rows:
    byz[z].append(b)
print("\nопыт Кимпи за ПОЛНЫЙ проход зоны (по каждому мобу min(цена, потолок)), и сколько проходов до след. уровня")
print("зона | мобов | " + " | ".join("%d лвл" % l for l in (22, 23, 24, 25)))
tab = []
for z, v in byz.items():
    if max(v) < 60000 or len(v) < 5:
        continue
    cells = []
    for l in (22, 23, 24, 25):
        s = sum(min(b, CAP[l]) for b in v)
        cells.append((s, DSU[l] / s if s else 0))
    tab.append((cells[0][0], z, len(v), cells))
tab.sort(reverse=True)
for _, z, k, cells in tab[:25]:
    print("%s | %d | " % (z, k) + " | ".join("%.1fM (%.1f пр.)" % (s / 1e6, p) for s, p in cells))
