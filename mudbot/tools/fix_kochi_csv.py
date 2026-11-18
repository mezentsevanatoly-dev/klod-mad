# -*- coding: utf-8 -*-
"""кочи_mob.csv Айлины (слова пользователя 13.11: «если в группе Айлина, то бить всех; в клетке со старцем писать уб старец»):
добавить старца, вождя, широкоплечих стражей, змеелова; исправить строки комнаты у сына вождя, пожилого пастуха, охотника. Бэкап .bak_kochi."""
import os, csv, io, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); BASE = os.path.dirname(ROOT)
P = os.path.join(BASE, "JMC БОТ АЙЛИНА", "areas", "кочи_mob.csv")
shutil.copy(P, P + ".bak_kochi")
rows = list(csv.reader(open(P, "rb").read().decode("cp1251").splitlines(), delimiter=";", quotechar='"'))
hdr = rows[0]; body = rows[1:]
FIX = {"Сын вождя": "Ослабленный болезнью сын вождя лежит тут. ", "Пожилой пастух": "Пожилой пастух проходит тут. ", "Охотник со шрамом": "Охотник со шрамом на лице, следящий за каждым вашим движением, стоит тут. "}
for r in body:
    if r[0] in FIX:
        r[1] = FIX[r[0]]
have = {(r[0], r[1]) for r in body}
NEW = [
 ("Старец", "Старец в белом плаще стоит тут, перебирая четки. ", 25, "false", "Маг"),                  # холдер: уб старец (HOLDERS)
 ("Вождь кочевников", "Вождь племени стоит перед вами, сложив руки на груди. ", 25, "false", "Воин"),
 ("Широкоплечий страж", "Широкоплечий страж стоит тут, охраняя вход в лагерь. ", 25, "true", "Воин"),
 ("Змеелов", "Змеелов, злобно поглядывающий по сторонам, стоит тут. ", 20, "false", "Следопыт"),
 ("Старый кочевник", "Старый кочевник бредет тут. ", 20, "false", ""),
]
for (n, line, lv, ass, prof) in NEW:
    if (n, line) not in have:
        body.append([n, line, "", "", "", "", "0", "0", str(lv), "false", ass, "", prof, "", ""])
s = io.StringIO(); w = csv.writer(s, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL, lineterminator="\r\n"); w.writerows([hdr] + body)
open(P, "wb").write(s.getvalue().encode("cp1251", "replace"))
print("мобов в кочи_mob.csv:", len(body))
# холдер Старец -> убить по имени (BotCore HOLDERS)
b = os.path.join(BASE, "JMC БОТ АЙЛИНА", "scripts", "BotCore.js")
t = open(b, "rb").read().decode("cp1251")
add = []
for h in ("Старец", "Рыболов", "Проклятая душа повелителя замка"):
    if ('"%s": 1' % h) not in t:
        add.append('"%s": 1' % h)
if add:
    shutil.copy(b, b + ".bak_holders")
    t = t.replace('var HOLDERS = {', 'var HOLDERS = {' + ", ".join(add) + ", ", 1)
    open(b, "wb").write(t.encode("cp1251", "replace")); print("HOLDERS +", add)
