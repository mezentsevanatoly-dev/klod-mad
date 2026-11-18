"""Сбор лотов биржи для варвара: `биржа предл од *<слот> =варвар =<лвл> !<оценка>` + `биржа инф <лот>` -> таблицы exch_lots, ex_items (game.db).
python -X utf8 tools/exch_collect.py [лвл ...]      по умолчанию 1 8 12 15 18 20; стоим в комнате склада (биржа доступна оттуда)
Карточки (оценка, АС, броня, звёзды, таймер, УНИКАЛЬНЫЙ) берём один раз на название; цена и таймер — по лоту.
"""
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit_collect as K  # noqa: E402

SLOTS = ["доп", "голов", "шея", "тело", "плеч", "талия", "кист", "руки", "ноги", "обув", "запя", "палец"]
MINR = {1: 8, 8: 20, 12: 25, 15: 28, 18: 30, 20: 30}          # порог оценки варвара по уровням (отсечь мусор)
LOT = re.compile(r"^\s*(\d+)\. \[\s*(\d+)\] \(\s*(\d+)\)(?: !\s*(\d+)!)? (.+?)\s*$")


def main():
    lvls = [int(a) for a in sys.argv[1:]] or [1, 8, 12, 20]       # 18 убрано по просьбе пользователя; =20 включает всё до 20 лвл
    db = sqlite3.connect(K.DB)
    db.execute("create table if not exists exch_lots (lot int primary key, name text, price int, timer int, rating int, slot text, lvl int, ts text)")
    db.execute("""create table if not exists ex_items (name text primary key, title text, type text, slot text, minlvl int, req text, flags text,
        unique_flag int, special int, timer int, weight int, stars int, ac int, cut int, crush int, pierce int, mods text, rating text, forbid text, ts text)""")
    lots = {}
    for lvl in lvls:
        for sl in SLOTS:
            out = K.cmd_pages(f"биржа предл од *{sl} =варвар ={lvl} !{MINR.get(lvl, 20)}")
            for l in out.splitlines():
                m = LOT.match(l)
                if m:
                    lot, price, timer, rt, name = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4) or 0), m.group(5)
                    lots.setdefault(lot, (name, price, timer, rt, sl, lvl))
        print(f"уровень {lvl}: всего лотов {len(lots)}", flush=True)
    for lot, (name, price, timer, rt, sl, lvl) in lots.items():
        db.execute("insert or replace into exch_lots values (?,?,?,?,?,?,?,datetime('now'))", (lot, name, price, timer, rt, sl, lvl))
    db.commit()
    done = {r[0] for r in db.execute("select name from ex_items")}
    for lot, (name, price, timer, rt, sl, lvl) in sorted(lots.items(), key=lambda x: x[1][1]):
        if name in done:
            continue
        out = K.cmd(f"биржа инф {lot}")
        c = K.parse_card(out)
        if not c["title"]:
            continue
        done.add(name)
        db.execute("insert or replace into ex_items values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))",
                   (name, c["title"], c["type"], c["slot"], c["minlvl"], c["req"], c["flags"], c["unique"], c["special"], c["timer"],
                    c["weight"], c["stars"], c["ac"], c["cut"], c["crush"], c["pierce"], "; ".join(c["mods"]), c["rating"], c["forbid"]))
        db.commit()
        print(f"{name} (лот {lot}, {price}) | мин {c['minlvl']} АС {c['ac']} {'УНИК' if c['unique'] else ''} {c['slot']}", flush=True)


if __name__ == "__main__":
    main()
