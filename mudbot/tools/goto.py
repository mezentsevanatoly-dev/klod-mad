"""Дойти до комнаты по картам MSDP (все areas/msdp/*.json вместе): кратчайший путь по vnum, каждый шаг проверяем.

python tools/goto.py 100173            -> до комнаты с номером
python tools/goto.py "Город Элендор"   -> до ближайшей комнаты этой зоны
Шаг привёл не туда -> путь считается заново от фактической комнаты.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from explore_msdp import CMD, OUT, WALKED, Explorer  # noqa: E402


def world():
    rooms = {}
    for f in os.listdir(OUT):
        if f.endswith(".json") and not f.endswith("_loot.json") and f not in ("items.json", "_walked.json"):
            rooms.update(json.load(open(os.path.join(OUT, f), encoding="utf-8")).get("rooms", {}))
    try:                                    # пройденное вручную: только то, чего нет в картах зон
        for v, r in json.load(open(WALKED, encoding="utf-8")).items():
            rooms.setdefault(v, r)
    except Exception:
        pass
    return rooms


def path(rooms, start, goal):
    """Путь до vnum goal или до первой комнаты зоны goal; выход в неизвестную комнату годится только как цель."""
    prev, q = {start: None}, [start]
    while q:
        v = q.pop(0)
        if v == goal or rooms.get(v, {}).get("area") == goal:
            out = []
            while prev[v]:
                v, d = prev[v]
                out.append(d)
            return out[::-1]
        for d, t in rooms.get(v, {}).get("exits", {}).items():
            if d in CMD and t not in prev and (t in rooms or t == goal):
                prev[t] = (v, d)
                q.append(t)
    return None


def goto(ex, goal, rooms=None):
    rooms = rooms or world()
    for _ in range(5):
        ex.last_msdp_from_log() if not ex.cur else None
        if not ex.cur:
            sys.exit("нет данных MSDP")
        node = rooms.setdefault(ex.cur["vnum"], {})              # выходы текущей комнаты — живые, из MSDP
        node["exits"] = {k: str(t) for k, t in ex.cur["exits"].items()}   # (записанные могли устареть)
        p = path(rooms, ex.cur["vnum"], goal)
        if p is None:
            print(f"нет пути из {ex.cur['vnum']} до {goal}")
            return False
        for d in p:
            want = rooms[ex.cur["vnum"]]["exits"][d]
            moved = ex.move(d) or (ex.open_door(d) and ex.move(d))
            if not moved or ex.cur["vnum"] != want:
                break
            ex.safe()
        else:
            print(f"пришли: {ex.cur['vnum']} {ex.cur['area']} | {ex.cur['name']}")
            return True
    return False


if __name__ == "__main__":
    goto(Explorer(), sys.argv[1])
