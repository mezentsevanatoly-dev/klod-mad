"""Зачистить этаж/участок обходом в глубину по выходам MSDP: бой (fight_here), лут, отметка скрытых деталей.

python tools/sweep_floor.py <mob.csv> [макс_комнат]
Вертикальные выходы (U/D) НЕ используем — только горизонтальные внутри этажа. Использовать ТОЛЬКО там, где карта MUD Mapper
проверена на ДТ (после гибели в «Обрыве» — правило: в неизвестное без проверки не шагать). Запоминает, где скрытая деталь.
"""
import sys
import time

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import botp_walk as b  # noqa: E402
from explore_msdp import BACK  # noqa: E402

w = b.Walker(b.load_mobs(sys.argv[1]))
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 60
w.last_msdp_from_log()
seen = {w.cur["vnum"]}
details = []
items = []


def visit():
    w.fight_here()
    out = w.answer("смотреть краткий", 1.0)
    if any("скрытая деталь" in l for l in out):
        details.append((w.cur["vnum"], w.cur["name"]))
        print(f"  СКРЫТАЯ ДЕТАЛЬ: {w.cur['vnum']} {w.cur['name']}", flush=True)
    for l in w.answer("взять все", 1.0):
        if "взяли" in l and "монет" not in l:
            items.append(l.strip())
            print("   ", l.strip(), flush=True)


def dfs():
    v = w.cur["vnum"]
    for d, t in list(w.cur["exits"].items()):
        if d in ("U", "D") or t in seen or len(seen) > limit:
            continue
        seen.add(t)
        if not w.move(d):
            print(f"  не прошла {d} из {v}", flush=True)
            continue
        print(f"{w.cur['vnum']} {w.cur['name']}", flush=True)
        visit()
        dfs()
        w.move(BACK[d])
        w.fight_here()


visit()
dfs()
print(f"обошла {len(seen)} комнат; детали: {details}; вещи: {items}", flush=True)
