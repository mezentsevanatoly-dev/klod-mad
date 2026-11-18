"""Справка игры (data/help/*.txt, 461 статья) -> таблица help в data/game.db с поиском.

  python tools/help_to_db.py                  загрузить/обновить
  python tools/help_to_db.py q "градация"     поиск по названию и тексту (первые 15 статей, с фрагментом)
"""
import glob
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "game.db")


def load():
    c = sqlite3.connect(DB)
    c.execute("DROP TABLE IF EXISTS help")
    c.execute("CREATE TABLE help (topic TEXT PRIMARY KEY, aliases TEXT, text TEXT)")
    n = 0
    for f in glob.glob(os.path.join(HERE, "data", "help", "*.txt")):
        t = open(f, encoding="utf-8", errors="replace").read()
        topic = os.path.splitext(os.path.basename(f))[0]
        first = t.split("\n", 1)[0]
        c.execute("INSERT OR REPLACE INTO help VALUES (?,?,?)", (topic, first, t))
        n += 1
    c.commit()
    c.close()
    return n


def query(q):
    c = sqlite3.connect(DB)
    like = f"%{q.lower()}%"
    rows = c.execute("SELECT topic, aliases, text FROM help WHERE lower(topic) LIKE ? OR lower(aliases) LIKE ? OR lower(text) LIKE ? "
                     "ORDER BY (lower(topic) LIKE ?) DESC, (lower(aliases) LIKE ?) DESC LIMIT 15", (like, like, like, like, like)).fetchall()
    for topic, aliases, text in rows:
        i = text.lower().find(q.lower())
        snip = re.sub(r"\s+", " ", text[max(0, i - 80): i + 200]) if i >= 0 else ""
        print(f"== {topic}: {aliases[:80]}\n   ...{snip}")
    print(f"найдено статей: {len(rows)}")
    c.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 2 and sys.argv[1] == "q":
        query(sys.argv[2])
    else:
        print("статей загружено:", load())
