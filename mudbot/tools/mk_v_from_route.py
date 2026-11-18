"""V-маршрут (с проверкой $MsdpRoomVnum) из маршрута log_prep (<имя>_route.json) и графа комнат из out.log (MSDP).

python -X utf8 tools/mk_v_from_route.py <имя> <старт_vnum> "<подход>" <выход.botp> <срезы шагов, напр. 35-86,87-88,164-166> [--out-log путь]
  подход: движение до клетки создания области (спидволк, напр. 2n13es8es4es4e2sw), клетки считаются по графу
Граф = последние [msdp] комната … в out.log (выходы комнат, реально виденные в прогонах). Если ход ведёт в неизвестную
клетку или выхода нет, печатаем место и останавливаем сборку (V-маршрут по гадательной клетке даёт вечное ожидание).
Результат: <выход.botp> (cp1251) в формате Чвырлы.
"""
import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
SW = {"n": "север", "s": "юг", "e": "восток", "w": "запад", "u": "вверх", "d": "вниз"}
V = ("#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};"
     "#if {{$MsdpRoomVnum == {v}}} {{{cmd}}}")


def graph(path):
    g = {}
    rx = re.compile(r"^\[msdp\] комната (\d+) \| ([^|]*) \| ([^|]*) \| (\{.*\})\s*$")
    for l in open(path, encoding="utf-8", errors="replace"):
        m = rx.match(l)
        if m:
            try:
                ex = ast.literal_eval(m.group(4))
            except Exception:
                continue
            g[m.group(1)] = (m.group(2).strip(), m.group(3).strip(), {k.upper(): str(v) for k, v in ex.items()})
    return g


def expand(sw):
    return [SW[ch] for n, ch in re.findall(r"(\d*)([nsewud])", sw) for _ in range(int(n or 1))]


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    name, cur, approach, out, spans = a[0], a[1], a[2], a[3], a[4]
    outlog = sys.argv[sys.argv.index("--out-log") + 1] if "--out-log" in sys.argv else os.path.join(ROOT, "out.log")
    g = graph(outlog)
    if "--extra" in sys.argv:                 # скрытые выходы «клетка:напр:куда,…» (после повернуть/нажать их нет в последнем MSDP)
        for e in sys.argv[sys.argv.index("--extra") + 1].split(","):
            r, d, t = e.split(":")
            g[r][2][d] = t
    route = json.load(open(os.path.join(ROOT, "data", "recon", name, name + "_route.json"), encoding="utf-8"))["steps"]
    items = [("move", m) for m in expand(approach)] if approach else []
    items.append(("cmd", ".триг обл с с"))
    for sp in spans.split(","):
        if sp.startswith(("c:", "m:")):       # c:команда — вставить команду, m:ход — вставить ход (скрытые выходы после нажатия)
            items.append(("cmd" if sp[0] == "c" else "move", sp[2:]))
            continue
        lo, hi = (int(x) for x in sp.split("-"))
        for st in route[lo:hi + 1]:
            if "move" in st:
                items.append(("move", st["move"]))
            elif "cmd" in st and not st["cmd"].startswith("область"):
                items.append(("cmd", st["cmd"]))
    if "--back" in sys.argv:                  # возврат к старту: подход в обратном порядке
        inv = {"север": "юг", "юг": "север", "восток": "запад", "запад": "восток", "вверх": "вниз", "вниз": "вверх"}
        items += [("move", inv[m]) for k, m in reversed([i for i in items[:len(expand(approach))]])]
    lines, log = [], []
    for kind, val in items:
        if kind == "cmd":
            lines.append(val if val.startswith(".") else val)
            continue
        ex = g.get(cur, ("", "", {}))[2]
        nxt = ex.get(D[val])
        if not nxt or nxt not in g:
            skipped = locals().get("skipped", 0) + 1
            print(f"пропуск хода «{val}» из {cur} ({g.get(cur, ('', '?', {}))[1]}): выхода нет в графе (повтор неудавшегося хода в логе?)")
            log.append(f"{cur} {g.get(cur, ('', '?', {}))[1]} -> {val} ПРОПУЩЕН")
            if skipped > 3:
                print("слишком много пропусков, стоп")
                break
            continue
        lines.append(V.format(v=cur, cmd=val))
        log.append(f"{cur} {g[cur][1]} -> {val} -> {nxt} {g[nxt][1]}")
        cur = nxt
    with open(out, "w", encoding="cp1251", newline="\r\n") as f:
        f.write("\n".join(lines) + "\n")
    with open(out + ".trace.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(log) + f"\nконец: {cur} {g.get(cur, ('', '?', {}))[1]}\n")
    print(f"шагов {len(lines)}, конец {cur} {g.get(cur, ('', '?', {}))[1]} -> {out}")


if __name__ == "__main__":
    main()
