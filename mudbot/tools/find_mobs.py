"""Найти мобов по словам (регулярки) в карточках эксплора и место (клетку) по логам Айлины.
python -X utf8 find_mobs.py "<цель>=<regex>" ...  -> таблица: цель | моб | строка в комнате | ур. | зона | клетки (номер название)
Клетка: в логе строка моба идёт после «[ Exits: …]» комнаты; название комнаты — последняя строка-заголовок перед описанием;
номер — из ЗОНЫ\\<зона>\\клетки.csv по названию (если в зоне одна такая клетка) или из ближайшего ## STEP/WHERE vn=."""
import os, sys, re, glob, collections
R = r"C:\Users\User\Desktop\Клод мад"
AREAS = os.path.join(R, "JMC БОТ АЙЛИНА", "areas")
cards = []   # (zone, name, line, level, raw)
for f in glob.glob(os.path.join(AREAS, "эксплор_*_mob.csv")):
    z = os.path.basename(f)[len("эксплор_"):-len("_mob.csv")].replace("_", " ")
    for l in open(f, encoding="cp1251", errors="replace").read().splitlines()[1:]:
        p = [x.strip('"') for x in l.split('";"')]
        if len(p) > 8: cards.append((z, p[0].strip('"'), p[1].strip().strip('"'), p[8], l))
cells = collections.defaultdict(list)   # (zone, name) -> [vnum]
for f in glob.glob(os.path.join(R, "ЗОНЫ", "*", "клетки.csv")):
    z = os.path.basename(os.path.dirname(f))
    for l in open(f, encoding="cp1251", errors="replace").read().splitlines()[1:]:
        p = l.split(";")
        if len(p) > 1: cells[(z, p[1])].append(p[0])
targets = [a.split("=", 1) for a in sys.argv[1:] if "=" in a]
want = {}
for t, rx in targets:
    r = re.compile(rx, re.I)
    for c in cards:
        if r.search(c[1]) or r.search(c[2]): want.setdefault(c[2].rstrip(". ").strip(), []).append((t, c))
# места по логам
where = collections.defaultdict(collections.Counter)
logs = sorted(glob.glob(os.path.join(R, "JMC БОТ АЙЛИНА", "Logs", "*.log")))
keys = list(want)
for f in logs:
    title = None; prev = None; vn = None; inroom = False; last = ""
    for raw in open(f, encoding="cp1251", errors="replace"):
        t = raw[9:].rstrip("\n") if re.match(r"\d\d:\d\d:\d\d ", raw) else raw.rstrip("\n")
        m = re.search(r"vn=(\d+)|## WHERE (\d+)", t)
        if m: vn = m.group(1) or m.group(2)
        if t.startswith("[ Exits:"):
            inroom = True; title = prev; continue
        if re.search(r"\d+H \d+M \d+V", t): inroom = False
        if inroom:
            s = t.strip().rstrip(". ").strip()
            for k in keys:
                if s.startswith(k):
                    where[k][title or "?"] += 1
        if t.startswith("   ") and last and not last.startswith(" ") and not last.startswith("[") and not re.search(r"\d+H \d+M|^#|^>>|^##", last) and len(last) < 60:
            prev = last.strip()        # заголовок комнаты: строка без отступа прямо перед описанием с отступом
        last = t
out = []
for k, lst in want.items():
    for t, c in lst[:1]:
        z = c[0]; places = []
        for title, n in where[k].most_common(4):
            vs = cells.get((z, title)) or [v for (zz, nm), v2 in cells.items() if nm == title for v in v2][:3]
            places.append("%s %s (%d)" % (",".join(vs[:3]) if vs else "?", title, n))
        out.append((t, c[1], c[2], c[3], z, "; ".join(places) or "в логах не видела"))
out.sort()
print("| Цель | Моб | Строка в комнате | Ур. | Зона | Где (клетка, сколько раз видела) |")
print("|---|---|---|---|---|---|")
for o in out: print("| %s |" % " | ".join(o))

