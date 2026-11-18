"""Опыт по уровням из логов: потолок опыта за моба и ДСУ (опыт до следующего уровня) -> data/db/exp_levels.md"""
import os, re, collections
JMC = os.path.join(os.path.dirname(__file__), "..", "..", "JMC")
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "db", "exp_levels.md")
dsu = collections.defaultdict(list)       # уровень -> [ДСУ]
ceil = collections.defaultdict(list)
for f in sorted(os.listdir(JMC)):
    p = os.path.join(JMC, f)
    if not os.path.isfile(p) or "." in f:
        continue
    t = open(p, encoding="cp1251", errors="replace").read().replace("\r", "").split("\n")
    lvl = None
    for i, l in enumerate(t):
        m = re.search(r"Варвар (\d+) уровня", l)
        if m:
            lvl = int(m.group(1))
        m = re.search(r"Вам надо набрать (\d+) опыта", l)
        if m and lvl:
            dsu[lvl].append(int(m.group(1)))
        if "Вы поднялись на уровень" in l and lvl:
            lvl += 1
        m = re.match(r"^Вы получили (\d+) единиц", l)
        if m and lvl:
            ceil[lvl].append(int(m.group(1)))
rows = ["# Опыт по уровням (из логов пользователя, Эсхирд)", "",
        "Потолок = максимум за убийство на этом уровне (моб равного/выше уровня); ДСУ = опыт до след. уровня (максимум в логах, т.е. сразу после повышения).", "",
        "| лвл | потолок за моба | ДСУ (макс) | убийств до уровня по потолку |", "|---|---|---|---|"]
for lv in sorted(set(dsu) | set(ceil)):
    c = max(ceil[lv]) if ceil[lv] else 0
    d = max(dsu[lv]) if dsu[lv] else 0
    rows.append(f"| {lv} | {c} | {d} | {round(d / c) if c and d else ''} |")
open(OUT, "w", encoding="utf-8").write("\n".join(rows))
print("\n".join(rows))
