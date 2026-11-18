"""БД мобов и предметов из логов JMC (Клод мад\\JMC\\<имя>, кодировка cp1251) и осмотров бота.

python tools/build_db.py            -> data/db/mobs.csv, data/db/gear.csv

mobs.csv: имя, уровень, профессия, хиты, особенности, навыки, раса, откуда (логи), убито, опыт (мин-макс по логам).
gear.csv: предмет, тип, слот, мин.ур., оценка по профессиям (Ва — варвар), флаги, аффекты, таймер, модификаторы, откуда.
Новые осмотры, сделанные ботом (`см имя`), дописывает lvlup.py через add_mob()/add_item() в те же файлы.
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
JMC = os.path.join(ROOT, "..", "JMC")
DB = os.path.join(ROOT, "data", "db")

MOB = re.compile(r"^(.+?) \[уровень (\d+)\](?:, (.+))?$")
ITEM = re.compile(r"^Предмет '(.+?)', Тип предмета: (.+)$")
KILL = re.compile(r"^(.*?) мертв[аоы]?\. R\.I\.P\.")
XP = re.compile(r"^Вы получили (\d+) единиц")
MOB_COLS = ["имя", "уровень", "профессия", "хиты", "особенности", "навыки", "раса", "логи", "убито", "опыт"]
ITEM_COLS = ["предмет", "тип", "слот", "мин_ур", "оценка_Ва", "оценка_все", "флаги", "запрет", "аффекты",
             "таймер", "ас", "модификаторы", "логи"]


def read_log(path):
    return open(path, encoding="cp1251", errors="replace").read().replace("\r", "").split("\n")


def scan(name, lines, mobs, items):
    last_kill = None
    for i, l in enumerate(lines):
        m = MOB.match(l)
        if m and not l.startswith(("Вы ", "Ваш")):
            blk = lines[i:i + 14]
            d = mobs.setdefault(m.group(1), {"имя": m.group(1), "логи": set(), "убито": 0, "xp": []})
            d["уровень"], d["профессия"] = m.group(2), m.group(3) or ""
            d["логи"].add(name)
            for b in blk[1:]:
                if b.startswith("Вы видите перед собой"):
                    d["раса"] = b.replace("Вы видите перед собой ", "").rstrip(".")
                elif b.startswith("Хиты:"):
                    d["хиты"] = re.sub(r"Хиты: (-?\d+)/(-?\d+).*", r"\2", b)
                elif b.startswith("Особенности:"):
                    d["особенности"] = b.split(":", 1)[1].strip()
                elif b.startswith("Навыки"):
                    d["навыки"] = b.split(":", 1)[1].strip()
            continue
        k = KILL.match(l)
        if k:
            last_kill = k.group(1)
            if last_kill in mobs:
                mobs[last_kill]["убито"] += 1
            continue
        x = XP.match(l)
        if x and last_kill:
            mobs.setdefault(last_kill, {"имя": last_kill, "логи": set(), "убито": 1, "xp": []})
            mobs[last_kill]["логи"].add(name)
            mobs[last_kill]["xp"].append(int(x.group(1)))
            last_kill = None
        it = ITEM.match(l)
        if it:
            blk = lines[i:i + 45]
            d = items.setdefault(it.group(1), {"предмет": it.group(1), "тип": it.group(2).strip(), "логи": set()})
            d["логи"].add(name)
            for j, b in enumerate(blk):
                if b.startswith("Оценка:"):
                    heads = blk[j - 1].split()
                    vals = [v.strip() for v in b[7:].split(",")]
                    r = dict(zip(heads, vals))
                    d["оценка_Ва"], d["оценка_все"] = r.get("Ва", ""), " ".join(f"{h}={v}" for h, v in r.items())
                elif b.startswith("Требует для использования"):
                    mm = re.search(r"мин\.уровень (\d+)", b)
                    d["мин_ур"] = mm.group(1) if mm else ""
                elif b.startswith("Флаги предмета"):
                    d["флаги"] = b.split(":", 1)[1].strip()
                elif b.startswith("Флаги запрета"):
                    d["запрет"] = b.split(":", 1)[1].strip()
                elif b.startswith("Аффекты"):
                    d["аффекты"] = b.split(":", 1)[1].strip()
                elif b.startswith("Вес:"):
                    mm = re.search(r"Таймер: (\d+)", b)
                    d["таймер"] = mm.group(1) if mm else ""
                elif b.startswith("Вы можете одеть это на") or b.startswith("Вы можете взять"):
                    d["слот"] = b.replace("Вы можете одеть это на ", "").rstrip(".")
                elif re.match(r"^ АС: ", b):
                    d["ас"] = b.split(":", 1)[1].strip()
                elif b.startswith("Модификаторы"):
                    mods = []
                    for c in blk[j + 1:]:
                        if c.startswith(" ") and not c.startswith("   "):
                            mods.append(c.strip())
                        else:
                            break
                    d["модификаторы"] = "; ".join(mods)


def rng(v):
    return "" if not v else (str(min(v)) if min(v) == max(v) else f"{min(v)}-{max(v)}")


def write(path, cols, rows):
    os.makedirs(DB, exist_ok=True)
    w = csv.writer(open(path, "w", encoding="utf-8-sig", newline=""), delimiter=";")
    w.writerow(cols)
    for r in rows:
        w.writerow([r.get(c, "") if not isinstance(r.get(c, ""), (set, list)) else ",".join(sorted(map(str, r[c]))) for c in cols])


def main():
    mobs, items = {}, {}
    for f in sorted(os.listdir(JMC)):
        p = os.path.join(JMC, f)
        if os.path.isfile(p) and "." not in f and f not in ("jmc",):
            try:
                scan(f, read_log(p), mobs, items)
            except OSError:
                pass
    for d in mobs.values():
        d["опыт"] = rng(d.pop("xp", []))
    rows = sorted(mobs.values(), key=lambda d: (int(d.get("уровень") or 0), d["имя"]))
    write(os.path.join(DB, "mobs.csv"), MOB_COLS, rows)
    write(os.path.join(DB, "gear.csv"), ITEM_COLS, sorted(items.values(), key=lambda d: d["предмет"]))
    known = sum(1 for d in mobs.values() if d.get("уровень"))
    print(f"мобов: {len(mobs)} (с уровнем {known}), предметов: {len(items)}")


if __name__ == "__main__":
    main()
