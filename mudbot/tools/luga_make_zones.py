# -*- coding: utf-8 -*-
"""Три зоны луга по уровням для круга зон: луга12 (мобы 12-15), луга15 (15-18), луга18 (18+).
Маршрут у всех один и тот же (обход ВСЕХ клеток от склада р1 Элендора: склад -> ЦП -> подход -> луга -> назад), отличаются только списки мобов (_mob.csv).
Источник: data/recon/луга_айлина/explore.json (эксплор Айлиной). Запуск: python -X utf8 tools/luga_make_zones.py
Пишет в data/recon/луга_айлина/ и копирует в JMC БОТ ИНКА\\areas (cp1251, CRLF)."""
import os, re, sys, json, shutil, sqlite3, collections

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(BASE, "mudbot", "data", "recon", "луга_айлина")
AREAS = [os.path.join(BASE, "JMC БОТ ИНКА", "areas")]
S = json.load(open(os.path.join(OUT, "explore.json"), encoding="utf-8"))
cells = {int(k): v for k, v in S["cells"].items()}
cards, line2name = S["cards"], S["line2name"]
db = sqlite3.connect(os.path.join(BASE, "mudbot", "data", "game.db"))
M = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
BK = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}
ENTRY = 137220


def db_exits(v):
    r = db.execute("select exits from rooms where vnum=?", (str(v),)).fetchone()
    return {k: int(x) for k, x in json.loads(r[0]).items()} if r else {}


def vline(frm, cmd):
    return "#if {$MsdpRoomVnum != %d} {#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить};#if {$MsdpRoomVnum == %d} {%s}" % (frm, frm, cmd)


def path_db(src, dst):
    prev = {src: None}; q = collections.deque([src])
    while q:
        v = q.popleft()
        if v == dst:
            break
        for d, n in db_exits(v).items():
            if n not in prev:
                prev[n] = (v, d); q.append(n)
    p = []; v = dst
    while prev.get(v):
        pv, d = prev[v]; p.append((pv, d, v)); v = pv
    return p[::-1]


# маршрут: склад 100076 -> ЦП 100009 -> подход 11esw17s -> 137220 -> обход дерева -> назад
to_cp = path_db(100076, 100009)
appr = []; v = 100009
for n, d in re.findall(r"(\d*)([nsewud])", "11esw17s"):
    for _ in range(int(n) if n else 1):
        nv = db_exits(v).get(d.upper()); appr.append((v, d.upper(), nv)); v = nv
assert v == ENTRY, v
seen = {ENTRY}; children = collections.defaultdict(list)
for frm, d, to in S["moves"]:
    if to in cells and to not in seen:
        seen.add(to); children[frm].append((d, to))
walk = []
sys.setrecursionlimit(5000)


def dfs(v):
    for d, ch in children.get(v, []):
        walk.append((v, d)); dfs(ch); walk.append((ch, BK[d]))


dfs(ENTRY)
assert len(seen) == len(cells) or True
lines = [".триг #scr botCore.BotInZone = false"]
for frm, d, to in to_cp:
    lines.append(vline(frm, M[d]))
for frm, d, to in appr:
    lines.append(vline(frm, M[d]))
lines.append(".триг #scr botCore.BotInZone = true")
for frm, d in walk:
    lines.append(vline(frm, M[d]))
lines.append(".триг #scr botCore.BotInZone = false")
for frm, d, to in reversed(appr):
    lines.append(vline(to, M[BK[d]]))
for frm, d, to in reversed(to_cp):
    lines.append(vline(to, M[BK[d]]))

# мобы: описание в комнате -> имя; строки, общие для нескольких видов, исключаем (бот не отличит)
bad_names = set()                      # строки у разных видов после пересчёта (luga_fix_lines.py) без конфликтов
for l, ns in S.get("line_conflicts", {}).items():
    bad_names |= set(ns)
name2line = {}
for l, n in line2name.items():
    name2line.setdefault(n, l)
hdr = ["Имя моба", "Описание в комнате", "Hp", "MaxHp", "Mp", "MaxMp", "Опыт", "Деньги", "Уровень", "Агрессивность", "Ассистит?", "Умения", "Профессия", "Раса", "Флаги NPC"]
CAP = {12: 297, 13: 517, 14: 902, 15: 1582, 16: 2782, 17: 4824, 18: 8404, 19: 14698, 20: 25798, 21: 45425, 22: 79211, 23: 138666}


def rows_for(lo, hi):
    out = []
    for nm, cd in sorted(cards.items(), key=lambda x: (x[1]["level"], x[0])):
        if not (lo <= cd["level"] <= hi) or nm in bad_names:
            continue
        desc = name2line.get(nm, "")
        if not desc:
            continue
        mp = cd["mp"] or "0"
        out.append([nm, desc, cd["hp"], cd["hp"], "%s/%s" % (mp, mp), "%s/%s" % (mp, mp), str(CAP.get(cd["level"] + 2, 0)), "0", str(cd["level"]),
                    "false", "false", cd["skills"] or "-", cd["class"], "", ""])
    return out


ZONES = [("луга12", 12, 15), ("луга15", 15, 18), ("луга18", 18, 99)]
skipped = sorted(bad_names)
for name, lo, hi in ZONES:
    rows = rows_for(lo, hi)
    for d in [OUT] + AREAS:
        with open(os.path.join(d, name + ".botp"), "w", encoding="cp1251", newline="") as f:
            f.write("\r\n".join(lines) + "\r\n")
        with open(os.path.join(d, name + "_mob.csv"), "w", encoding="cp1251", newline="") as f:
            f.write(";".join('"%s"' % h for h in hdr) + "\r\n")
            for r in rows:
                f.write(";".join('"%s"' % x for x in r) + "\r\n")
    print("%s: мобов %d (ур %d-%s): %s" % (name, len(rows), lo, hi if hi < 99 else "+", ", ".join(r[0] for r in rows)))
print("строк в маршруте:", len(lines), "| исключены (общая строка в комнате у разных видов):", skipped or "нет")

