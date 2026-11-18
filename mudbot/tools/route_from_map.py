"""Маршрут бота из карты эксплора: обход всех клеток зоны (DFS с возвратом), шаги с номерами клеток, конец — на старте.
python -X utf8 route_from_map.py <имя маршрута> <старт vnum> <зона> [<зона2> ...] [--bit "<regex имён/строк>"] [--nebit "<regex>"]
         [--only "<regex названий клеток>"] [--skip "<regex названий клеток>"] [--prefix "<шаги до старта через ;>"]
Пишет JMC БОТ АЙЛИНА\\areas\\<имя>.botp и <имя>_mob.csv (из эксплор_<зона>_mob.csv: без [Мирный]/[Продавец], с фильтрами --bit/--nebit).
Не ходит: выходы из ЗОНЫ\\дт_выходы.txt (ДТ, красные, ручные запреты), закрытые/«не прошла» из клетки.csv, в другие зоны.
Формат шага как у маршрутов Айлины: #if {$MsdpRoomVnum != N} {#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить};#if {$MsdpRoomVnum == N} {шаг}"""
import os, sys, re, glob, sys as _s
R = r"C:\Users\User\Desktop\Клод мад"
AREAS = os.path.join(R, "JMC БОТ АЙЛИНА", "areas")
W2D = {"север": "N", "юг": "S", "запад": "W", "восток": "E", "вверх": "U", "вниз": "D"}
D2W = {v: k for k, v in W2D.items()}
OPP = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}


def opt(name, default=None):
    return _s.argv[_s.argv.index(name) + 1] if name in _s.argv else default


pos = [a for i, a in enumerate(_s.argv[1:], 1) if not a.startswith("--") and not (_s.argv[i - 1].startswith("--"))]
name, start, zones = pos[0], pos[1], pos[2:]
only = re.compile(opt("--only")) if opt("--only") else None
skip = re.compile(opt("--skip")) if opt("--skip") else None

# запреты: имя клетки|направление (и зона|имя|направление)
ban = set()
for l in open(os.path.join(R, "ЗОНЫ", "дт_выходы.txt"), encoding="cp1251", errors="replace"):
    p = l.strip().split(";")
    if len(p) == 3:
        zw = set(re.findall(r"\w{4,}", p[0].lower()))     # ДТ из маппера: зона в маппере называется иначе, чем в MSDP — сверяю по общему слову
        if any(zw & set(re.findall(r"\w{4,}", z.lower())) for z in zones): ban.add((p[1], p[2]))
    if len(p) == 4: ban.add((p[0], p[1], p[2]))

G, NM, ZN = {}, {}, {}
for z in zones:
    f = os.path.join(R, "ЗОНЫ", z, "клетки.csv")
    for l in open(f, encoding="cp1251", errors="replace").read().splitlines()[1:]:
        p = l.split(";")
        if len(p) < 3: continue
        v = p[0]; NM[v] = p[1]; ZN[v] = z; G.setdefault(v, {})
        closed = p[3] if len(p) > 3 else ""
        for kv in p[2].split(","):
            if "=" not in kv: continue
            w, t = kv.split("=", 1)
            if w not in W2D: continue
            if re.search(r"(^|,)\s*" + w + r":", closed): continue
            if (p[1], w) in ban or (z, p[1], w) in ban: continue
            G[v][W2D[w]] = t


def ok(v):
    if v not in G: return False
    if only and not only.search(NM.get(v, "")): return False
    if skip and skip.search(NM.get(v, "")): return False
    return True


assert start in G, "старт %s не в карте зон %s" % (start, zones)
steps = []  # (from, dir)
seen = {start}


def dfs(v):
    for d, t in sorted(G[v].items()):
        if t in seen or not ok(t): continue
        if OPP[d] not in G.get(t, {}) or G[t][OPP[d]] != v: continue    # нужен обратный ход тем же путём
        seen.add(t); steps.append((v, d)); dfs(t); steps.append((t, OPP[d]))


_s.setrecursionlimit(10000)
dfs(start)
lines = [".триг #scr botCore.BotInZone = true"]
pre = opt("--prefix")
if pre: lines = [s.strip() for s in pre.split(";") if s.strip()] + lines
for v, d in steps:
    lines.append("#if {$MsdpRoomVnum != %s} {#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить};#if {$MsdpRoomVnum == %s} {%s}" % (v, v, D2W[d]))
lines.append(".триг #scr botCore.BotInZone = false")
open(os.path.join(AREAS, name + ".botp"), "w", encoding="cp1251", errors="replace").write("\n".join(lines) + "\n")

bit = re.compile(opt("--bit")) if opt("--bit") else None
nebit = re.compile(opt("--nebit")) if opt("--nebit") else None
head = None; rows = []; names = set()
for z in zones:
    f = os.path.join(AREAS, "эксплор_%s_mob.csv" % z.replace(" ", "_"))
    if not os.path.exists(f): continue
    L = open(f, encoding="cp1251", errors="replace").read().splitlines()
    head = head or L[0]
    for l in L[1:]:
        if re.search(r"Мирный|Продавец", l) or l.startswith('"";'): continue
        if bit and not bit.search(l): continue
        if nebit and nebit.search(l): continue
        key = l.split(";")[1] if ";" in l else l
        if key in names: continue
        names.add(key); rows.append(l)
open(os.path.join(AREAS, name + "_mob.csv"), "w", encoding="cp1251", errors="replace").write("\n".join([head or '"Имя моба";"Описание в комнате"'] + rows) + "\n")
print("маршрут %s: клеток %d из %d, шагов %d; мобов %d" % (name, len(seen), len(G), len(steps), len(rows)))
missed = [v for v in G if v not in seen and ok(v)]
if missed: print("не дошёл (нет обратного хода/закрыто):", ", ".join("%s %s" % (v, NM[v]) for v in missed[:15]))
for r in rows: print("   ", r.split(";")[0], "|", r.split(";")[1][:70])


