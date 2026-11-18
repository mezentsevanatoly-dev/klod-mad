"""Собрать итог по Храму пламенного меча: csv (cp1251) мобов этого прогона и заметки зоны."""
import csv
import glob
import os
import re
import shutil
import sqlite3

H = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(H)))
cards, kills = {}, {}
for f in sorted(glob.glob(os.path.join(ROOT, "tools", "run_hram*.log"))):
    for l in open(f, encoding="utf-8", errors="replace"):
        m = re.match(r"\s*в БД: (.+?) ур (\d+) (\S+)", l)
        if m:
            cards[m.group(1)] = (int(m.group(2)), m.group(3))
        m = re.match(r"\s*убит (.+?) за [\d.]+ с: опыт (\d+) \[ур (\d+)", l)
        if m:
            kills.setdefault(m.group(1), []).append(int(m.group(2)))
db = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
src = list(csv.reader(open(os.path.join(H, "храм_mob.csv"), encoding="cp1251"), delimiter=";"))
SKIP = {"Кто-то", "Городской страж", "Высокая эльфийка", "Голем"}     # город / не из зоны / не найден в инстансе
rows = [src[0]]
for r in src[1:]:
    if r[0] in SKIP:
        continue
    if r[0] in cards:
        r[8], r[12] = str(cards[r[0]][0]), cards[r[0]][1]
    if r[0] in kills:
        r[6] = str(sum(kills[r[0]]) // len(kills[r[0]]))
    rows.append(r)
rows.append(["Старец", "Старец в балахоне сидит тут. ", "1500", "1500", "1000", "1000", "429233", "1100", "27", "false",
             "false", "украсть душу, истощить жизнь", "Некромант", "человека", ""])
for r in rows:
    if r[0] == "Оживший труп":
        r[6] = "429233"
dst = os.path.join(H, "рр2_ХрамV_mob.csv")
with open(dst, "w", encoding="cp1251", errors="replace", newline="") as f:
    csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL, lineterminator="\r\n").writerows(rows)
# plain-вариант: те же ходы без проверки клеток
plain = []
for l in open(os.path.join(H, "рр2_ХрамV.botp"), encoding="cp1251").read().splitlines():
    m = re.search(r"== \d+\} \{(.*)\}$", l)
    plain.append(m.group(1) if l.startswith("#if") and m else l)
with open(os.path.join(H, "рр2_Храм.botp"), "w", encoding="cp1251", newline="\r\n") as f:
    f.write("\n".join(plain) + "\n")
print(len(rows) - 1, "мобов в csv;", len(plain), "строк plain;", {k: (v[0], len(v)) for k, v in kills.items()})
print({k: v for k, v in cards.items()})
