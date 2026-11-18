# -*- coding: utf-8 -*-
"""24плюс (Геолант 24+, слова пользователя: «оббегаешь весь город, убивая стражей»): бой включён с первой клетки, в списке убраны строки-дубли,
добавлены строки стражей из логов. Бэкапы .bak_city24."""
import os, csv, io, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
A = os.path.join(BASE, "JMC БОТ АЙЛИНА", "areas")
p = os.path.join(A, "24плюс.botp"); shutil.copy(p, p + ".bak_city24")
L = open(p, "rb").read().decode("cp1251").splitlines()
if L and "BotInZone = false" in L[0]:
    L[0] = ".триг #scr botCore.BotInZone = true"
open(p, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251", "replace"))
c = os.path.join(A, "24плюс_mob.csv"); shutil.copy(c, c + ".bak_city24")
rows = list(csv.reader(open(c, "rb").read().decode("cp1251").splitlines(), delimiter=";", quotechar='"'))
hdr, body = rows[0], rows[1:]
BAD = ("Молодой парень рассматривает", "попытался", "Кто-то")
body = [r for r in body if not any(b in r[1] or b == r[0] for b in BAD)]
seen = {}
for r in body:
    seen[r[1]] = r
body = list(seen.values())
for r in body:
    if r[0] == "Стражник":
        r[1] = "Стражник в парадной лилово-желтой ливрее стоит здесь. "
have = {r[1] for r in body}
for n, line, lv in (("Городской стражник", "Городской стражник следит за порядком в городе. ", 25), ("Городской страж", "Городской страж присматривает за порядком в городе. ", 25)):
    if line not in have:
        body.append([n, line, "1152", "1152", "", "", "243591", "0", str(lv), "false", "true", "", "Воин", "", ""])
s = io.StringIO(); w = csv.writer(s, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL, lineterminator="\r\n"); w.writerows([hdr] + body)
open(c, "wb").write(s.getvalue().encode("cp1251", "replace"))
print("мобов в 24плюс_mob.csv:", len(body))
for r in body:
    print("  ", r[0], "|", r[1][:60])
