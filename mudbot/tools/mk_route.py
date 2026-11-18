"""Маршрут из лога пользователя (JMC\\<имя>) -> data/db/routes/<имя>.json + текстовая сводка.

python tools/mk_route.py парк [аллея ...]     (без аргументов — все логи)

Шаги маршрута: {"move": "юг", "room": "Название"}, {"kill": ["Имя моба", ...]}, {"cmd": "область создать с"}.
Из хода пользователя убираем лишнее: неудавшиеся шаги, `смотреть`, возвраты назад без боя/команд между ними (А -> Б -> А).
Повторные заходы в одну и ту же комнату НЕ склеиваем (клетки без MSDP различимы только по названию), только возвраты.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
JMC = os.path.join(ROOT, "..", "JMC")
OUT = os.path.join(ROOT, "data", "db", "routes")

DIRS = {"север": "север", "с": "север", "юг": "юг", "ю": "юг", "запад": "запад", "з": "запад", "восток": "восток",
        "в": "восток", "вверх": "вверх", "вв": "вверх", "вниз": "вниз", "вн": "вниз"}
BACK = {"север": "юг", "юг": "север", "запад": "восток", "восток": "запад", "вверх": "вниз", "вниз": "вверх"}
CMD_RE = re.compile(r"^(област|обл |ехать|войт|вой |путь |отпер|откр |куп |изуч|уч |трен |осуш|кз |кс |од |сня |чин|заточ|сд |рерент|постой)")
FAIL = re.compile(r"Вы не можете идти|Дверь закрыта|закрыто|Вы слишком устали|не пускает вас|Вы не видите выхода|Вы встали")
KILL = re.compile(r"^(.*?) мертв[аоы]?\. R\.I\.P\.")
ROOM_ART = re.compile(r"^[\s+:|~^v@.mM%$\"_RGB()\-?!#*\\/<>=&]*$")


def parse(path):
    lines = open(path, encoding="cp1251", errors="replace").read().replace("\r", "").split("\n")
    steps, pending = [], []
    room = None
    start = None
    for i, raw in enumerate(lines):
        l = raw.strip()
        if not l:
            continue
        if l in DIRS:
            pending.append(("move", DIRS[l]))
        elif l in ("смотреть", "см", "оглядеться", "ос"):
            pending.append(("look", None))
        elif CMD_RE.match(l):
            steps.append({"cmd": l})
        elif FAIL.search(l) and pending:
            if pending[0][0] != "look":
                pending.pop(0)
        elif l.startswith("[ Exits:") and i:
            name = lines[i - 1].strip()
            prev_room = room
            if not name or ROOM_ART.match(name):
                continue
            kind = pending.pop(0) if pending else ("look", None)
            if start is None:
                start = prev_room if kind[0] == "move" else name
            room = name
            if kind[0] == "move":
                steps.append({"move": kind[1], "room": name})
        else:
            k = KILL.match(l)
            if k and not k.group(1).startswith(("Кто-то", "Вы")):
                if steps and "kill" in steps[-1]:
                    steps[-1]["kill"].append(k.group(1))
                else:
                    steps.append({"kill": [k.group(1)], "room": room})
    return start, steps


def prune(steps):
    """А -> Б -> А без боя между: убираем оба шага (возврат назад); повторяем, пока что-то убирается."""
    changed = True
    while changed:
        changed = False
        for i in range(len(steps) - 1):
            a, b = steps[i], steps[i + 1]
            if "move" in a and "move" in b and BACK[a["move"]] == b["move"]:
                del steps[i:i + 2]
                changed = True
                break
    return steps


def summary(steps):
    out, run = [], []
    for s in steps:
        if "move" in s:
            run.append(s["move"][0] if s["move"] != "вверх" else "вв")
            continue
        if run:
            out.append(" ".join(run))
            run = []
        out.append("УБИТЬ: " + ", ".join(sorted(set(s["kill"]))) if "kill" in s else "КОМАНДА: " + s["cmd"])
    if run:
        out.append(" ".join(run))
    return out


def main():
    names = sys.argv[1:] or [f for f in os.listdir(JMC) if os.path.isfile(os.path.join(JMC, f)) and "." not in f]
    os.makedirs(OUT, exist_ok=True)
    for n in names:
        start, steps = parse(os.path.join(JMC, n))
        steps = prune(steps)
        json.dump({"start": start, "steps": steps}, open(os.path.join(OUT, n + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
        moves = sum(1 for s in steps if "move" in s)
        kills = sum(len(s["kill"]) for s in steps if "kill" in s)
        open(os.path.join(OUT, n + ".txt"), "w", encoding="utf-8").write("\n".join(summary(steps)))
        print(f"{n}: шагов {moves}, убийств {kills}, команд {sum(1 for s in steps if 'cmd' in s)}")


if __name__ == "__main__":
    main()


