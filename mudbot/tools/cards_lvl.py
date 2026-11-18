"""Все карточки мобов уровня [от, до] из эксплоров и маршрутов: зона, имя, строка, ур., профессия, где стоит (из логов).
python -X utf8 cards_lvl.py 25 30  -> НАЙДЕНО\\мобы 25-30.md"""
import os, sys, re, glob, collections
R = r"C:\Users\User\Desktop\Клод мад"
lo, hi = int(sys.argv[1]), int(sys.argv[2])
cards = {}
for f in glob.glob(os.path.join(R, "JMC БОТ АЙЛИНА", "areas", "эксплор_*_mob.csv")):
    z = os.path.basename(f)[8:-8].replace("_", " ")
    for l in open(f, encoding="cp1251", errors="replace").read().splitlines()[1:]:
        p = [x.strip('"') for x in l.split('";"')]
        if len(p) < 15: continue
        try: lv = int(p[8])
        except ValueError: continue
        if not (lo <= lv <= hi): continue
        if re.search(r"Мирный|Продавец|Банкир|Кузнец|Гостиница|Кладовщик|Учитель", p[14]): continue
        line = p[1].strip().rstrip(".").strip()
        cards.setdefault(line, (z, p[0].strip('"'), line, lv, p[12], p[10]))
# где видела: заголовок комнаты по логам
where = collections.defaultdict(collections.Counter)
for f in glob.glob(os.path.join(R, "JMC БОТ АЙЛИНА", "Logs", "*.log")):
    prev = None; last = ""; title = None; inroom = False
    for raw in open(f, encoding="cp1251", errors="replace"):
        t = raw[9:].rstrip("\n") if re.match(r"\d\d:\d\d:\d\d ", raw) else raw.rstrip("\n")
        if t.startswith("   ") and last and not last.startswith((" ", "[", "#", ">")) and not re.search(r"\d+H \d+M", last) and len(last) < 60:
            prev = last.strip()
        if t.startswith("[ Exits:"): inroom = True; title = prev; last = t; continue
        if re.search(r"\d+H \d+M \d+V", t): inroom = False
        if inroom and title:
            s = t.strip().rstrip(".").strip()
            if s in cards: where[s][title] += 1
        last = t
byz = collections.defaultdict(list)
for line, c in cards.items(): byz[c[0]].append(c)
out = ["# Мобы %d–%d уровня по карточкам эксплора (без мирных/торговцев)" % (lo, hi), "",
       "Источник: `JMC БОТ АЙЛИНА\\areas\\эксплор_*_mob.csv`, места — по логам Айлины. Всего: %d видов в %d зонах." % (len(cards), len(byz)), ""]
for z in sorted(byz, key=lambda z: -len(byz[z])):
    out += ["## %s (%d)" % (z, len(byz[z])), "| Моб | Ур. | Профессия | Ассист | Строка в комнате | Где видела |", "|---|---|---|---|---|---|"]
    for c in sorted(byz[z], key=lambda c: -c[3]):
        w = ", ".join("%s (%d)" % (k, n) for k, n in where[c[2]].most_common(3)) or "—"
        out.append("| %s | %d | %s | %s | %s | %s |" % (c[1], c[3], c[4], c[5], c[2], w))
    out.append("")
open(os.path.join(R, "НАЙДЕНО", "мобы %d-%d.md" % (lo, hi)), "w", encoding="utf-8").write("\n".join(out))
print(len(cards), "видов,", len(byz), "зон:", ", ".join("%s %d" % (z, len(byz[z])) for z in sorted(byz, key=lambda z: -len(byz[z]))))
