"""Опыт за убийства из логов пользователя (JMC\\*, cp1251) -> таблица exp_obs (log, my_level, mob, exp).
Лвл берём из `сч` («Варвар N уровня») в логе и увеличиваем на 1 при «Вы поднялись на уровень!». python -X utf8 tools/exp_from_logs.py
"""
import os
import re
import sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JMC = os.path.join(os.path.dirname(ROOT), "JMC")
KILL = re.compile(r"^(.+?) мертв[аоы]?\. R\.I\.P\.")
EXP = re.compile(r"^Вы получили (\d+) единиц")
LV = re.compile(r"(?:Варвар|Воин|Рыцарь смерти|Друид|Маг|Клирик) (\d+) уровня")


def main():
    db = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
    db.execute("drop table if exists exp_obs")
    db.execute("create table exp_obs (log text, my_level int, mob text, exp int)")
    skip = {"changelog.txt", "перелив дк.txt", "Сборная солянка.txt"}
    total = 0
    lvl = 1                                                          # уровень сквозной: логи идут по времени (mtime), якоря — строки `сч`
    names = [n for n in os.listdir(JMC) if n not in skip and os.path.isfile(os.path.join(JMC, n)) and os.path.getsize(os.path.join(JMC, n)) >= 5000
             and "." not in n]
    for n in sorted(names, key=lambda x: os.path.getmtime(os.path.join(JMC, x))):
        p = os.path.join(JMC, n)
        t = open(p, "rb").read().decode("cp1251", errors="replace").replace("\r", "").split("\n")
        last, rows = None, []
        for l in t:
            s = l.strip()
            m = LV.search(s)
            if m and s.startswith("Вы "):
                lvl = int(m.group(1))                              # якорь: `сч` показывает текущий лвл
            if "Вы поднялись на уровень" in s:
                lvl += 1
            m = KILL.match(s)
            if m:
                last = m.group(1)
                continue
            m = EXP.match(s)
            if m and last and lvl:
                rows.append((n, lvl, last, int(m.group(1))))
                last = None
        db.executemany("insert into exp_obs values (?,?,?,?)", rows)
        total += len(rows)
        print(n, len(rows), "стартовый лвл", next((r[1] for r in rows), None), flush=True)
    db.commit()
    print("всего", total)


if __name__ == "__main__":
    main()
