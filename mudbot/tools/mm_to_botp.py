"""Дописать номера клеток в маршрут Чвырлы без vnum: прогон по карте MUD Mapper -> .botp в формате `#if {$MsdpRoomVnum ==N} {команды}`.

python tools/mm_to_botp.py <зона> <botp_без_vnum> <с_строки> <по_строку> <id_старта> <база_vnum> <vnum_до_входа> <выход.botp>
Строка 1 вывода — вход из клетки <vnum_до_входа> (первая команда исходной строки с_строки). Дальше клетка перед каждой строкой.
Файл пишется в cp1251, как у Чвырлы (load_steps читает его так же). Ошибки прогона (нет выхода/клетки) печатаются и останавливают разметку.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm_sim as m  # noqa: E402

FLIP = (True, False, False)           # для Кладбища подобрано mm_sim.py (обмен осей x/y)


def main():
    zone, botp, a, b, start, base, outside, out = sys.argv[1:9]
    a, b, start, base = int(a), int(b), int(start), int(base)
    rooms, by = m.load(zone)
    src = open(botp, encoding="cp1251").read().splitlines()
    cur, lines, errors = rooms[start], ["#if {$MsdpRoomVnum ==%s} {#var SumReset 0}" % outside], []
    for i in range(a - 1, b):
        l = src[i].strip()
        if not l:
            continue
        is_trig = l.startswith(".триг")
        cmds = [c.strip().replace("подкр ", "") for c in (l[5:] if is_trig else l).split(";")]
        if is_trig:                          # в триггерах тоже бывают шаги («откр дверь;подкр юг») — позицию двигаем
            lines.append(l)
            for c in cmds:
                d = m.RU.get(c.strip())
                if d:
                    n = m.neighbor(cur, d, by, FLIP) if cur["links"].get(d) else None
                    if n is None:
                        errors.append(f"строка {i + 1} (триг): из {base + cur['id']} {c} — нет выхода/клетки")
                        break
                    cur = n
            if errors:
                break
            continue
        here = outside if (i == a - 1) else str(base + cur["id"])
        if i == a - 1:                       # первая строка — вход в зону из соседней клетки
            lines.append("#if {$MsdpRoomVnum ==%s} {%s}" % (here, l))
            continue
        lines.append("#if {$MsdpRoomVnum ==%s} {%s}" % (here, l))
        for c in cmds:
            d = m.RU.get(c)
            if not d:
                continue
            n = m.neighbor(cur, d, by, FLIP) if cur["links"].get(d) else None
            if n is None:
                errors.append(f"строка {i + 1}: из {base + cur['id']} {c} — нет выхода/клетки")
                break
            cur = n
        if errors:
            break
    with open(out, "w", encoding="cp1251", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"строк: {len(lines)}, ошибок: {len(errors)}, последняя клетка: {base + cur['id']} {cur['name']}")
    for e in errors:
        print(e)


if __name__ == "__main__":
    main()
