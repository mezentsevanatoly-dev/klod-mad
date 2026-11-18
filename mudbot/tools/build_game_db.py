"""Сводная база знаний игры: data/game.db (SQLite).

  python tools/build_game_db.py        пересобрать из файлов проекта (журнал `journal` не трогает)
  python tools/build_game_db.py q "<SQL>"   запрос, например: q "select * from shops where item like '%кираса%'"

Таблицы: zones, rooms, mobs, danger, items, shops, consumables, speedwalks, places, gear_sets, journal.
Источники: areas/msdp/*.json и _walked.json (клетки), data/db/mobs.csv и areas/inc/*_мобы.csv (мобы),
data/db/gear.csv и areas/msdp/items.json (вещи), speedwalks.txt, tools/trip.py (PLACES), data/zones_game.tsv (зоны),
плюс то, что я увидела в игре сама (shops, consumables) — оно внесено ниже вручную и помечено source='игра 03.11'.
"""
import csv
import glob
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "game.db")


def p(*a):
    return os.path.join(HERE, *a)


SCHEMA = """
DROP TABLE IF EXISTS zones; DROP TABLE IF EXISTS rooms; DROP TABLE IF EXISTS mobs; DROP TABLE IF EXISTS danger;
DROP TABLE IF EXISTS items; DROP TABLE IF EXISTS shops; DROP TABLE IF EXISTS consumables; DROP TABLE IF EXISTS speedwalks;
DROP TABLE IF EXISTS places; DROP TABLE IF EXISTS gear_sets;
CREATE TABLE zones (num INTEGER, name TEXT, lvl_from INTEGER, lvl_to INTEGER, where_ TEXT);
CREATE TABLE rooms (vnum TEXT PRIMARY KEY, zone TEXT, name TEXT, exits TEXT, note TEXT, source TEXT);
CREATE TABLE mobs (name TEXT, level TEXT, prof TEXT, hp TEXT, flags TEXT, skills TEXT, race TEXT, zone_log TEXT, kills TEXT, exp TEXT);
CREATE TABLE danger (mob TEXT, where_ TEXT, why TEXT, rule TEXT);
CREATE TABLE items (name TEXT, type TEXT, slot TEXT, min_lvl TEXT, ac TEXT, timer TEXT, mods TEXT, flags TEXT, source TEXT);
CREATE TABLE shops (place TEXT, vnum TEXT, zone TEXT, item TEXT, price INTEGER, note TEXT, source TEXT);
CREATE TABLE consumables (name TEXT, effect TEXT, charges TEXT, buy_at TEXT, price TEXT, note TEXT);
CREATE TABLE speedwalks (name TEXT, path TEXT, end_vnum TEXT, note TEXT);
CREATE TABLE places (name TEXT, vnum TEXT, how_to_get TEXT);
CREATE TABLE gear_sets (lvl INTEGER, slot TEXT, item TEXT, where_from TEXT, note TEXT);
CREATE TABLE IF NOT EXISTS journal (id INTEGER PRIMARY KEY AUTOINCREMENT, t TEXT, stage TEXT, chk TEXT, result TEXT, decision TEXT, why TEXT);
"""


def load_rooms(c):
    n = 0
    for f in glob.glob(p("areas", "msdp", "*.json")):
        base = os.path.basename(f)
        if base in ("items.json",) or base.endswith("_loot.json"):
            continue
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        if base == "_walked.json":
            for v, r in d.items():
                c.execute("INSERT OR IGNORE INTO rooms VALUES (?,?,?,?,?,?)",
                          (v, r.get("area", ""), r.get("name", ""), json.dumps(r.get("exits", {}), ensure_ascii=False), "", "_walked"))
                n += 1
        elif isinstance(d, dict) and isinstance(d.get("rooms"), dict):
            for v, r in d["rooms"].items():
                note = ("ДТ? " if r.get("dt_hint") else "") + ("скрытое: " + str(r["hidden"]) if r.get("hidden") else "") + ("двери: " + str(r["doors"]) if r.get("doors") else "")
                c.execute("INSERT OR REPLACE INTO rooms VALUES (?,?,?,?,?,?)",
                          (v, r.get("area", d.get("area", "")), r.get("name", ""), json.dumps(r.get("exits", {}), ensure_ascii=False), note, base))
                n += 1
    return n


