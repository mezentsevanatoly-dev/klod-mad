"""Список мобов зоны из логов осмотра бота (строки «осмотрен: Имя ур N (Профессия)») -> таблица mob_zone в data/game.db.

  python tools/school_mobs.py "Мад школа" tools/run_school*.log
"""
import glob
import os
import re
import sqlite3
import sys
from collections import Counter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "game.db")
INSP = re.compile(r"^\s*осмотрен: (.+?) ур (\d+|\?) \((.*)\)\s*$")
KILL = re.compile(r"^\s*убит (.+?) \(ур [^)]*\) за [\d.]+ с: опыт (\d+)")


def main(zone, patterns):
    seen, kills, exp = {}, Counter(), Counter()
    for pat in patterns:
        for f in glob.glob(pat):
            for l in open(f, encoding="utf-8", errors="replace"):
                m = INSP.match(l)
                if m and m.group(2) != "?":
                    seen[m.group(1)] = (m.group(2), m.group(3))
                k = KILL.match(l)
                if k:
                    kills[k.group(1)] += 1
                    exp[k.group(1)] += int(k.group(2))
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS mob_zone (zone TEXT, name TEXT, level TEXT, prof TEXT, role TEXT, kills INTEGER, exp_total INTEGER,
                 PRIMARY KEY (zone, name))""")
    for name, (lv, prof) in sorted(seen.items()):
        role = "квестер, мирный, не бить" if "учител" in name.lower() else "бить"
        c.execute("INSERT OR REPLACE INTO mob_zone VALUES (?,?,?,?,?,?,?)", (zone, name, lv, prof, role, kills[name], exp[name]))
    c.commit()
    for r in c.execute("SELECT name, level, prof, role, kills, exp_total FROM mob_zone WHERE zone=? ORDER BY level, name", (zone,)):
        print(" | ".join(str(x) for x in r))
    c.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], sys.argv[2:])
