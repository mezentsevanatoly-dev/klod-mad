"""Карточки мобов из JMC-лога (результат «смотреть <моб>») -> game.db mob_cards, если такой карточки (zone,name) ещё нет.

  python -X utf8 tools/cards_from_log.py <зона_в_базе> [--from HH:MM]
Формат в логе: «Имя [уровень N], Профессия» и ниже «Хиты: a/b, мана: c/d» (необязательно).
"""
import re, sqlite3, sys

LOG = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\claude_game.log"
DB = r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db"
zone = sys.argv[1]
frm = sys.argv[sys.argv.index("--from") + 1] + ":00" if "--from" in sys.argv else "00:00:00"
L = open(LOG, "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
c = sqlite3.connect(DB)
cols = [r[1] for r in c.execute("pragma table_info(mob_cards)")]
n = 0
for i, l in enumerate(L):
    m = re.match(r"^(\d\d:\d\d:\d\d) (.+?) \[уровень (\d+)\], (.+?)\s*$", l)
    if not m or m.group(1) < frm:
        continue
    name, lvl, prof = m.group(2), m.group(3), m.group(4)
    if c.execute("select 1 from mob_cards where zone=? and name=?", (zone, name)).fetchone():
        continue
    hp = mana = None
    for k in range(i + 1, min(i + 6, len(L))):
        h = re.search(r"Хиты: (\d+)/(\d+), мана: (\d+)/(\d+)", L[k])
        if h:
            hp, mana = h.group(2), h.group(4)
            break
    vals = {"zone": zone, "name": name, "level": lvl, "prof": prof, "hp": hp, "mana": mana}
    keys = [k for k in vals if k in cols]
    c.execute("insert into mob_cards(%s) values (%s)" % (",".join(keys), ",".join("?" * len(keys))), [vals[k] for k in keys])
    print("карточка:", name, lvl, prof, hp, mana)
    n += 1
c.commit()
print("добавлено:", n)
