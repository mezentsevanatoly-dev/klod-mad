"""Обход магазинов зоны: `путь список` -> для каждого магазина `путь <название>` -> `список` -> `характеристики N` -> data/game.db (shops, items).

  python tools/shop_scan.py            магазины зоны, где стоит персонаж
  python tools/shop_scan.py "оружейный магазин" "лавка алхимика"      только указанные

Ничего не покупает. Зоны без `путь` (нет ключевых комнат) пропускаются. Перед запуском остановить других охотников.
"""
import os
import re
import sqlite3
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(HERE, "data", "game.db")
SHOP_WORDS = re.compile(r"магазин|лавка|кузниц|оруж|алхим|трактир|шатер|шатёр|рынок|торгов|точильщик|лавочк|палатк|аптек|бакале|пекар|мясн|таверн", re.I)


def cmd(cmds, wait=1.5):
    env = dict(os.environ, MUD_VIA="bot", PYTHONUTF8="1")
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "tools", "cmd.py")] + [f"{c}|{wait}" for c in cmds],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=HERE, env=env)
    return r.stdout


def cur(out):
    m = re.findall(r"\[cur\] \{'vnum': '(\d+)', 'area': '([^']*)', 'name': '([^']*)'", out.replace("\n", " "))
    return m[-1] if m else ("", "", "")


def key_rooms():
    out = cmd(["путь список"], 3)
    rooms = []
    for l in out.split("\n"):
        m = re.match(r"^\s+([^()]+?)\s*(?:\(([^)]*)\))?\s*$", l)
        if m and l.startswith(" ") and not l.startswith("Список") and SHOP_WORDS.search(l):
            rooms.append(m.group(1).strip())
    return rooms, cur(out)[1]


def parse_card(text):
    d = {"name": "", "type": "", "slot": "", "timer": "", "ac": "", "mods": [], "skill": "", "dmg": "", "rate": ""}
    mods = False
    for l in text.split("\n"):
        s = l.strip()
        m = re.match(r"^Предмет '(.+?)', Тип предмета: (.+)$", s)
        if m:
            d["name"], d["type"] = m.group(1), m.group(2)
        elif s.startswith("Оценка:"):
            d["rate"] = s.split(":", 1)[1].strip()
        elif s.startswith("Вес:"):
            mm = re.search(r"Таймер: (\d+)", s)
            d["timer"] = mm.group(1) if mm else ""
        elif s.startswith("Вы можете одеть это на"):
            d["slot"] = s.replace("Вы можете одеть это на", "").strip(" .")
        elif s.startswith("Оружейное умение:"):
            d["skill"] = s.split(":", 1)[1].split(",")[0].strip()
        elif s.startswith("Повреждения:"):
            d["dmg"] = s.split(":", 1)[1].strip()
        elif s.startswith("Модификаторы"):
            mods = True
        elif mods and s and not re.match(r"^\d+H ", s) and not s.startswith("[cur]"):
            d["mods"].append(s)
            if s.startswith("АС:"):
                d["ac"] = s.split(":", 1)[1].strip()
        elif mods and (not s or re.match(r"^\d+H ", s)):
            mods = False
    return d


def scan_shop(c, room, walk=True):
    out = cmd(["где"], 2) if not walk else cmd([f"путь {room}"], 40)
    for _ in range(4 if walk else 0):                          # дошли? иначе ещё подождать
        if "Вы достигли пункта назначения" in out:
            break
        out += cmd(["где"], 20)
    vnum, zone, rname = cur(out)
    lst = cmd(["список"], 3)
    items = [(int(m.group(1)), int(m.group(2)), m.group(3).strip()) for l in lst.split("\n") if (m := re.match(r"^\s*(\d+)\.\s*\[\s*(\d+)\]\s*(.+)$", l))]
    if not items:
        print(f"{room}: не магазин (список пуст)")
        return 0
    print(f"{room} ({vnum}, {zone}): {len(items)} товаров")
    cards = cmd([f"характеристики {n}" for n, _, _ in items], 1.2)
    parts = re.split(r">>> характеристики (\d+)\n", cards)
    byn = {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}
    for n, price, name in items:
        d = parse_card(byn.get(n, ""))
        import item_cards
        item_cards.save_card(c, byn.get(n, ""), place=rname or room, vnum=vnum, price=price, source="скан магазина")      # все поля + сырой текст
        c.execute("DELETE FROM shops WHERE place=? AND item=?", (rname or room, name))
        c.execute("INSERT INTO shops VALUES (?,?,?,?,?,?,?)", (rname or room, vnum, zone, name, price,
                                                               (d["skill"] + " " + d["dmg"] + " " + "; ".join(d["mods"]))[:200], "скан магазина"))
        if d["name"]:
            c.execute("DELETE FROM items WHERE name=? AND source LIKE 'магазин %'", (d["name"],))
            c.execute("INSERT INTO items VALUES (?,?,?,?,?,?,?,?,?)", (d["name"], d["type"], d["slot"], "", d["ac"], d["timer"],
                                                                        "; ".join(d["mods"]), "", f"магазин {rname or room} {price}"))
    c.commit()
    return len(items)


def main(only):
    c = sqlite3.connect(DB)
    if only[:1] == ["--here"]:                                 # зоны без `путь` (деревни): магазин в текущей комнате
        print("товаров записано:", scan_shop(c, only[1] if len(only) > 1 else "магазин здесь", walk=False))
        return
    rooms, zone = key_rooms()
    if only:
        rooms = [r for r in rooms if any(o.lower() in r.lower() for o in only)] or only
    print(f"зона «{zone}», магазины: {rooms}")
    total = sum(scan_shop(c, r) for r in rooms)
    print("всего товаров записано:", total)
    c.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1:])