def load_mobs(c):
    n = 0
    f = p("data", "db", "mobs.csv")
    if os.path.exists(f):
        for r in csv.reader(open(f, encoding="utf-8"), delimiter=";"):
            if r and r[0] != "имя" and len(r) >= 10:
                c.execute("INSERT INTO mobs VALUES (?,?,?,?,?,?,?,?,?,?)", r[:10])
                n += 1
    return n


def load_items(c):
    n = 0
    f = p("data", "db", "gear.csv")
    if os.path.exists(f):
        for r in csv.reader(open(f, encoding="utf-8"), delimiter=";"):
            if r and r[0] != "предмет" and len(r) >= 12:
                c.execute("INSERT INTO items VALUES (?,?,?,?,?,?,?,?,?)", (r[0], r[1], r[2], r[3], r[10], r[9], r[11], r[6], "gear.csv " + (r[12] if len(r) > 12 else "")))
                n += 1
    return n


def load_zones(c):
    n = 0
    f = p("data", "zones_game.tsv") if os.path.exists(p("data", "zones_game.tsv")) else p("areas", "zones_game.tsv")
    for r in csv.reader(open(f, encoding="utf-8"), delimiter="\t"):
        if r and r[0].isdigit() and len(r) >= 6:
            c.execute("INSERT INTO zones VALUES (?,?,?,?,?)", (int(r[0]), r[1], int(r[2]), int(r[3]), r[5]))
            n += 1
    return n


def load_speedwalks(c):
    n = 0
    for l in open(p("speedwalks.txt"), encoding="utf-8"):
        m = re.match(r"^([^#=\s][^=]*?)\s*=\s*(\S+)(?:\s*@\s*(\d+))?", l)
        if m:
            c.execute("INSERT INTO speedwalks VALUES (?,?,?,?)", (m.group(1).strip(), m.group(2), m.group(3) or "", ""))
            n += 1
    return n


def load_places(c):
    s = open(p("tools", "trip.py"), encoding="utf-8").read()
    i = s.find("PLACES = {")
    j = s.find("}", i)
    n = 0
    for k, v in re.findall(r'"([^"]+)":\s*"(\d+)"', s[i:j]):
        c.execute("INSERT INTO places VALUES (?,?,?)", (k, v, "python tools/trip.py в:" + k))
        n += 1
    return n


