"""Запись наблюдений охотника в data/game.db: карточки мобов (mob_cards) и опыт за каждое убийство (mob_kills)."""
import os
import re
import sqlite3
import time

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "game.db")


def _c():
    c = sqlite3.connect(DB, timeout=20)
    c.execute("""CREATE TABLE IF NOT EXISTS mob_cards (zone TEXT, name TEXT, level INTEGER, prof TEXT, hp TEXT, mana TEXT, skills TEXT,
                 kind TEXT, desc TEXT, room TEXT, PRIMARY KEY (zone, name))""")
    c.execute("""CREATE TABLE IF NOT EXISTS mob_kills (ts TEXT, zone TEXT, name TEXT, mob_level TEXT, my_level INTEGER, exp INTEGER, secs REAL)""")
    return c


def card(zone, info, lines=()):
    """info: name, level, prof, skills, flags, room; lines — строки карточки из игры (хиты, вид, описание)."""
    if not info.get("name") or not str(info.get("level", "")).isdigit():
        return
    hp = mana = kind = ""
    desc = []
    for l in lines:
        s = l.strip()
        m = re.match(r"^Хиты: (\S+?), мана: (\S+)", s)
        if m:
            hp, mana = m.group(1), m.group(2)
        elif s.startswith("Вы видите перед собой"):
            kind = s.replace("Вы видите перед собой", "").strip(" .")
        elif s and not re.match(r"^(Навыки|Особенности|Хиты):", s) and "[уровень" not in s and not re.match(r"^\d+H ", s) and "состоянии" not in s:
            desc.append(s)
    c = _c()
    c.execute("INSERT OR REPLACE INTO mob_cards VALUES (?,?,?,?,?,?,?,?,?,?)",
              (zone, info["name"], int(info["level"]), info.get("prof", ""), hp, mana, info.get("skills", ""), kind,
               " ".join(desc)[:300], info.get("room", "")))
    c.commit()
    c.close()


def kill(zone, name, mob_level, my_level, exp, secs=0.0):
    c = _c()
    c.execute("INSERT INTO mob_kills VALUES (?,?,?,?,?,?,?)", (time.strftime("%d.%m %H:%M:%S"), zone, name, str(mob_level), my_level, exp or None, secs))   # 0 = строка опыта не успела прийти: NULL, добор из лога
    c.commit()
    c.close()
