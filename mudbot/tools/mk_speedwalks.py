"""Спидволки от склада Геоланта (115092) до клеток входа в зоны и обратно -> speedwalks.txt.

python tools/mk_speedwalks.py [старт_vnum]       (по умолчанию 115092, Геолант, Склад)
Клетка входа зоны = комната вне зоны, куда ведёт выход из стартовой комнаты зоны (areas/msdp/<Зона>.json, «start»); именно там
создаётся область. Путь — кратчайший по картам MSDP (goto.world/path); города и зоны без пешего пути от старта пропускаются.
Имена: `гео_<зона>` (туда) и `<зона>_гео` (обратно, до склада). Уже записанные не дублируются. Запуск: `!sw гео_<зона>`.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import goto as g  # noqa: E402
from explore_msdp import OUT  # noqa: E402

ROOT = os.path.dirname(HERE)
SW = os.path.join(ROOT, "speedwalks.txt")
OPP = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}


def compress(dirs):
    s, i = "", 0
    dirs = [d.lower() for d in dirs]
    while i < len(dirs):
        j = i
        while j < len(dirs) and dirs[j] == dirs[i]:
            j += 1
        s += (str(j - i) if j - i > 1 else "") + dirs[i]
        i = j
    return s


def main():
    start = sys.argv[1] if len(sys.argv) > 1 else "115092"
    rooms = g.world()
    have = open(SW, encoding="utf-8").read()
    tasks = set()                                          # только зоны из `задания все` (польз.), а не всё, что мы разведали
    for l in open(os.path.join(ROOT, "areas", "tasks_all_2026-11-01.txt"), encoding="utf-8-sig"):
        m = re.match(r'\s*\d+\. Задание "(.+?)"(?: \(зона "(.+?)"\))?\.', l)
        if m:
            tasks.add(re.sub(r"\s+", " ", (m[2] or m[1]).lower().replace("ё", "е")))
    lines, table = [], []
    for f in sorted(os.listdir(OUT)):
        if not f.endswith(".json") or f.endswith("_loot.json") or f in ("items.json", "_walked.json") or f.startswith("Город_"):
            continue
        z = json.load(open(os.path.join(OUT, f), encoding="utf-8"))
        zr = z.get("rooms", {})
        st = str(z.get("start", ""))
        if st not in zr or z.get("area", "").startswith(("Дорога", "Южная дорога")):
            continue
        if re.sub(r"\s+", " ", z.get("area", "").lower().replace("ё", "е")) not in tasks:
            continue
        outer = next((str(t) for d, t in zr[st]["exits"].items() if str(t) not in zr), None)
        if not outer or outer not in rooms:
            table.append((z["area"], "нет клетки входа в картах"))
            continue
        there = g.path(rooms, start, outer)
        back = g.path(rooms, outer, start)
        name = re.sub(r"\s+", "_", z["area"].lower())
        if there is None:
            table.append((z["area"], f"вход {outer}: пешего пути от {start} нет"))
            continue
        a, b = compress(there), compress(back) if back else None
        row = f'{name}: вход {outer} ({rooms[outer].get("name", "?")}), туда {len(there)} шагов' + (f", обратно {len(back)}" if back else ", обратно нет")
        table.append((z["area"], row))
        if f"гео_{name} =" not in have:
            lines.append(f"# {z['area']}: от {start} (Склад) до {outer} {rooms[outer].get('name', '')}; обратно до склада")
            lines.append(f"гео_{name} = {a} @ {outer}")
            if b:
                lines.append(f"{name}_гео = {b} @ {start}")
    if lines:
        with open(SW, "a", encoding="utf-8") as fh:
            fh.write("\n# Склад Геоланта <-> входы в зоны (tools/mk_speedwalks.py)\n" + "\n".join(lines) + "\n")
    for a, row in table:
        print(a, "|", row)
    print(f"записано строк: {len(lines)}")


if __name__ == "__main__":
    main()