SHOPS = [  # (place, vnum, zone, item, price, note)
    ("Оружейный магазин", "100079", "Город Элендор", "простой кастет", 200, "рукопашный бой, правая рука"),
    ("Оружейный магазин", "100079", "Город Элендор", "прямой длинный меч", 200, "длинные лезвия, правая"),
    ("Оружейный магазин", "100079", "Город Элендор", "боевой кинжал", 150, "короткие лезвия, любая рука"),
    ("Оружейный магазин", "100079", "Город Элендор", "боевая секира", 200, "топоры, правая"),
    ("Оружейный магазин", "100079", "Город Элендор", "утренняя звезда", 200, "дубины и палицы +5, 4D3, правая рука"),
    ("Оружейный магазин", "100079", "Город Элендор", "железная булава", 300, "дубины и палицы +5, 4D5, две руки"),
    ("Оружейный магазин", "100079", "Город Элендор", "стальной шлем", 250, "АС+5 Хиты+5"),
    ("Оружейный магазин", "100079", "Город Элендор", "простой шлем", 100, ""),
    ("Оружейный магазин", "100079", "Город Элендор", "стеганый доспех", 150, "АС+4"),
    ("Оружейный магазин", "100079", "Город Элендор", "железная кольчуга", 300, "АС+6 Хиты+5"),
    ("Оружейный магазин", "100079", "Город Элендор", "стальная кираса", 500, "АС+8 Телосложение+1, броня 4/4/4"),
    ("Оружейный магазин", "100079", "Город Элендор", "обычный плащ", 200, "АС+3"),
    ("Оружейный магазин", "100079", "Город Элендор", "обычный пояс", 200, "АС+3"),
    ("Оружейный магазин", "100079", "Город Элендор", "стальные перчатки", 200, "АС+3"),
    ("Оружейный магазин", "100079", "Город Элендор", "полные наручи", 250, "АС+4 Хиты+5"),
    ("Оружейный магазин", "100079", "Город Элендор", "полные поножи", 250, "АС+4 Хиты+5"),
    ("Оружейный магазин", "100079", "Город Элендор", "железные солереты", 200, "АС+3"),
    ("Оружейный магазин", "100079", "Город Элендор", "стальной ростовой щит", 300, "АС+5"),
    ("Трактир «Перекуси с дороги»", "100073", "Город Элендор", "дневной рацион", 8, "еда; питья нет"),
    ("Трактир «Перекуси с дороги»", "100073", "Город Элендор", "кусок хлеба", 1, ""),
    ("Шатёр с напитками", "169042", "Парк аттракционов", "настойка лечения", 400, ""),
    ("Шатёр с напитками", "169042", "Парк аттракционов", "настойка восстановления", 500, "энергия"),
    ("Шатёр с напитками", "169042", "Парк аттракционов", "настойка насыщения", 500, "еда и питьё сразу"),
    ("Шатёр с напитками", "169042", "Парк аттракционов", "настойка левитации", 500, "полёт"),
    ("Шатёр с напитками", "169042", "Парк аттракционов", "настойка внимательности", 500, ""),
    ("Шатёр с напитками", "169042", "Парк аттракционов", "настойка силы", 500, ""),
    ("Шатёр с напитками", "169042", "Парк аттракционов", "настойка защиты", 750, ""),
    ("Шатёр с напитками", "169042", "Парк аттракционов", "настойка ускорения", 750, ""),
    ("Шатёр с напитками", "169042", "Парк аттракционов", "настойка прозрения", 250, "от слепоты"),
    ("Шатёр с напитками", "169042", "Парк аттракционов", "настойка противоядия", 250, ""),
    ("Лавка алхимика", "100013", "Город Элендор", "охранный свиток", 5000, "авто-реколл при смерти (из памяти)"),
    ("Лавка алхимика", "100013", "Город Элендор", "свиток панацеи", 10000, "снимает яд (из памяти)"),
    ("Лавка алхимика", "100013", "Город Элендор", "эликсир летучей мыши", 5000, "вампиризм (из памяти)"),
    ("Лавка кузнеца (Деревня варваров)", "", "Деревня варваров", "кожаный комплект «из толстой кожи», палицы битв", None, "со слов пользователя 03.11; вход с «Дорога Фелонад - Стэдвик» на север; не проверено"),
    ("Магазин знахаря (Деревня варваров)", "", "Деревня варваров", "настойки", None, "со слов пользователя 03.11; не проверено"),
]
SHOPS_SRC = "игра 03.11"

