"""Маршрут по графу зоны от текущей комнаты (последняя комната в out.log) до комнаты с названием.

python tools/route.py mad_school "Перед залом"   ->  печатает команды через ;
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mudbot.graph import ZoneGraph, room_key  # noqa: E402
from mudbot.parser import RoomParser  # noqa: E402

zone, target = sys.argv[1], sys.argv[2]
log = os.path.join(os.path.dirname(__file__), "..", "out.log")
rp, last = RoomParser(), None
for line in open(log, encoding="utf-8", errors="replace").read().splitlines()[-400:]:
    r = rp.feed(line)
    if r and r.name:
        last = r
g = ZoneGraph(zone)
if not last:
    sys.exit("текущая комната не найдена в out.log")
path = g.bfs(room_key(last), g.find(target))
print(";".join(path) if path is not None else f"нет пути из '{last.name}'")
