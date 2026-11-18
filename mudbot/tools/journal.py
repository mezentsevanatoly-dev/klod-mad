"""Дневник игры (база SQLite): что проверил, что получилось, что решил и почему.

  python tools/journal.py add "<этап>" "<проверка>" "<результат>" "<решение>" "<почему>"
  python tools/journal.py show [N]        последние N записей (по умолчанию 40)
  python tools/journal.py md              выгрузить в data/journal.md
"""
import os
import sqlite3
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "game.db")


def conn():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT, t TEXT, stage TEXT, chk TEXT, result TEXT, decision TEXT, why TEXT)""")
    return c


def add(stage, chk, result, decision, why, t=None):
    c = conn()
    c.execute("INSERT INTO journal (t,stage,chk,result,decision,why) VALUES (?,?,?,?,?,?)",
              (t or time.strftime("%d.%m %H:%M"), stage, chk, result, decision, why))
    c.commit()
    c.close()


def rows(n=40):
    c = conn()
    r = c.execute("SELECT t,stage,chk,result,decision,why FROM journal ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    c.close()
    return r[::-1]


def md():
    c = conn()
    r = c.execute("SELECT t,stage,chk,result,decision,why FROM journal ORDER BY id").fetchall()
    c.close()
    out = ["# Дневник игры", "", "| Время | Этап | Проверка | Результат | Решение | Почему |", "|---|---|---|---|---|---|"]
    for x in r:
        out.append("| " + " | ".join(str(v).replace("|", "/").replace("\n", " ") for v in x) + " |")
    p = os.path.join(HERE, "data", "journal.md")
    open(p, "w", encoding="utf-8").write("\n".join(out) + "\n")
    return p


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    a = sys.argv[1:]
    if a and a[0] == "add" and len(a) == 6:
        add(*a[1:])
    elif a and a[0] == "show":
        for x in rows(int(a[1]) if len(a) > 1 else 40):
            print(" | ".join(x))
    elif a and a[0] == "md":
        print(md())
    else:
        print(__doc__)
