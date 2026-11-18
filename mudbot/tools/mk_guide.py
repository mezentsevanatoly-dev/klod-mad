"""«Путь для нубов»: маршруты логов пользователя в виде спидволков со списком боёв -> data/db/путь_для_нубов.md.

python tools/mk_guide.py            (после tools/mk_route.py)
Для каждого лога (по дате изменения): старт, спидволк до клетки входа (до `область создать`), потом куски «спидволк — кого бьём».
Спидволк: n s e w u d, число = повтор (2es3w). Старт у всех логов — Склад Элендора (100076).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
JMC = os.path.join(ROOT, "..", "JMC")
DB = os.path.join(ROOT, "data", "db")
L = {"север": "n", "юг": "s", "восток": "e", "запад": "w", "вверх": "u", "вниз": "d"}


def compress(ds):
    out, i = "", 0
    while i < len(ds):
        j = i
        while j < len(ds) and ds[j] == ds[i]:
            j += 1
        out += (str(j - i) if j - i > 1 else "") + ds[i]
        i = j
    return out


def render(name, steps):
    lines, run, kills_total = [], [], 0
    def flush():
        nonlocal run
        if run:
            lines.append("  `" + compress(run) + "`")
            run = []
    for s in steps:
        if "move" in s:
            run.append(L[s["move"]])
        elif "kill" in s:
            flush()
            kills_total += len(s["kill"])
            cnt = {}
            for n in s["kill"]:
                cnt[n] = cnt.get(n, 0) + 1
            lines.append("  бить: " + ", ".join(f"{n}" + (f" ×{c}" if c > 1 else "") for n, c in cnt.items()))
        else:
            flush()
            lines.append("  команда: `" + s["cmd"] + "`")
    flush()
    return lines, kills_total


def main():
    logs = sorted((f for f in os.listdir(JMC) if os.path.isfile(os.path.join(JMC, f)) and "." not in f),
                  key=lambda f: os.path.getmtime(os.path.join(JMC, f)))
    out = ["# Путь для нубов (из логов пользователя, по порядку дат)", "",
           "Старт каждого лога — Склад Элендора (100076, гостиница «Три быка», север от холла). Спидволк: n s e w u d, число — повтор.",
           "«бить» — кто убит в клетке (имена из лога). Двери/области — строки «команда». Файлы: `routes/<лог>.json`.", ""]
    sw_lines = ["", "# Спидволки логов (tools/mk_guide.py): <лог>_вход — от Склада до клетки, где создаётся область/первый бой"]
    for n in logs:
        p = os.path.join(DB, "routes", n + ".json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        steps = d["steps"]
        lines, kills = render(n, steps)
        out += [f"## {n} (убийств {kills}, шагов {sum(1 for s in steps if 'move' in s)})"] + lines + [""]
        entry = []
        for s in steps:
            if "kill" in s or ("cmd" in s and "област" in s["cmd"]):
                break
            if "move" in s:
                entry.append(L[s["move"]])
        if entry:
            sw_lines.append(f"{n}_вход = {compress(entry)}")
    open(os.path.join(DB, "путь_для_нубов.md"), "w", encoding="utf-8").write("\n".join(out))
    sw = os.path.join(ROOT, "speedwalks.txt")
    text = open(sw, encoding="utf-8").read()
    text = re.sub(r"\n\n# Спидволки логов \(tools/mk_guide\.py\).*\Z", "", text, flags=re.S)
    open(sw, "w", encoding="utf-8").write(text + "\n".join(sw_lines) + "\n")
    print(f"логов: {len(logs)}; data/db/путь_для_нубов.md, спидволки добавлены в speedwalks.txt")


if __name__ == "__main__":
    main()
