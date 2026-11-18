"""Все карты MUD Mapper (.mm2) -> таблица mapper_rooms (zone, tag, x, y, l, name, exits, desc) в data/game.db + сравнение полноты с моими rooms.
  python tools/mapper_import.py
"""
import glob
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
import mm2

DB = os.path.join(HERE, "data", "game.db")


def norm(s):
    return s.lower().replace("ё", "е").replace("-", " ").strip()


def main():
    c = sqlite3.connect(DB)
    c.execute("DROP TABLE IF EXISTS mapper_rooms")
    c.execute("CREATE TABLE mapper_rooms (zone TEXT, tag INTEGER, x INTEGER, y INTEGER, l INTEGER, name TEXT, exits TEXT, descr TEXT)")
    tot = 0
    for f in sorted(glob.glob(os.path.join(mm2.MAPS, "*.mm2"))):
        zone = os.path.splitext(os.path.basename(f))[0]
        n = 0
        for r in mm2.parse(f):
            if r.get("_class") != "TMudRoom2" or "X" not in r:
                continue
            c.execute("INSERT INTO mapper_rooms VALUES (?,?,?,?,?,?,?,?)", (zone, r.get("Tag"), r["X"], r["Y"], r.get("L", 0), r.get("Hint", ""), r.get("Exits", ""), (r.get("Description") or "")[:400]))
            n += 1
        tot += n
    c.commit()
    mine = {}
    for z, n in c.execute("select zone,count(*) from rooms group by zone"):
        mine[norm(z)] = n
    print("клеток мапера:", tot)
    rows = []
    for z, n in c.execute("select zone,count(*) from mapper_rooms group by zone"):
        have = mine.get(norm(z.replace("Мад школа", "Мад-школа")), 0)
        rows.append((z, n, have))
    miss = [r for r in rows if r[2] < r[1]]
    print("зон в мапере:", len(rows), "| у меня полнее или равно:", len(rows) - len(miss), "| у меня неполно/нет:", len(miss))
    for z, n, have in sorted(miss, key=lambda r: r[2] - r[1])[:40]:
        print(f"  {z}: мапер {n}, у меня {have}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
