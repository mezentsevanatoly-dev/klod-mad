# -*- coding: utf-8 -*-
"""Итоги эксплора зоны (zone_explore.py): python -X utf8 tools/zone_report.py кочи [--install]
Читает data/recon/<зона>_айлина/explore.json, пересчитывает пары «строка в комнате -> имя» (без подсказок «[Зона…]», общие строки по словам имени),
пишет туда же: mobs.md, cells.csv, map.png, <зона>.botp (V: склад -> подход -> область -> обход всех клеток -> назад) и <зона>_mob.csv (без NOKILL).
--install: копирует botp/csv в JMC БОТ ИНКА\\areas."""
import os, re, sys, json, csv, collections, shutil

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ZN = sys.argv[1] if len(sys.argv) > 1 else "кочи"
CFG = {"кочи": {"botp": "кочи.botp", "root": 111041, "root_dir": "S", "nokill": r"страж|вождь|старец", "area_line": ".триг обл с ю"}}
C = CFG[ZN]
OUT = os.path.join(BASE, "mudbot", "data", "recon", ZN + "_айлина")
S = json.load(open(os.path.join(OUT, "explore.json"), encoding="utf-8"))
cells = {int(k): v for k, v in S["cells"].items()}
cards, exp = S["cards"], S["exp"]
ENTRY = C["root"]
CAP = {12: 297, 13: 517, 14: 902, 15: 1582, 16: 2782, 17: 4824, 18: 8404, 19: 14698, 20: 25798, 21: 45425, 22: 79211, 23: 138666, 24: 243591, 25: 429233, 26: 567765}
BK = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}
M = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
OPP = {"север": "юг", "юг": "север", "восток": "запад", "запад": "восток", "вверх": "вниз", "вниз": "вверх"}


def short(l):
    return re.sub(r"\s*\.\.\..*$", "", l).strip() + " "


def full_exp(lv):
    return CAP.get(min(lv + 2, 26), 0)


def stem_hit(name, line):
    ws = [w[:5].lower() for w in re.findall(r"[А-Яа-яЁё]+", name) if len(w) > 3]
    return sum(1 for w in ws if w in line.lower())


# --- пары строка -> имя
cnt = collections.defaultdict(collections.Counter)
for vn, c in cells.items():
    ents = [l for l in c.get("mobs_lines", []) if not l.startswith("[")]
    nm = c.get("mobs", [])
    if len(ents) == len(nm):
        for l, n in zip(ents, nm):
            cnt[short(l)][n] += 1
main = {}
for l, c in cnt.items():
    cand = list(c)
    if len(cand) > 1:
        sc = sorted(((stem_hit(n, l), n) for n in cand), reverse=True)
        if sc[0][0] > 0 and sc[0][0] > sc[1][0]:
            main[l] = sc[0][1]; continue
    main[l] = c.most_common(1)[0][0]
for vn, c in cells.items():
    ents = [short(l) for l in c.get("mobs_lines", []) if not l.startswith("[")]
    nm = list(c.get("mobs", []))
    if len(ents) == len(nm):
        continue
    e2, n2 = list(ents), list(nm)
    for l in list(e2):
        n = main.get(l)
        if n in n2:
            n2.remove(n); e2.remove(l)
    if len(e2) == 1 and len(n2) == 1 and e2[0] not in main:
        main[e2[0]] = n2[0]
allines = {short(l) for c in cells.values() for l in c.get("mobs_lines", []) if not l.startswith("[")}
for n in cards:
    if n in set(main.values()):
        continue
    cand = [l for l in allines if l not in main and stem_hit(n, l) >= 2]
    if len(cand) == 1:
        main[cand[0]] = n
conflicts = {l: sorted(c) for l, c in cnt.items() if len(c) > 1 and not any(stem_hit(n, l) for n in c)}
name2line = {}
for l, n in main.items():
    name2line.setdefault(n, l)

