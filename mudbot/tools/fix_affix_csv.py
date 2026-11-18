# -*- coding: utf-8 -*-
"""Убрать из колонки «Описание в комнате» хвосты-аффекты (' ...освящение', ' ...светящийся шарик', '(летит)'): бот режет всё после точки до сравнения. Бэкап .bak_affix."""
import os, re, csv, io, glob, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
for j in ("JMC БОТ АЙЛИНА", "JMC БОТ ИНКА"):
    tot = 0
    for p in sorted(glob.glob(os.path.join(BASE, j, "areas", "*_mob.csv"))):
        txt = open(p, "rb").read().decode("cp1251", "replace")
        rows = list(csv.reader(txt.splitlines(), delimiter=";", quotechar='"'))
        ch = []
        for r in rows[1:]:
            if len(r) > 1:
                new = re.sub(r"\s*\.\.\..*$", "", r[1]).rstrip()
                new = re.sub(r"\s*\((?:летит|невидим|невидима)\)\s*$", "", new)
                if new and not new.endswith(".") and r[1].strip().endswith(("освящение", "шарик", "аура")):
                    new += "."
                new = new + " "
                if new != r[1]:
                    ch.append((r[0], r[1], new)); r[1] = new
        if ch:
            shutil.copy(p, p + ".bak_affix")
            s = io.StringIO(); w = csv.writer(s, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL, lineterminator="\r\n"); w.writerows(rows)
            open(p, "wb").write(s.getvalue().encode("cp1251", "replace")); tot += len(ch)
            print(j[4:], os.path.basename(p), ":", "; ".join("%s" % c[0] for c in ch))
    print(j, "исправлено строк:", tot)
