"""Проверка: насколько маршрут лога внутри зоны ложится на граф rooms (по названиям клеток и направлениям).
python -X utf8 tools/resolve_zone.py <лог> <vnum_входа>   -> сколько ходов не легло, куда, и список vnum маршрута
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import resolve_entries as RE  # noqa: E402

R, D, L = RE.R, RE.D, RE.L


def resolve(name, entry):
    steps = json.load(open(os.path.join(RE.RECON, name, name + "_route.json"), encoding="utf-8"))["steps"]
    k = next(i for i, s in enumerate(steps) if s.get("cmd", "").startswith("область создать"))
    cur, out, bad = entry, [], []
    for i, st in enumerate(steps[k + 1:], start=k + 1):
        if "move" not in st:
            continue
        t = R.get(cur, ("", "", {}))[2].get(D[st["move"]])
        hidden = st["room"].startswith("*")
        if t and t in R and (hidden or R[t][1] == st["room"]):
            out.append((i, st["move"], t))
            cur = t
        elif t and t in R:
            bad.append((i, "имя", st["move"], st["room"], R[t][1]))
            out.append((i, st["move"], t))       # верим графу, фиксируем расхождение имени
            cur = t
        else:
            bad.append((i, "нет выхода", st["move"], st["room"], cur))
    return out, bad


if __name__ == "__main__":
    out, bad = resolve(sys.argv[1], sys.argv[2])
    print(len(out), "ходов легло,", len(bad), "расхождений")
    for b in bad[:12]:
        print(b)
