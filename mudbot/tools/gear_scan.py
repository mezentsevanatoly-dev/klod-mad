"""База стафа для варвара через JMC (только чтение): КСК по слотам -> характеристики каждой вещи -> оценка по правилам пользователя.
python tools/gear_scan.py [уровень=18]   -> data/gear_<ур>.json и таблица лучших вещей по слотам (data/dress_rules.md)

Правила: приоритет АС (с потенциалом звёзд: n-е улучшение той же характеристики стоит n звёзд, АС растёт на 2 за улучшение),
затем броня, звёзды, таймер, статы/бонусы умений, не выше уровня. Надетое осматриваем «осмотреть <слово>».
Пользователь в строке ввода JMC не печатает — jmc.py сам откажется, если там текст.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jmc  # noqa: E402

ROOT = os.path.dirname(HERE)
SLOTS = [("допслот", "доп"), ("голова", "голов"), ("шея", "шея"), ("тело", "тело"), ("плечи", "плеч"), ("талия", "талия"),
         ("кисти", "кист"), ("руки", "руки"), ("ноги", "ноги"), ("обувь", "обув"), ("запястье", "запя"), ("палец", "палец")]


def stars(name):
    return len(re.findall(r"\*", name))


def clean(name):
    return re.sub(r"\s*(\*+|\[\d+\])", "", name).strip()


def parse_info(lines):
    """Блок «Предмет '…', Тип предмета» -> словарь."""
    d = {"ac": 0, "armor": 0, "mods": {}, "stars_reserve": 0, "timer": 0, "level": 0, "slot": "", "rating": None, "aff": ""}
    cols = []
    for i, l in enumerate(lines):
        m = re.match(r"^Предмет '(.+?)', Тип предмета: (\S+)", l)
        if m:
            d["name"], d["type"] = m.group(1), m.group(2)
        if re.match(r"^\s+Вн\s+Ва", l):
            cols = l.split()
        if l.startswith("Оценка:") and cols:
            vals = re.findall(r"\d+", l)
            if "Ва" in cols and len(vals) > cols.index("Ва"):
                d["rating"] = int(vals[cols.index("Ва")])
        if l.startswith("Требует для использования"):
            m = re.search(r"мин\.уровень (\d+)", l)
            d["level"] = int(m.group(1)) if m else 0
        if l.startswith("Аффекты"):
            d["aff"] = l.split(":", 1)[1].strip()
        m = re.match(r"^Вес: \d+, Таймер: (\d+)", l)
        if m:
            d["timer"] = int(m.group(1))
        if l.startswith("Запас особенностей"):
            d["stars_reserve"] = l.count("*")
        if l.startswith("Вы можете одеть это на"):
            d["slot"] = l.replace("Вы можете одеть это на", "").strip(" .")
        m = re.match(r"^ (\*?)([^:+]+?): ([+-]\d+)$", l)
        if m:
            key, val = m.group(2).strip(), int(m.group(3))
            if m.group(1):
                key = "*" + key
            d["mods"][key] = val
            if key == "АС":
                d["ac"] = val
            if key == "Броня против режущего":
                d["armor"] = val
    return d


def upgrades(s):
    """Сколько улучшений одной характеристики даст запас s: 1+2+3... <= s."""
    k = 0
    while (k + 1) * (k + 2) // 2 <= s:
        k += 1
    return k


def score(d, extra_stars=0):
    s = d["stars_reserve"] + extra_stars
    pot_ac = d["ac"] + (2 * upgrades(s) if d["ac"] else 0)
    bonus = sum(v for k, v in d["mods"].items() if re.search(r"Сила|Ловкость|Телосложение|Дополнительная атака|Атака второй рукой|DAMROLL", k))
    return (pot_ac, d["armor"], s, min(d["timer"], 60000), bonus)


def main():
    level = int(sys.argv[1]) if len(sys.argv) > 1 else 18
    db = {}
    cmds = [f"ксклад * одежда *{tok} =варвар ={level}" for _, tok in SLOTS]
    res = jmc.do_many(cmds, 1.3)
    cand = {}
    for (slot, tok), (c, lines) in zip(SLOTS, res):
        names = []
        for l in lines:
            m = re.match(r"^\[\s*(\S+)\]:\s+(.+)$", l)
            if m:
                names.append((m.group(1), m.group(2).strip()))
        cand[slot] = names
        print(f"{slot}: {len(names)} вещей", flush=True)
    uniq = {}
    for slot, names in cand.items():
        for dept, n in names:
            uniq.setdefault(clean(n), []).append((slot, dept, n))
    print("уникальных вещей:", len(uniq), flush=True)
    # характеристики: «ксклад инф <слова>» — по пачкам
    keys = list(uniq)
    for i in range(0, len(keys), 8):
        batch = keys[i:i + 8]
        cmds = ["ксклад инф " + ".".join(k.split()[:3]) for k in batch]
        out = jmc.do_many(cmds, 1.2)
        for k, (c, lines) in zip(batch, out):
            info = parse_info(lines)
            if info.get("name"):
                info["places"] = uniq[k]
                db[k] = info
    json.dump(db, open(os.path.join(ROOT, "data", f"gear_{level}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n=== лучшие по слотам (АС с потенциалом звёзд, броня, звёзды, таймер, бонусы) ===")
    for slot, _ in SLOTS:
        rows = [(score(db[clean(n)]), clean(n), dept, n) for dept, n in cand[slot] if clean(n) in db]
        rows.sort(reverse=True)
        for sc, name, dept, n in rows[:4]:
            d = db[name]
            print(f"{slot:9} {n:42} [{dept}] АС{d['ac']:+d} пот.{sc[0]} брон{d['armor']} звёзд{d['stars_reserve']} "
                  f"таймер{d['timer']} ур{d['level']}")


if __name__ == "__main__":
    main()
