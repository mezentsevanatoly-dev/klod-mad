# -*- coding: utf-8 -*-
"""Проставить колонку «Ассистит?» = true в *_mob.csv зон Айлины по словарю ассист-мобов (data/ассист_мобы.csv + названное пользователем).
Бэкап рядом (*.bak_assist). Остальное в csv не меняется. python -X utf8 tools/apply_assist.py [папка areas]"""
import os, re, sys, csv, glob, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
AREAS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "JMC БОТ АЙЛИНА", "areas")
names = set()
for r in csv.reader(open(os.path.join(ROOT, "data", "ассист_мобы.csv"), encoding="utf-8-sig"), delimiter=";"):
    if r and r[0] != "моб-ассист" and len(r) > 1 and r[1].isdigit() and int(r[1]) >= 3:
        names.add(r[0].strip().lower())
MANUAL = re.compile(r"управляющ|охранник склада|дюжий охранник|страж каземата|капитан эльфийск|городской страж|стражник|начальник городской стражи|охранник банка|охранники банка|облако испарений|сеятель чумы|зловонн\w+ порождение|больной старик|зараженный лучник|беглец|старый ворон|кантор", re.I)
tot = 0
for p in sorted(glob.glob(os.path.join(AREAS, "*_mob.csv"))):
    raw = open(p, "rb").read()
    try:
        txt = raw.decode("cp1251")
    except UnicodeDecodeError:
        continue
    rows = list(csv.reader(txt.splitlines(), delimiter=";", quotechar='"'))
    if not rows or len(rows[0]) < 11 or "Ассист" not in rows[0][10]:
        continue
    ch = []
    for r in rows[1:]:
        if len(r) < 11:
            continue
        n = r[0].strip().lower()
        if (n in names or MANUAL.search(r[0])) and r[10].lower() != "true":
            r[10] = "true"; ch.append(r[0])
    if ch:
        shutil.copy(p, p + ".bak_assist")
        with open(p, "wb") as f:
            import io
            s = io.StringIO(); w = csv.writer(s, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL, lineterminator="\r\n"); w.writerows(rows)
            f.write(s.getvalue().encode("cp1251", "replace"))
        tot += len(ch); print(os.path.basename(p), "->", ", ".join(ch))
print("всего помечено:", tot, "| словарь:", len(names), "имён")
