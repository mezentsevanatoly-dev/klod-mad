# -*- coding: utf-8 -*-
"""Описания мобов («Описание в комнате») для areas/<зона>_mob.csv Айлины - только из реальных строк мобов в комнате:
строки сразу после «[ Exits: ... ]» до строки состояния/пустой. Источники: claude_game.log обеих жаб, Logs\\*, логи пользователя JMC\\*.
Для моба берётся самая частая строка, где встречается его имя (или основа имени). Чинятся только мобы с плохим описанием
(одно на разных / похоже на бой / пустое / нет в логах). python tools/fix_desc_v2.py <зона> [--apply]  (бэкап .bak_desc2)"""
import os, re, io, sys, csv, glob, shutil, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
A = os.path.join(BASE, "JMC БОТ АЙЛИНА", "areas")
BAD = re.compile(r"R\.I\.P|попытал|промах|ударил|рубанул|приготовил|оглушен|произнес|прибежал|прилетел|пришел|пришла|ушел|ушла|убежал|улетел|выполнено|^Вы |состоянии|ранен|умирает|сказал|исчез|встал|выбыл|Труп |лежит тут|глаза сузились")
PROMPT = re.compile(r"\d+H \d+M \d+V|^\d+H|Вых:|^>>|^##")
MOBLINES = collections.Counter()
srcs = [os.path.join(BASE, j, "claude_game.log") for j in ("JMC БОТ АЙЛИНА", "JMC БОТ ИНКА")]
for j in ("JMC БОТ АЙЛИНА", "JMC БОТ ИНКА"):
    srcs += glob.glob(os.path.join(BASE, j, "Logs", "*"))
srcs += [p for p in glob.glob(os.path.join(BASE, "JMC", "*")) if os.path.isfile(p) and "." not in os.path.basename(p)]
for p in srcs:
    try:
        L = open(p, "rb").read().decode("cp1251", "replace").splitlines()
    except OSError:
        continue
    on = False
    for s in L:
        t = re.sub(r"^\[?\d\d:\d\d:\d\d\]? ?", "", s).strip()
        if t.startswith("[ Exits:"):
            on = True; continue
        if on:
            if not t or PROMPT.search(t):
                on = False; continue
            if t.startswith("[Зона") or t.startswith("*"):
                continue
            t = re.sub(r"\s*\.\.\.\S.*$", "", t).strip()        # хвост аффектов «...освящение» бот отрезает
            t = re.sub(r"\s*\[\d+\]$", "", t).strip()             # «[2]» - число одинаковых
            if 8 < len(t) < 160 and not BAD.search(t):
                MOBLINES[t] += 1


def stem(w):
    w = w.lower().replace("ё", "е")
    return w[:max(4, len(w) - 2)]


def cands(name):
    words = [w for w in re.split(r"[\s]+", name) if len(w) >= 3]
    out = []
    for t, c in MOBLINES.items():
        tl = t.lower().replace("ё", "е")
        if name.lower().replace("ё", "е") in tl:
            out.append((c * 10, t))                     # точное имя - сильнее
        elif words and all(stem(w) in tl for w in words):
            out.append((c, t))
    return sorted(out, reverse=True)


zone = sys.argv[1]; apply = "--apply" in sys.argv
# ручные поправки там, где по основе имени находится чужой моб (городской монах вместо храмового) или строка боя
OVERRIDE = {("храм", "Монах"): "Занятый заучиванием псалмов монах проходит тут.",
            ("геоканал3", "Кобольд-жрец"): ""}
p = os.path.join(A, zone + "_mob.csv")
rows = list(csv.reader(open(p, "rb").read().decode("cp1251").splitlines(), delimiter=";", quotechar='"'))
hdr, body = rows[0], [r for r in rows[1:] if r]
by = collections.defaultdict(set)
for r in body:
    by[r[1].strip()].add(r[0].strip())
fixed = 0
for r in body:
    nm, d = r[0].strip(), r[1].strip()
    if nm in ("Вы", "", "Кто-то"):        # «Кто-то» = невидимый моб, строки в комнате у него нет
        continue
    if (zone, nm) in OVERRIDE:
        r[1] = OVERRIDE[(zone, nm)] + (" " if OVERRIDE[(zone, nm)] else ""); fixed += 1
        print("%-22s было: %-50s -> (вручную) %s" % (nm, d[:50], OVERRIDE[(zone, nm)] or "очищено"))
        continue
    badness = (not d) or len(by[d]) > 1 or bool(BAD.search(d)) or d not in MOBLINES
    if not badness:
        continue
    c = [x for x in cands(nm) if x[1] not in {rr[1].strip() for rr in body if rr[0].strip() != nm and rr[1].strip() not in ("",) and len(by[rr[1].strip()]) == 1 and not BAD.search(rr[1])}]
    if c:
        print("%-22s было: %-50s -> %s  (x%d)" % (nm, d[:50], c[0][1], c[0][0]))
        r[1] = c[0][1] + " "; fixed += 1
    else:
        if BAD.search(d):          # чужая строка (бой, свой аффект) хуже пустой: бот примет её за моба
            r[1] = ""; fixed += 1
            print("%-22s было: %-50s -> НЕ НАШЛА, описание очищено (было чужое)" % (nm, d[:50]))
        else:
            print("%-22s было: %-50s -> НЕ НАШЛА строку в логах, оставила" % (nm, d[:50]))
body = [r for r in body if r[0].strip() != "Вы"]
print("исправлено:", fixed)
if apply and fixed:
    shutil.copy(p, p + ".bak_desc2")
    s = io.StringIO(); w = csv.writer(s, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL, lineterminator="\r\n"); w.writerows([hdr] + body)
    open(p, "wb").write(s.getvalue().encode("cp1251", "replace"))
    print("записано", p)
