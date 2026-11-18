"""Мобы и опыт из JMC-лога пользователя -> game.db (mob_cards, mob_kills) без обхода зоны.
  python tools/log_to_db.py <лог> "<Зона>" [уровень_пользователя]
Карточка: «Имя [уровень N], Профа» + «Хиты: a/b, мана: c/d» + «Навыки: …». Убийство: «<Имя> мертв(а). R.I.P.» -> ближайшее «Вы получили N единиц опыта».
Существующие карточки не трогаем (INSERT OR IGNORE).
"""
import os
import re
import sqlite3
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JMC = os.path.join(os.path.dirname(HERE), "JMC")
DB = os.path.join(HERE, "data", "game.db")
CARD = re.compile(r"^(.+?) \[уровень (\d+)\](?:, (.+))?$")
DEAD = re.compile(r"^(.+?) (?:мертв[аоы]?)\. R\.I\.P\.")
XP = re.compile(r"Вы получили (\d+) единиц")


def main(name, zone, my_level=0):
    L = [l.rstrip("\r").strip() for l in open(os.path.join(JMC, name), "rb").read().decode("cp1251", "replace").split("\n")]
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS mob_cards (zone TEXT, name TEXT, level INTEGER, prof TEXT, hp TEXT, mana TEXT, skills TEXT, kind TEXT, desc TEXT, room TEXT, PRIMARY KEY (zone, name))")
    cards = {}
    for i, s in enumerate(L):
        m = CARD.match(s)
        if not m or len(s) > 70:
            continue
        nm, lv, prof = m.group(1), int(m.group(2)), m.group(3) or ""
        hp = mana = skills = ""
        for k in range(i + 1, min(i + 6, len(L))):
            h = re.match(r"^Хиты: (\S+?), мана: (\S+)", L[k])
            if h:
                hp, mana = h.group(1), h.group(2)
            if L[k].startswith("Навыки:"):
                skills = L[k].split(":", 1)[1].strip()
        if nm.lower() not in cards:
            cards[nm.lower()] = (nm, lv, prof, hp, mana, skills)
    n_cards = 0
    for nm, lv, prof, hp, mana, skills in cards.values():
        cur = c.execute("INSERT OR IGNORE INTO mob_cards (zone,name,level,prof,hp,mana,skills,kind,desc,room) VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (zone, nm, lv, prof, hp, mana, skills, "", "", "из лога " + name))
        n_cards += cur.rowcount
    n_kills, seen_ts = 0, time.strftime("%d.%m %H:%M:%S")
    for i, s in enumerate(L):
        m = DEAD.match(s)
        if not m:
            continue
        nm = m.group(1).strip()
        key = nm.lower()
        card = cards.get(key) or next((v for k, v in cards.items() if k.endswith(key) or key.endswith(k)), None)
        xp = None
        for k in range(i + 1, min(i + 8, len(L))):
            x = XP.search(L[k])
            if x:
                xp = int(x.group(1))
                break
        c.execute("INSERT INTO mob_kills (ts,zone,name,mob_level,my_level,exp,secs) VALUES (?,?,?,?,?,?,?)",
                  (seen_ts + " (лог " + name + ")", zone, card[0] if card else nm, str(card[1]) if card else "", my_level, xp, 0))
        n_kills += 1
    c.commit()
    print(f"карточек в логе: {len(cards)}, добавлено новых: {n_cards}; убийств из лога: {n_kills}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