# --- мобы
cells_of = collections.defaultdict(set)
for vn, c in cells.items():
    for n in c.get("mobs", []):
        cells_of[n].add(vn)
rows = sorted(((cd["level"], nm, cd, exp.get(nm)) for nm, cd in cards.items()), key=lambda r: (r[0], r[1]))
with open(os.path.join(OUT, "mobs.md"), "w", encoding="utf-8") as f:
    f.write("# %s: мобы (эксплор Айлиной, ДК 26)\n\nОпыт «Айлина» — реально полученный за одно убийство (26 лвл); «-» не убивали (по правилу или не засчитался). «Полный» — потолок за моба для персонажа на 2 уровня выше моба.\n\n" % ZN)
    f.write("| Ур | Имя | Профа | Хиты | Навыки | Вид | Клеток | Опыт Айлина | Полный |\n|---|---|---|---|---|---|---|---|---|\n")
    for lv, nm, cd, e in rows:
        f.write("| %d | %s | %s | %s | %s | %s | %d | %s | %d |\n" % (lv, nm, cd["class"], cd["hp"], cd["skills"] or "-", cd["kind"], len(cells_of.get(nm, ())), ("%d" % e) if e and e > 0 else "-", full_exp(lv)))
    f.write("\n## Описания\n\n")
    for lv, nm, cd, e in rows:
        f.write("**%s** (ур %d, %s): %s\n\n" % (nm, lv, cd["class"], cd["desc"]))
    f.write("\n## Строка в комнате -> имя\n\n")
    for l, n in sorted(main.items(), key=lambda x: x[1]):
        f.write("- %s -> **%s**\n" % (l.strip(), n))
