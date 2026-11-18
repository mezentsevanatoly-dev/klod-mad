# -*- coding: utf-8 -*-
"""Итоги эксплора луга (Айлина): читает data/recon/луга_айлина/explore.json, пишет туда же:
  mobs.md (все мобы: имя, уровень, профа, хиты, навыки, описание, опыт), cells.csv, карта map.png,
  луга.botp (V-маршрут от ЦП 100009 по всем клеткам и назад), луга_mob.csv (правильные имя<->описание в комнате).
Запуск: python -X utf8 tools/luga_report.py [--install]   (--install: скопировать botp/csv в JMC БОТ АЙЛИНА\\areas)"""
import os, sys, re, json, csv, collections, sqlite3, shutil

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(BASE, "mudbot", "data", "recon", "луга_айлина")
S = json.load(open(os.path.join(OUT, "explore.json"), encoding="utf-8"))
cells = {int(k): v for k, v in S["cells"].items()}
cards, exp, line2name = S["cards"], S["exp"], S["line2name"]

CAP = {1: 1, 2: 1, 3: 1, 4: 3, 5: 5, 6: 10, 7: 17, 8: 29, 9: 55, 10: 94, 11: 171, 12: 297, 13: 517, 14: 902, 15: 1582, 16: 2782,
       17: 4824, 18: 8404, 19: 14698, 20: 25798, 21: 45425, 22: 79211, 23: 138666, 24: 243591, 25: 429233, 26: 567765}


def full_exp(mob_level):
    """Полный опыт за моба: потолок уровня персонажа, когда персонаж не более чем на 2 уровня выше моба."""
    return CAP.get(min(mob_level + 2, 26), 0)


# ---------- мобы ----------
rows = []
cells_of = collections.defaultdict(set)
for vn, c in cells.items():
    for nm in c.get("mobs", []):
        cells_of[nm].add(vn)
for nm, cd in cards.items():
    rows.append((cd["level"], nm, cd, exp.get(nm)))
rows.sort(key=lambda r: (r[0], r[1]))
with open(os.path.join(OUT, "mobs.md"), "w", encoding="utf-8") as f:
    f.write("# Заливные луга: мобы (эксплор Айлиной, ДК 26)\n\n")
    f.write("Опыт «Айлина» — реально полученный за одно убийство (26 лвл). «Полный» — потолок за моба для персонажа на 2 уровня выше моба.\n\n")
    f.write("| Ур | Имя | Профа | Хиты | Навыки | Вид | Клеток | Опыт Айлина | Полный опыт |\n|---|---|---|---|---|---|---|---|---|\n")
    for lv, nm, cd, e in rows:
        f.write("| %d | %s | %s | %s | %s | %s | %d | %s | %d |\n" % (lv, nm, cd["class"], cd["hp"], cd["skills"] or "-", cd["kind"], len(cells_of.get(nm, ())),
                                                              ("%d" % e) if e and e > 0 else "-", full_exp(lv)))
    f.write("\n## Описания\n\n")
    for lv, nm, cd, e in rows:
        f.write("**%s** (ур %d, %s): %s\n\n" % (nm, lv, cd["class"], cd["desc"]))
    f.write("\n## Строка в комнате -> имя\n\n")
    for ln, nm in sorted(line2name.items(), key=lambda x: x[1]):
        f.write("- %s -> **%s**\n" % (ln.strip(), nm))

