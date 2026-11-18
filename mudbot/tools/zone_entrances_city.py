"""Спидволки от центральной площади города (р2 Геолант, р4 Огис) до клетки входа в зону и обратно. Без реколла и поездок:
персонаж уже в городе; после каждой зоны возвращается на площадь по только что посчитанному обратному пути.
  python tools/zone_entrances_city.py Геолант "Катакомбы Геоланта:катакомбы" "Чайный домик:чайный домик" ...
Вход определяется игрой (`путь вход в зону <имя>` -> клетка с [Зона, <напр>: <Зона>]), маршрут — по графу rooms (BFS).
"""
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
import zone_entrances as ze
import zone_survey as zs

HUBS = {"Геолант": ("115039", "гео_цп", "Город Геолант"), "Огис": ("180096", "огис_цп", "Город Огис")}


def sw(path, wait=25):
    zs.cmd([f"!sw {path}"], wait)


def main(city, items):
    hub, hname, area = HUBS[city]
    g = ze.graph()
    if zs.where()[0] != hub:
        v0 = zs.where()[0]
        p = ze.bfs(g, v0, hub)
        if p:
            sw(ze.compress(p))
    for it in items:
        zone, entrance = it.split(":")
        zs.cmd([f"путь вход в зону {entrance}"], 60)
        v, a, name = zs.where()
        o = zs.cmd(["смотреть"], 2)
        m = re.search(r"\[Зона, (?:на )?([а-я]+): " + re.escape(zone) + r",? ?(ур\. ?[\d-]+)?", o)
        if not v or not m:
            zs.say(f"{zone}: вход не найден (комната {v} {a} {name})")
            continue
        fwd = ze.bfs(g, hub, v)
        if fwd is None:
            zs.say(f"{zone}: {v} не достижим из площади по графу")
            continue
        back = [ze.OPP[d] for d in reversed(fwd)]
        base = f"{hname}-{zone.replace(' ', '_')}"
        ze.save(base + "_область", ze.compress(fwd), v, f"клетка создания области «{zone}» ({m.group(2) or ''}); выход в зону: {m.group(1)}; {v} {name}")
        ze.save(base.replace(hname + "-", "") + "_область-" + hname, ze.compress(back), hub, "обратно к центральной площади")
        zs.say(f"{zone}: {ze.compress(fwd)} | обратно {ze.compress(back)} | {v} {name} {m.group(1)} {m.group(2) or ''}")
        sw(ze.compress(back), 40)
        zs.say("  на площади:", zs.where()[0] == hub)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main(sys.argv[1], sys.argv[2:])