CONS = [
    ("настойка насыщения", "снимает голод и жажду", "2 (в Колбах), 10 (в Шатре)", "Шатёр с напитками 169042", "500", ""),
    ("настойка восстановления", "энергия (V)", "1", "Шатёр с напитками", "500", ""),
    ("настойка лечения", "лечит HP", "?", "Шатёр с напитками", "400", ""),
    ("настойка левитации", "полёт", "8", "Шатёр с напитками", "500", "из ренты без полёта не выходить"),
    ("эликсир летучей мыши", "вампиризм", "23, ~17 минут", "Лавка алхимика 100013", "5000", ""),
    ("свиток панацеи", "снимает яд", "20", "Лавка алхимика", "10000", ""),
    ("охранный свиток", "реколл при смерти", "15", "Лавка алхимика", "5000", "не работает в клетках !рекол"),
    ("эликсир прозрения", "лечит слепоту", "1", "Лавка алхимика", "~6800", ""),
]
DANGER = [
    ("огромный ящер", "Селение человекоящеров", "бьёт 75–193 за раунд", "не бить; смерть Эсхирда 01.11"),
    ("чёрный ящер-кастер", "Селение человекоящеров", "холд ×3, истощить жизнь", "не бить; смерть Эсхирда 01.11"),
    ("охранник трона", "Тоннель бесов, тронный зал", "×3 по ~80", "не бить; смерть, −358 тыс. опыта"),
    ("демон-лорд", "Тоннель бесов, тронный зал", "пламя хаоса 115–186, развеивает магию", "не бить"),
    ("ужас катакомб", "Катакомбы Геоланта, разветвление туннеля", "3 удара по ~246 + яд", "не бить; смерть, −270 тыс. опыта"),
    ("огненная саламандра", "Катакомбы Геоланта, комната 226125", "маг ур 21, агрессивная", "обходить комнату 226125"),
    ("Управляющий складом", "Склад в Геоланте", "маг ур 18, холд", "не бить"),
    ("Рыцарь смерти 30", "Город Элендор", "ур 30", "в городах никого не бить"),
]
GEAR = [  # (lvl, slot, item, where, note)
    (1, "голова", "шлем из толстой кожи", "Деревня варваров (со слов пользователя)", "комплект 1 лвл у Эсхирда; в КСК лежал в :следак1"),
    (1, "тело", "доспех из толстой кожи", "Деревня варваров", ""),
    (1, "руки", "наручи из толстой кожи", "Деревня варваров", ""),
    (1, "ноги", "поножи из толстой кожи", "Деревня варваров", ""),
    (1, "обувь", "сапоги из толстой кожи", "Деревня варваров", ""),
    (1, "кисти", "перчатки из грубой кожи", "Деревня варваров", ""),
    (1, "плечи", "плотный холщовый плащ", "Деревня варваров", ""),
    (1, "правая рука", "палица битв", "Деревня варваров", "дубины и палицы"),
    (1, "левая рука", "легкая палица битв", "Деревня варваров", ""),
    (1, "шея", "легкий шарфик ×2", "биржа", ""),
    (1, "талия", "змеиный пояс", "биржа", ""),
    (1, "запястье", "склизкий браслет", "КСК :следак1/:барб2", "+10 палицы, носить до 8 лвл"),
    (1, "голова", "стальной шлем", "Оружейный магазин Элендора", "то, что надето у Ждадиуса сейчас (без клана)"),
    (1, "тело", "стальная кираса", "Оружейный магазин Элендора", ""),
    (1, "правая рука", "утренняя звезда", "Оружейный магазин Элендора", ""),
]


def main():
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    c = sqlite3.connect(DB)
    c.executescript(SCHEMA)
    r = {"rooms": load_rooms(c), "mobs": load_mobs(c), "items": load_items(c), "zones": load_zones(c),
         "speedwalks": load_speedwalks(c), "places": load_places(c)}
    for s in SHOPS:
        c.execute("INSERT INTO shops VALUES (?,?,?,?,?,?,?)", s + (SHOPS_SRC,))
    for s in CONS:
        c.execute("INSERT INTO consumables VALUES (?,?,?,?,?,?)", s)
    for s in DANGER:
        c.execute("INSERT INTO danger VALUES (?,?,?,?)", s)
    for s in GEAR:
        c.execute("INSERT INTO gear_sets VALUES (?,?,?,?,?)", s)
    r.update(shops=len(SHOPS), consumables=len(CONS), danger=len(DANGER), gear_sets=len(GEAR))
    c.commit()
    c.close()
    print("game.db:", r)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) > 2 and sys.argv[1] == "q":
        c = sqlite3.connect(DB)
        cur = c.execute(sys.argv[2])
        print(" | ".join(d[0] for d in cur.description))
        for row in cur.fetchmany(60):
            print(" | ".join(str(x) for x in row))
    else:
        main()
