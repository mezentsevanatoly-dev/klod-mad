"""Сбор карточек вещей КСК для варвара в таблицу ksk_items (game.db): списки `ксклад * од =варвар =<лвл>` + `ксклад инф :<отдел> <слова>`.
python -X utf8 tools/kit_collect.py [лвл ...]     (по умолчанию 1 5 8 12 15 20)
Стоим в комнате склада (Элендор 100076). Карточки не трогают клан (инф бесплатный). Уникальные свойства (синие вещи) инф не показывает: флаг
УНИКАЛЬНЫЙ ставится в базу, полные свойства — кск х для финалистов.
"""
import os
import re
import sqlite3
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV = dict(os.environ, MUD_VIA="bot")
DB = os.path.join(ROOT, "data", "game.db")
STOP = {"из", "с", "в", "на", "и", "для", "от", "под", "над", "по"}


def cmd(c, timeout=90):
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(ROOT, "tools", "cmd.py"), c], env=ENV, cwd=ROOT,
                       capture_output=True, encoding="utf-8", errors="replace", timeout=timeout)
    return r.stdout


def cmd_pages(c, maxpages=12):
    """Команда со списком: если игра предлагает «<Enter> - показать следующую страницу», листаем пробелом до конца."""
    out = cmd(c)
    for _ in range(maxpages):
        if "показать следующую страницу" not in out.rsplit("[cur]", 2)[0][-400:]:
            break
        nxt = cmd(" ")
        out += "\n" + nxt
    if "показать следующую страницу" in out.rsplit("[cur]", 2)[0][-400:]:
        cmd("к")                                  # закрыть листание, если страниц больше лимита
    return out


def keyword(name, n=1):
    words = [w for w in re.sub(r"[*,\[\]\d]", " ", name).split() if w.lower() not in STOP]
    k = ".".join(w[:5] for w in words) or name
    return (str(n) + k) if n > 1 else k


def listing(lvl):
    out = cmd_pages(f"ксклад * од =варвар ={lvl}")
    items = []
    for l in out.splitlines():
        m = re.match(r"^\[\s*([^\]]+?)\]:\s+(.+?)\s*$", l)
        if m:
            name, cnt = m.group(2), 1
            mm = re.match(r"^(.*?)\s*\[(\d+)\]$", name)
            if mm:
                name, cnt = mm.group(1), int(mm.group(2))
            items.append((m.group(1).strip(), name.strip(), cnt))
    return items


def parse_card(text):
    d = {"title": "", "type": "", "rating": "", "req": "", "minlvl": 0, "flags": "", "forbid": "", "timer": 0, "weight": 0,
         "stars": 0, "slot": "", "ac": 0, "cut": 0, "crush": 0, "pierce": 0, "mods": [], "unique": 0, "special": 0}
    m = re.search(r"Предмет '(.+?)', Тип предмета: (.+)", text)
    if m:
        d["title"], d["type"] = m.group(1), m.group(2).strip()
    if "особенными и уникальными свойствами" in text or "уникальными свойствами" in text:
        d["special"] = 1
    m = re.search(r"Оценка:\s*([\d,\s]+)", text)
    if m:
        vals = [v.strip() for v in m.group(1).split(",") if v.strip()]
        d["rating"] = ",".join(vals)
    m = re.search(r"Требует для использования: (.+)", text)
    if m:
        d["req"] = m.group(1).strip()
        mm = re.search(r"мин\.уровень (\d+)", d["req"])
        d["minlvl"] = int(mm.group(1)) if mm else 0
    m = re.search(r"Флаги предмета: (.+)", text)
    if m:
        d["flags"] = m.group(1).strip()
        d["unique"] = 1 if "УНИКАЛЬНЫЙ" in d["flags"] else 0
    m = re.search(r"Флаги запрета : (.+)", text)
    if m:
        d["forbid"] = m.group(1).strip()
    m = re.search(r"Таймер: (\d+)", text)
    if m:
        d["timer"] = int(m.group(1))
    m = re.search(r"Вес: (\d+)", text)
    if m:
        d["weight"] = int(m.group(1))
    m = re.search(r"Запас особенностей: (\*+)", text)
    if m:
        d["stars"] = len(m.group(1))
    m = re.search(r"Вы можете (?:одеть|надеть|взять|держать|использовать)[^.\n]*", text)
    if m:
        d["slot"] = m.group(0).strip()
    mods = re.search(r"Модификаторы :\n(.*?)(?:\n\s{3}\S|\n\d+H |\Z)", text, re.S)
    if mods:
        for l in mods.group(1).splitlines():
            s = l.strip()
            if not s or s.startswith("[cur]"):
                continue
            d["mods"].append(s)
            mm = re.match(r"\*?АС: \+?(-?\d+)", s)
            if mm and not s.startswith("*"):
                d["ac"] += int(mm.group(1))
            mm = re.match(r"\*?АС: \+?(-?\d+)", s)
            if mm and s.startswith("*"):
                d["ac"] += int(mm.group(1))
            for key, fld in (("режущего", "cut"), ("дробящего", "crush"), ("колющего", "pierce")):
                mm = re.match(r"Броня против " + key + r": \+?(-?\d+)", s)
                if mm:
                    d[fld] = int(mm.group(1))
    return d


def main():
    lvls = [int(a) for a in sys.argv[1:]] or [1, 8, 12, 20]
    db = sqlite3.connect(DB)
    db.execute("""create table if not exists ksk_items (dept text, name text, title text, type text, slot text, minlvl int, req text,
        flags text, unique_flag int, special int, timer int, weight int, stars int, ac int, cut int, crush int, pierce int, mods text,
        rating text, forbid text, cnt int, seen_lvl int, ts text, primary key (dept, name))""")
    seen = {}
    for lvl in lvls:
        for dept, name, cnt in listing(lvl):
            seen.setdefault((dept, name), [cnt, lvl])
    print(f"позиций: {len(seen)}", flush=True)
    for dept, name in db.execute("select dept,name from ksk_items").fetchall():          # вещи, которые с КСК ушли (забрали другие), из базы убираем
        if (dept, name) not in seen:
            db.execute("delete from ksk_items where dept=? and name=?", (dept, name))
            print("убрана из базы (ушла со склада):", dept, name, flush=True)
    db.commit()
    for (dept, name), (cnt, lvl) in seen.items():
        row = db.execute("select 1 from ksk_items where dept=? and name=?", (dept, name)).fetchone()
        if row:
            db.execute("update ksk_items set cnt=? where dept=? and name=?", (cnt, dept, name))
            continue
        card = None
        for n in (1, 2, 3):
            out = cmd(f"ксклад инф :{dept.lower()} {keyword(name, n)}")
            c = parse_card(out)
            if c["title"] and c["title"].replace(" ", "") == name.replace(" ", ""):
                card = c
                break
            if not c["title"]:
                break
        if not card:
            print("не нашла карточку:", dept, name, flush=True)
            continue
        db.execute("insert or replace into ksk_items values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))",
                   (dept, name, card["title"], card["type"], card["slot"], card["minlvl"], card["req"], card["flags"], card["unique"],
                    card["special"], card["timer"], card["weight"], card["stars"], card["ac"], card["cut"], card["crush"], card["pierce"],
                    "; ".join(card["mods"]), card["rating"], card["forbid"], cnt, lvl))
        db.commit()
        print(f"{dept}: {name} | мин {card['minlvl']} АС {card['ac']} {'УНИК' if card['unique'] else ''} {card['slot']}", flush=True)
    db.commit()


if __name__ == "__main__":
    main()
