"""Добрать опыт убийств, который не успел записаться (mob_kills.exp IS NULL), из out.log.
В логе: «<Моб> мертв(а). R.I.P.» -> ближайшая строка «Вы получили N единиц опыта». События идут в том же порядке, что и записи mob_kills,
поэтому сопоставление по имени вперёд по порядку.
  python tools/backfill_exp.py
"""
import os
import re
import sqlite3

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "game.db")
OUT = os.path.join(HERE, "out.log")
DEAD = re.compile(r"^(.+?) (?:мертв[аоы]?)\. R\.I\.P\.")
XP = re.compile(r"Вы получили (\d+) единиц")


def events():
    ev, pending = [], None
    with open(OUT, "rb") as f:
        for raw in f:
            s = raw.decode("utf-8", "replace").strip()
            m = DEAD.match(s)
            if m:
                if pending:
                    ev.append((pending[0], None))
                pending = [m.group(1).lower(), 0]
                continue
            if pending:
                x = XP.search(s)
                if x:
                    ev.append((pending[0], int(x.group(1))))
                    pending = None
                else:
                    pending[1] += 1
                    if pending[1] > 12:                      # строка опыта так и не пришла
                        ev.append((pending[0], None))
                        pending = None
    return ev


def main():
    ev = events()
    c = sqlite3.connect(DB)
    rows = c.execute("select rowid, name, exp from mob_kills order by rowid").fetchall()
    p, fixed = 0, 0
    for rid, name, exp in rows:
        key = (name or "").lower()
        for j in range(p, min(p + 400, len(ev))):
            if ev[j][0] == key:
                if exp is None and ev[j][1]:
                    c.execute("update mob_kills set exp=? where rowid=?", (ev[j][1], rid))
                    fixed += 1
                p = j + 1
                break
    c.commit()
    left = c.execute("select count(*) from mob_kills where exp is null").fetchone()[0]
    print(f"событий в логе: {len(ev)}; добрано: {fixed}; осталось без опыта: {left}")


if __name__ == "__main__":
    main()
