"""Журнал прохода зоны: areas/runs/<зона>_<дата>.json + строка в areas/runs/index.tsv.

Пишет: задания до/после, пройденные клетки (шаг маршрута, vnum, название, выходы), мобы (строки комнат со счётчиком),
предметы в инвентаре до/после (лут), время и итог. Подключён в botp_walk.py (walk/main); реальные vnum -> таблица для
карт MUD Mapper (где vnum в .mm2 нет).
"""
import json
import os
import time
from datetime import datetime

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RUNS = os.path.join(ROOT, "areas", "runs")


def _j(w):
    if not hasattr(w, "journal"):
        w.journal = {"t0": time.time(), "steps": [], "mobs": {}, "quests0": None, "inv0": None, "notes": []}
    return w.journal


def _lines(w, cmd, wait=1.5):
    return [l.rstrip() for l in w.answer(cmd, wait) if l.strip() and "Вых:" not in l]


def begin(w):
    j = _j(w)
    j["t0"] = time.time()
    j["quests0"] = _lines(w, "задания")
    j["inv0"] = _lines(w, "инв")


def step(w, i, a, cmd):
    cur = w.cur or {}
    _j(w)["steps"].append({"step": i, "plan_vnum": a, "vnum": cur.get("vnum"), "name": cur.get("name"),
                           "exits": cur.get("exits"), "cmd": cmd[:80]})


def mobs(w, lines):
    m = _j(w)["mobs"]
    for l in lines:
        l = l.strip()
        if l and not l.startswith("Труп"):
            m[l] = m.get(l, 0) + 1


def note(w, text):
    _j(w)["notes"].append(text)


def end(w, result=""):
    j = _j(w)
    area = (w.cur or {}).get("area", "зона")
    os.makedirs(RUNS, exist_ok=True)
    quests1 = _lines(w, "задания")
    inv1 = _lines(w, "инв")
    old = set(j.get("inv0") or [])
    data = {"zone": area, "start": datetime.fromtimestamp(j["t0"]).isoformat(timespec="seconds"),
            "minutes": round((time.time() - j["t0"]) / 60, 1), "result": result,
            "quests_before": j.get("quests0"), "quests_after": quests1,
            "loot_new_inventory": [l for l in inv1 if l not in old], "mobs_seen": j["mobs"],
            "steps": j["steps"], "notes": j["notes"]}
    name = f"{area}_{datetime.now():%Y-%m-%d_%H%M}".replace(" ", "_")
    path = os.path.join(RUNS, name + ".json")
    json.dump(data, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(RUNS, "index.tsv"), "a", encoding="utf-8") as f:
        f.write(f"{data['start']}\t{area}\t{data['minutes']}\t{len(j['steps'])}\t{len(j['mobs'])}\t{result}\t{name}.json\n")
    return path
