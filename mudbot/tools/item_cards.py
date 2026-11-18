"""Карточка предмета (ответ игры на `характеристики`/`кск х`/`биржа х`/`осм`) -> таблица item_cards в data/game.db.

Хранится ВСЁ: разобранные поля и сырой текст карточки (raw), чтобы ничего не потерять и можно было перепарсить.
  save_card(conn, text, place="", vnum="", price=None, source="")
Ключ: (name, place, source).
"""
import re

SCHEMA = """CREATE TABLE IF NOT EXISTS item_cards (
    name TEXT, type TEXT, slot TEXT, requires TEXT, weight TEXT, timer TEXT, material TEXT,
    flags TEXT, weapon_flags TEXT, forbid TEXT, weapon_skill TEXT, damage TEXT,
    ac TEXT, armor_cut TEXT, armor_crush TEXT, armor_pierce TEXT, mods TEXT, affects TEXT,
    charges TEXT, spell TEXT, rating TEXT, place TEXT, vnum TEXT, price INTEGER, source TEXT, raw TEXT,
    PRIMARY KEY (name, place, source))"""
RATE_COLS = re.compile(r"^\s*(Вн\s+Ва.*)$")


def parse(text):
    d = {k: "" for k in ("name", "type", "slot", "requires", "weight", "timer", "material", "flags", "weapon_flags", "forbid",
                         "weapon_skill", "damage", "ac", "armor_cut", "armor_crush", "armor_pierce", "charges", "spell", "rating")}
    mods, affects = [], []
    section = None
    heads = None
    for l in text.split("\n"):
        s = l.strip()
        if not s or re.match(r"^\d+H \d+M|^<<|^\[cur\]|^>>>", s):
            if re.match(r"^\d+H \d+M|^<<", s):
                break
            continue
        m = re.match(r"^Предмет '(.+?)', Тип предмета: (.+)$", s)
        if m:
            d["name"], d["type"] = m.group(1), m.group(2)
            continue
        if RATE_COLS.match(l):
            heads = s.split()
            continue
        if s.startswith("Оценка:") and heads:
            vals = [x.strip() for x in s.split(":", 1)[1].split(",")]
            d["rating"] = " ".join(f"{h}={v}" for h, v in zip(heads, vals))
            continue
        if s.startswith("Требует для использования:"):
            d["requires"] = s.split(":", 1)[1].strip()
        elif s.startswith("Флаги предмета"):
            d["flags"] = s.split(":", 1)[1].strip()
        elif s.startswith("Флаги оружия"):
            d["weapon_flags"] = s.split(":", 1)[1].strip()
        elif s.startswith("Флаги запрета"):
            d["forbid"] = s.split(":", 1)[1].strip()
        elif s.startswith("Вес:"):
            mm = re.match(r"Вес: (\S+), Таймер: (\S+), Материал: (.+)", s)
            if mm:
                d["weight"], d["timer"], d["material"] = mm.group(1).rstrip(","), mm.group(2).rstrip(","), mm.group(3)
        elif s.startswith("Вы можете одеть это на"):
            d["slot"] = s.replace("Вы можете одеть это на", "").strip(" .")
        elif s.startswith("Оружейное умение:"):
            d["weapon_skill"] = s.split(":", 1)[1].split(",")[0].strip()
        elif s.startswith("Повреждения:"):
            d["damage"] = s.split(":", 1)[1].strip()
        elif s.startswith("Количество применений:"):
            d["charges"] = s.split(":", 1)[1].strip()
        elif s.startswith("Заклинание:"):
            d["spell"] = s.split(":", 1)[1].strip()
        elif s.startswith("Модификаторы"):
            section = "mods"
        elif s.startswith("Аффекты"):
            section = "affects"
        elif section == "mods":
            mods.append(s)
            for key, col in (("АС:", "ac"), ("Броня против режущего:", "armor_cut"), ("Броня против дробящего:", "armor_crush"),
                             ("Броня против колющего:", "armor_pierce")):
                if s.startswith(key):
                    d[col] = s.split(":", 1)[1].strip()
        elif section == "affects":
            affects.append(s)
    d["mods"] = "; ".join(mods)
    d["affects"] = "; ".join(affects)
    return d


def save_card(conn, text, place="", vnum="", price=None, source=""):
    conn.execute(SCHEMA)
    d = parse(text)
    if not d["name"]:
        return None
    cols = ["name", "type", "slot", "requires", "weight", "timer", "material", "flags", "weapon_flags", "forbid", "weapon_skill", "damage",
            "ac", "armor_cut", "armor_crush", "armor_pierce", "mods", "affects", "charges", "spell", "rating"]
    conn.execute(f"INSERT OR REPLACE INTO item_cards ({','.join(cols)},place,vnum,price,source,raw) VALUES ({','.join('?' * len(cols))},?,?,?,?,?)",
                 [d[k] for k in cols] + [place, vnum, price, source, text.strip()[:4000]])
    return d