with open(os.path.join(OUT, "cells.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["vnum", "название", "выходы", "мобы", "описание"])
    for vn in sorted(cells):
        c = cells[vn]; w.writerow([vn, c["name"], "".join(c["exits"]), ", ".join(c.get("mobs", [])), c["desc"]])

# --- карта
DIR = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
edges = collections.defaultdict(dict)
for vn, c in cells.items():
    for d, n in c.get("edges", {}).items():
        edges[vn][d] = n; edges[n].setdefault(BK[d], vn)
for frm, d, to in S["moves"]:
    if frm and to and frm != to and d in BK:
        edges[frm].setdefault(d, to); edges[to].setdefault(BK[d], frm)
start = ENTRY if ENTRY in edges else min(cells)
pos = {start: (0, 0)}; q = collections.deque([start])
while q:
    v = q.popleft()
    for d, n in edges.get(v, {}).items():
        if d in DIR and n not in pos:
            pos[n] = (pos[v][0] + DIR[d][0], pos[v][1] + DIR[d][1]); q.append(n)
map_ok = False
try:
    from PIL import Image, ImageDraw, ImageFont
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    cs = 50; mx, my = min(xs), min(ys)
    img = Image.new("RGB", ((max(xs) - mx + 2) * cs, (max(ys) - my + 2) * cs + 40), (250, 250, 247)); dr = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 11)
    except Exception:
        font = ImageFont.load_default()
    P = lambda v: ((pos[v][0] - mx) * cs + cs, (pos[v][1] - my) * cs + cs + 20)
    for v, es in edges.items():
        for d, n in es.items():
            if v in pos and n in pos and d in DIR:
                dr.line([P(v), P(n)], fill=(150, 150, 150), width=2)
    for v in pos:
        x, y = P(v); c = cells.get(v); k = len(c.get("mobs", [])) if c else 0
        col = (255, 255, 255) if k == 0 else (255, 224, 170) if k < 3 else (240, 150, 120)
        if v == start:
            col = (170, 210, 255)
        dr.rectangle([x - 20, y - 15, x + 20, y + 15], fill=col, outline=(80, 80, 80))
        dr.text((x - 18, y - 13), str(v)[-3:], fill=(0, 0, 0), font=font)
        if c:
            dr.text((x - 18, y + 1), ("м%d" % k) if k else "", fill=(120, 0, 0), font=font)
    dr.text((8, 4), "%s: %d клеток в зоне (голубая — вход, оранжевые — мобы)" % (ZN, len(cells)), fill=(0, 0, 0), font=font)
    img.save(os.path.join(OUT, "map.png")); map_ok = True
except Exception as e:
    print("карта не построена:", e)

# --- botp
enc = "cp1251"
old = open(os.path.join(BASE, "JMC БОТ ИНКА", "areas", C["botp"]), encoding=enc).read().splitlines()
steps = []
for s in old:
    if s.startswith(".триг обл"):
        break
    m = re.search(r"MsdpRoomVnum == (\d+)\} \{([^{}]*)\}\s*$", s)
    if m:
        steps.append((int(m.group(1)), m.group(2)))


def vline(frm, cmd):
    return "#if {$MsdpRoomVnum != %d} {#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить};#if {$MsdpRoomVnum == %d} {%s}" % (frm, frm, cmd)


seen = {ENTRY}; children = collections.defaultdict(list)
for frm, d, to in S["moves"]:
    if (to in cells or to == ENTRY) and to not in seen:
        seen.add(to); children[frm].append((d, to))
walk = []
sys.setrecursionlimit(5000)


def dfs(v):
    for d, ch in children.get(v, []):
        walk.append((v, d)); dfs(ch); walk.append((ch, BK[d]))


dfs(ENTRY)
lines = [".триг #scr botCore.BotInZone = false"]
for frm, c in steps:
    lines.append(vline(frm, c))
lines += [C["area_line"], ".триг #scr botCore.BotInZone = true"]
for frm, d in walk:
    lines.append(vline(frm, M[d]))
lines.append(".триг #scr botCore.BotInZone = false")
dests = [steps[i + 1][0] if i + 1 < len(steps) else ENTRY for i in range(len(steps))]
for i in range(len(steps) - 1, -1, -1):
    lines.append(vline(dests[i], OPP[steps[i][1]]))
with open(os.path.join(OUT, ZN + ".botp"), "w", encoding=enc, newline="") as f:
    f.write("\r\n".join(lines) + "\r\n")

# --- csv (без NOKILL)
hdr = ["Имя моба", "Описание в комнате", "Hp", "MaxHp", "Mp", "MaxMp", "Опыт", "Деньги", "Уровень", "Агрессивность", "Ассистит?", "Умения", "Профессия", "Раса", "Флаги NPC"]
skipped = []
with open(os.path.join(OUT, ZN + "_mob.csv"), "w", encoding=enc, newline="") as f:
    f.write(";".join('"%s"' % h for h in hdr) + "\r\n")
    for lv, nm, cd, e in rows:
        if re.search(C["nokill"], nm, re.I) or not name2line.get(nm):
            skipped.append(nm); continue
        mp = cd["mp"] or "0"
        vals = [nm, name2line[nm], cd["hp"], cd["hp"], "%s/%s" % (mp, mp), "%s/%s" % (mp, mp), str(full_exp(lv)), "0", str(lv), "false", "false", cd["skills"] or "-", cd["class"], "", ""]
        f.write(";".join('"%s"' % x for x in vals) + "\r\n")
print("%s: клеток %d | видов %d | с опытом %d | ходов %d | заблокировано %d | выходов за зону %d | конфликтов строк %d | карта %s | botp %d строк | в csv не вошли: %s"
      % (ZN, len(cells), len(cards), sum(1 for v in exp.values() if v and v > 0), len(S["moves"]), len(S["blocked"]), len(S["out_edges"]), len(conflicts), map_ok, len(lines), skipped))
if "--install" in sys.argv:
    dst = os.path.join(BASE, "JMC БОТ ИНКА", "areas")
    for fn in (ZN + ".botp", ZN + "_mob.csv"):
        shutil.copy(os.path.join(OUT, fn), os.path.join(dst, fn))
    print("скопировано в", dst, "(старые кочи.botp/кочи_mob.csv заменены)")
