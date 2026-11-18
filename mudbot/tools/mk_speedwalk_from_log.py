"""Спидволк из пройденного пути: комнаты по MSDP из out.log между двумя vnum.

  python tools/mk_speedwalk_from_log.py <vnum_начала> <vnum_конца> "<имя>"
Берёт последнее прохождение (последняя запись начала, затем конец). Записывает в speedwalks.txt (формат `имя = 2ws3w @ vnum`)
и в таблицу speedwalks game.db; добавляет обратный `имя_обратно`.
"""
import ast
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "out.log")
RE = re.compile(r"^\[msdp\] комната (\d+) \| (.*?) \| (.*?) \| (\{.*\})\s*$")
BACK = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}
LET = {"N": "n", "S": "s", "E": "e", "W": "w", "U": "u", "D": "d"}


def compress(dirs):
    out, i = "", 0
    while i < len(dirs):
        j = i
        while j < len(dirs) and dirs[j] == dirs[i]:
            j += 1
        n = j - i
        out += (str(n) if n > 1 else "") + LET[dirs[i]]
        i = j
    return out


def main(a, b, name):
    rooms = []
    for l in open(OUT, encoding="utf-8", errors="replace"):
        m = RE.match(l.strip())
        if m:
            rooms.append((m.group(1), m.group(2), m.group(3), ast.literal_eval(m.group(4))))
    # последнее вхождение начала, после него первое вхождение конца
    si = max((i for i, r in enumerate(rooms) if r[0] == a), default=None)
    if si is None:
        sys.exit("начало не найдено в логе")
    ei = next((i for i in range(si, len(rooms)) if rooms[i][0] == b), None)
    if ei is None:
        sys.exit("конец после начала не найден")
    seq = rooms[si:ei + 1]
    # убрать петли (вернулись в уже пройденную комнату)
    clean = []
    for r in seq:
        k = next((i for i, x in enumerate(clean) if x[0] == r[0]), None)
        if k is not None:
            clean = clean[:k + 1]
        else:
            clean.append(r)
    dirs = []
    for x, y in zip(clean, clean[1:]):
        d = next((dd for dd, v in x[3].items() if str(v) == y[0]), None)
        if not d:
            sys.exit(f"нет выхода из {x[0]} в {y[0]}")
        dirs.append(d)
    fwd = compress(dirs)
    rev = compress([BACK[d] for d in reversed(dirs)])
    line = f"{name} = {fwd} @ {b}\n{name}_обратно = {rev} @ {a}\n"
    open(os.path.join(HERE, "speedwalks.txt"), "a", encoding="utf-8").write(f"# {clean[0][2]} -> {clean[-1][2]} ({len(dirs)} шагов)\n" + line)
    c = sqlite3.connect(os.path.join(HERE, "data", "game.db"))
    c.execute("INSERT INTO speedwalks VALUES (?,?,?,?)", (name, fwd, b, f"{clean[0][1]}: {clean[0][2]} -> {clean[-1][2]}"))
    c.execute("INSERT INTO speedwalks VALUES (?,?,?,?)", (name + "_обратно", rev, a, ""))
    c.commit()
    print(f"{name}: {fwd}  ({len(dirs)} шагов)")
    print(f"{name}_обратно: {rev}")
    for r in clean:
        print("  ", r[0], r[1], "|", r[2])


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], sys.argv[2], sys.argv[3])
