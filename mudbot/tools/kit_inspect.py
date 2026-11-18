"""Полные свойства УНИКАЛЬНЫХ вещей комплектов: взять с КСК, `осмотреть` (в инвентаре показывает уникальные строки бесплатно), сдать обратно.
python -X utf8 tools/kit_inspect.py   -> data/kit_unique.md и таблица kit_unique (game.db)
"""
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_collect as K  # noqa: E402


def main():
    db = sqlite3.connect(K.DB)
    db.execute("create table if not exists kit_unique (dept text, name text, mods text, raw text, ts text, primary key (dept, name))")
    rows = db.execute("select dept,name from ksk_items where dept like 'Следак%' and unique_flag=1 order by dept,name").fetchall()
    md = ["# Уникальные вещи комплектов (полные свойства из `осмотреть`)\n"]
    for dept, name in rows:
        word = K.keyword(name)
        out = K.cmd(f"кз :{dept.lower()} {word}|2")
        if "забрали" not in out:
            print("не забралось", dept, name, flush=True)
            continue
        txt = K.cmd(f"осмотреть {word}|2")
        mods = re.search(r"Модификаторы :\n(.*?)(?:\n\s{3}\S|\n\d+H |\Z)", txt, re.S)
        lines = [l.strip() for l in (mods.group(1).splitlines() if mods else []) if l.strip() and not l.startswith("[cur]")]
        K.cmd(f"кс :{dept.lower()} {word}|2")
        db.execute("insert or replace into kit_unique values (?,?,?,?,datetime('now'))", (dept, name, "; ".join(lines), txt))
        db.commit()
        md.append(f"## {dept}: {name}\n" + "\n".join(f"- {l}" for l in lines) + "\n")
        print(f"{dept}: {name}: {'; '.join(lines)[:200]}", flush=True)
    with open(os.path.join(ROOT, "data", "kit_unique.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))


if __name__ == "__main__":
    main()
