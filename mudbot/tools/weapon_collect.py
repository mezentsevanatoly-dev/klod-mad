"""Оружие для варвара (дубины и палицы): КСК и биржа -> таблица weapons (game.db), выбор правой/левой руки для комплектов.
python -X utf8 tools/weapon_collect.py collect      собрать карточки (КСК `ксклад оружие *дубины =варвар =L`, биржа `биржа предл оружие *дубины =варвар =L !40`)
python -X utf8 tools/weapon_collect.py select       показать лучшие правую/левую руки для окон 1-8, 9-12, 13-20 (оценка варвара Ва; уникальные помечены)
"""
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_collect as K  # noqa: E402

LOT = re.compile(r"^\s*(\d+)\. \[\s*(\d+)\] \(\s*(\d+)\)(?: !\s*(\d+)!)? (.+?)\s*$")


def card(text):
    c = K.parse_card(text)
    m = re.search(r"Флаги оружия\s*: (.+)", text)
    c["hand"] = (m.group(1).strip() if m else "")
    m = re.search(r"Повреждения: (\d+)D(\d+) \(среднее (\d+)\)", text)
    c["dmg"] = int(m.group(3)) if m else 0
    m = re.search(r"Аффекты\s*: (.+)", text)
    c["aff"] = m.group(1).strip() if m else ""
    m = re.search(r"Оружейное умение: ([^,]+)", text)
    c["skill"] = m.group(1).strip() if m else ""
    r = c["rating"].split(",")
    c["va"] = int(r[1]) if len(r) > 1 and r[1].strip().isdigit() else 0
    return c


def collect():
    db = sqlite3.connect(K.DB)
    db.execute("""create table if not exists weapons (src text, ref text, name text, hand text, minlvl int, va int, timer int, stars int, dmg int,
        skill text, aff text, mods text, price int, uni int, flags text, ts text, primary key (src, ref))""")
    for lvl in (8, 12, 20):
        out = K.cmd_pages(f"ксклад оружие *дубины =варвар ={lvl}")
        for l in out.splitlines():
            m = re.match(r"^\[\s*([^\]]+?)\]:\s+(.+?)\s*$", l) or re.match(r"^ (\S.+?)\s*$", l)
            if not m or l.startswith((" Всего", ">>>", "[cur]")) or "хранятся" in l or "Вых:" in l:
                continue
            if m.re.pattern.startswith("^\\["):
                dept, name = m.group(1).strip(), m.group(2)
            else:
                dept, name = "Следак1", m.group(1)
            name = re.sub(r"\s*\[\d+\]$", "", name).strip()
            if db.execute("select 1 from weapons where src=? and ref=?", ("КСК:" + dept, name)).fetchone():
                continue
            out2 = K.cmd(f"ксклад инф :{dept.lower()} {K.keyword(name)}")
            c = card(out2)
            if c["title"]:
                db.execute("insert or replace into weapons values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))",
                           ("КСК:" + dept, name, name, c["hand"], c["minlvl"], c["va"], c["timer"], c["stars"], c["dmg"], c["skill"], c["aff"],
                            "; ".join(c["mods"]), 0, c["unique"], c["flags"]))
                db.commit()
                print("КСК", dept, name, c["minlvl"], c["va"], c["hand"], flush=True)
    seen = {}
    for lvl in (8, 12, 20):
        out = K.cmd_pages(f"биржа предл оружие *дубины =варвар ={lvl} !40")
        for l in out.splitlines():
            m = LOT.match(l)
            if m:
                seen.setdefault(int(m.group(1)), (m.group(5), int(m.group(2)), int(m.group(3))))
    for lot, (name, price, timer) in sorted(seen.items(), key=lambda x: x[1][1]):
        if db.execute("select 1 from weapons where src='биржа' and ref=?", (str(lot),)).fetchone():
            continue
        c = card(K.cmd(f"биржа инф {lot}"))
        if c["title"]:
            db.execute("insert or replace into weapons values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))",
                       ("биржа", str(lot), name, c["hand"], c["minlvl"], c["va"], timer, c["stars"], c["dmg"], c["skill"], c["aff"],
                        "; ".join(c["mods"]), price, c["unique"], c["flags"]))
            db.commit()
            print("биржа", lot, name, price, c["minlvl"], c["va"], c["hand"], flush=True)


def select():
    db = sqlite3.connect(K.DB)
    rows = db.execute("select src,ref,name,hand,minlvl,va,timer,stars,dmg,aff,mods,price,uni from weapons").fetchall()
    for lo, hi in ((1, 8), (9, 12), (13, 20)):
        print(f"\n== окно {lo}-{hi}")
        for hand, key in (("правая", "ПРАВУЮ"), ("левая", "ЛЕВУЮ")):
            pool = [r for r in rows if key in r[3] and r[4] <= hi and r[6] >= 8000 and r[11] <= (30000 if hi <= 12 else 150000)]
            pool.sort(key=lambda r: (r[5] - r[11] / 5000), reverse=True)
            for r in pool[:4]:
                print(f"  {hand:7} {r[2]:28} мин{r[4]:>3} Ва{r[5]:>4} ур{r[8]:>3} зв{r[7]} т{r[6]:>6} {'У' if r[12] else ' '} {r[0]}:{r[1]} {r[11] or ''} | {r[9]} {r[10][:60]}")


if __name__ == "__main__":
    {"collect": collect, "select": select}[sys.argv[1] if len(sys.argv) > 1 else "select"]()