# ---------- клетки ----------
with open(os.path.join(OUT, "cells.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["vnum", "название", "выходы", "мобы", "описание"])
    for vn in sorted(cells):
        c = cells[vn]
        w.writerow([vn, c["name"], "".join(c["exits"]), ", ".join(c.get("mobs", [])), c["desc"]])

# ---------- конфликты описание<->имя ----------
conf = collections.defaultdict(set)
for vn, c in cells.items():
    ml, mn = c.get("mobs_lines", []), c.get("mobs", [])
    if len(ml) == len(mn):
        for l, n in zip(ml, mn):
            conf[l].add(n)
conflicts = {l: sorted(n) for l, n in conf.items() if len(n) > 1}

# ---------- карта ----------
DIR = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
db = sqlite3.connect(os.path.join(BASE, "mudbot", "data", "game.db"))
edges = collections.defaultdict(dict)
for vn, c in cells.items():
    for d, n in c.get("edges", {}).items():
        edges[vn][d] = n
        edges[n].setdefault({"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}[d], vn)
pos = {}
start = 137220 if 137220 in cells else min(cells)
pos[start] = (0, 0); q = collections.deque([start]); used = {(0, 0)}
while q:
    v = q.popleft()
    for d, n in edges.get(v, {}).items():
        if d in DIR and n not in pos:
            x, y = pos[v][0] + DIR[d][0], pos[v][1] + DIR[d][1]
            pos[n] = (x, y); q.append(n)
try:
    from PIL import Image, ImageDraw, ImageFont
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    cs = 46; mx, my = min(xs), min(ys)
    W = (max(xs) - mx + 2) * cs; H = (max(ys) - my + 2) * cs + 40
    img = Image.new("RGB", (W, H), (250, 250, 247)); dr = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font = ImageFont.load_default()
    P = lambda v: ((pos[v][0] - mx) * cs + cs, (pos[v][1] - my) * cs + cs + 20)
    for v, es in edges.items():
        if v not in pos:
            continue
        for d, n in es.items():
            if n in pos and d in DIR:
                dr.line([P(v), P(n)], fill=(150, 150, 150), width=2)
    for v, p in pos.items():
        x, y = P(v); c = cells.get(v)
        k = len(c.get("mobs", [])) if c else 0
        col = (255, 255, 255) if k == 0 else (255, 224, 170) if k < 3 else (240, 150, 120)
        if v == start:
            col = (170, 210, 255)
        dr.rectangle([x - 18, y - 14, x + 18, y + 14], fill=col, outline=(80, 80, 80))
        dr.text((x - 16, y - 12), str(v)[-3:], fill=(0, 0, 0), font=font)
        dr.text((x - 16, y + 1), ("м%d" % k) if k else "", fill=(120, 0, 0), font=font)
    dr.text((8, 4), "Заливные луга: %d клеток; рамка: голубая=вход, белая=пусто, оранжевая=мобы" % len(pos), fill=(0, 0, 0), font=font)
    img.save(os.path.join(OUT, "map.png"))
    map_ok = True
except Exception as e:
    map_ok = False
    print("карта не построена:", e)

# ---------- botp (V) + csv для бота ----------
M = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}


def vline(frm, cmd):
    return "#if {$MsdpRoomVnum != %d} {#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить};#if {$MsdpRoomVnum == %d} {%s}" % (frm, frm, cmd)


def db_exits(v):
    r = db.execute("select exits from rooms where vnum=?", (str(v),)).fetchone()
    return {k: int(x) for k, x in json.loads(r[0]).items()} if r else {}


# подход ЦП 100009 -> 137220: 11e s w 17s (проверен по графу)
appr = []
v = 100009
for n, d in re.findall(r"(\d*)([nsewud])", "11esw17s"):
    for _ in range(int(n) if n else 1):
        nv = db_exits(v).get(d.upper())
        appr.append((v, d.upper(), nv)); v = nv
lines = [".триг #scr botCore.BotInZone = true"]
for frm, d, to in appr:
    lines.append(vline(frm, M[d]))
BK = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}
seen = {137220}; children = collections.defaultdict(list)
for frm, d, to in S["moves"]:                 # дерево обхода: ходы, которыми впервые нашли клетку
    if to in cells and to not in seen:
        seen.add(to); children[frm].append((d, to))
walk = []


def dfs(v):
    for d, ch in children.get(v, []):
        walk.append((v, d)); dfs(ch); walk.append((ch, BK[d]))


sys.setrecursionlimit(5000)
dfs(137220)
for frm, d in walk:                            # полный обход по дереву с возвратами в 137220
    lines.append(vline(frm, M[d]))
for frm, d, to in reversed(appr):
    back = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}[d]
    lines.append(vline(to, M[back]))
with open(os.path.join(OUT, "луга.botp"), "w", encoding="cp1251", newline="") as f:
    f.write("\r\n".join(lines) + "\r\n")

hdr = ["Имя моба", "Описание в комнате", "Hp", "MaxHp", "Mp", "MaxMp", "Опыт", "Деньги", "Уровень", "Агрессивность", "Ассистит?", "Умения", "Профессия", "Раса", "Флаги NPC"]
name2line = {}
for l, n in line2name.items():
    name2line.setdefault(n, l)
with open(os.path.join(OUT, "луга_mob.csv"), "w", encoding="cp1251", newline="") as f:
    f.write(";".join('"%s"' % h for h in hdr) + "\r\n")
    for lv, nm, cd, e in rows:
        mp = cd["mp"] or "0"
        vals = [nm, name2line.get(nm, ""), cd["hp"], cd["hp"], "%s/%s" % (mp, mp), "%s/%s" % (mp, mp), str(e if e and e > 0 else full_exp(lv)), "0",
                str(lv), "false", "false", cd["skills"] or "-", cd["class"], "", ""]
        f.write(";".join('"%s"' % x for x in vals) + "\r\n")

print("клеток:", len(cells), "| видов мобов:", len(cards), "| с опытом:", sum(1 for v in exp.values() if v and v > 0),
      "| ходов в маршруте:", len(S["moves"]), "| заблокировано:", len(S["blocked"]), "| выходов за зону:", len(S["out_edges"]),
      "| конфликтов описание-имя:", len(conflicts), "| карта:", map_ok)
for l, n in list(conflicts.items())[:10]:
    print("  конфликт:", l[:60], "->", n)
if "--install" in sys.argv:
    dst = os.path.join(BASE, "JMC БОТ АЙЛИНА", "areas")
    for fn in ("луга.botp", "луга_mob.csv"):
        shutil.copy(os.path.join(OUT, fn), os.path.join(dst, fn))
    print("скопировано в", dst)
