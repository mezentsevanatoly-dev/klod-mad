"""База слов-целей: для каждого моба зоны — имя, слово, на которое он отзывается (`см паучок`, а не `см быстрый`), и строки комнаты, в которых он виден.

  python tools/mob_words_db.py "Мад школа"
Таблицы game.db: mob_zone.word (слово цели), mob_lines(zone, line, name, word) — строки вида «Быстрый паучок скользит … паутинке.»
"""
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "game.db")
OUT = os.path.join(HERE, "out.log")
SKIP_WORDS = ("с", "в", "и", "на")


def word_of(name):
    return [w for w in name.lower().split() if w not in SKIP_WORDS][-1]


def main(zone):
    c = sqlite3.connect(DB)
    cols = [r[1] for r in c.execute("PRAGMA table_info(mob_zone)")]
    if "word" not in cols:
        c.execute("ALTER TABLE mob_zone ADD COLUMN word TEXT")
    c.execute("CREATE TABLE IF NOT EXISTS mob_lines (zone TEXT, line TEXT, name TEXT, word TEXT, PRIMARY KEY (zone, line))")
    names = [r[0] for r in c.execute("SELECT name FROM mob_zone WHERE zone=? AND role='бить'", (zone,))]
    for n in names:
        c.execute("UPDATE mob_zone SET word=? WHERE zone=? AND name=?", (word_of(n), zone, n))
    text = open(OUT, encoding="utf-8", errors="replace").read()[-6_000_000:]
    seen = set()
    for l in text.split("\n"):
        s = l.strip()
        if not s or len(s) > 140 or s.startswith(("Труп", "Вы ", "[", ">", "<")) or re.match(r"^\d+H ", s):
            continue
        low = s.lower()
        for n in sorted(names, key=len, reverse=True):
            if re.search(r"(?<![а-яё])" + re.escape(n.lower()) + r"(?![а-яё])", low):
                s2 = re.sub(r"\.?\(летит\)$", "", s).strip()
                if s2 not in seen and (s2.endswith((".", "!")) or "тут" in s2):
                    seen.add(s2)
                    c.execute("INSERT OR IGNORE INTO mob_lines VALUES (?,?,?,?)", (zone, s2, n, word_of(n)))
                break
    c.commit()
    print("слова-цели:")
    for r in c.execute("SELECT name, word, level FROM mob_zone WHERE zone=? ORDER BY name", (zone,)):
        print("  ", " | ".join(str(x) for x in r))
    print("строк комнаты в базе:", c.execute("SELECT count(*) FROM mob_lines WHERE zone=?", (zone,)).fetchone()[0])
    for r in c.execute("SELECT line, word FROM mob_lines WHERE zone=? ORDER BY word LIMIT 40", (zone,)):
        print("  ", r[1], "<-", r[0][:90])
    c.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1])
