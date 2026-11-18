# -*- coding: utf-8 -*-
"""Готовые зоны оригинального бота (Bot_ZayNew areas / areas 123 / areas 321, БОТ ЧВЫРЛА\\areas): мобы, уровни, опыт для Кимпи.
Опыт за моба = min(цена, потолок уровня). Пишет data/зоны_оригинал_экспа.csv и печатает топ."""
import os, io, sys, csv, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
DIRS = [os.path.join(BASE, "Bot_Inka", "Bot_Inka", "Bot_ZayNew", d) for d in ("areas", "areas 123", "areas 321")] + [r"C:\Users\User\Desktop\мад\БОТ ЧВЫРЛА\areas"]
CAP = {25: 429233}
for l in range(26, 31):
    CAP[l] = int(CAP[l - 1] * 1.75)
PRICE = {17: 4824, 18: 8404, 19: 14698, 20: 25798, 21: 45425, 22: 79211, 23: 138666, 24: 243591, 25: 429233}
for l in range(26, 46):
    PRICE[l] = int(PRICE[l - 1] * 1.75)
def num(x):
    try:
        return int(float(str(x).replace(" ", "")))
    except Exception:
        return 0
seen = {}
for d in DIRS:
    for p in glob.glob(os.path.join(d, "*_mob.csv")):
        z = os.path.basename(p)[:-8]
        try:
            rows = list(csv.reader(open(p, "rb").read().decode("cp1251", "replace").splitlines(), delimiter=";", quotechar='"'))[1:]
        except Exception:
            continue
        mobs = []
        for r in rows:
            if not r or len(r) < 9:
                continue
            lv = num(r[8]); ex = num(r[6])
            if ex == 0 and lv:
                ex = PRICE.get(lv, 0)          # в оригинальных csv опыта нет: цена моба ~ потолок его уровня (по таблице exp_levels.md)
            mobs.append((r[0], lv, ex))
        if not mobs:
            continue
        key = (z, len(mobs))
        if z in seen and seen[z][0] >= len(mobs):
            continue
        seen[z] = (len(mobs), mobs, p)
out = []
for z, (n, mobs, p) in seen.items():
    lv = [m[1] for m in mobs if m[1]]
    row = [z, n, min(lv) if lv else 0, max(lv) if lv else 0]
    for L in (24, 25, 26, 27):
        c = CAP.get(L, 243591)
        row.append(sum(min(m[2], c) for m in mobs if L - 3 <= m[1] <= L + 2))   # бить только мобов в окне [лвл-3, лвл+2]: слабее мало опыта, сильнее опасно
    row.append(p)
    out.append(row)
out.sort(key=lambda r: -r[5])
with open(os.path.join(ROOT, "data", "зоны_оригинал_экспа.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f, delimiter=";"); w.writerow(["зона", "мобов", "лвл мин", "лвл макс", "опыт на 24", "опыт на 25", "опыт на 26", "опыт на 27", "файл"]); w.writerows(out)
print("зон:", len(out))
print("зона | мобов | лвл | Кимпи на 24 | на 25 | на 26 | на 27 (млн за полный проход)")
for r in out[:28]:
    print("%s | %d | %d-%d | %.1f | %.1f | %.1f | %.1f" % (r[0], r[1], r[2], r[3], r[4] / 1e6, r[5] / 1e6, r[6] / 1e6, r[7] / 1e6))
