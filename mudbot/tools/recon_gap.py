"""Сверка: какие мобы из лога пользователя (_mob.csv) не убиты Айлиной (game.db, mob_kills при my_level>=25) и какие ходы были закрыты.
python -X utf8 tools/recon_gap.py [лог ...]      таблица по зонам (без аргументов — по всем папкам data/recon)
"""
import csv
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RECON = os.path.join(ROOT, "data", "recon")
db = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
killed = {n.lower() for n, in db.execute("select distinct name from mob_kills where my_level>=25")}
blocked = {}
for l in open(os.path.join(ROOT, "tools", "recon_all.log"), encoding="utf-8", errors="replace"):
    m = re.search(r"=== зона (\S+)", l)
    if m:
        cur = m.group(1)
    b = re.search(r"неудачных ходов \[(.*?)\]", l)
    if b and "cur" in dir():
        blocked[cur] = re.findall(r"\('(\d+)', '(\w)'\)", b.group(1))
for z in sys.argv[1:] or sorted(os.listdir(RECON)):
    p = os.path.join(RECON, z, z + "_mob.csv")
    if z.startswith("_") or not os.path.exists(p):
        continue
    names = [r[0] for r in list(csv.reader(open(p, encoding="cp1251"), delimiter=";"))[1:]]
    miss = [n for n in names if n.lower() not in killed]
    print(f"{z:14} в логе {len(names):3} не убиты {len(miss):3}: {', '.join(miss) or '—'} | закрыто: {blocked.get(z) or '—'}")
