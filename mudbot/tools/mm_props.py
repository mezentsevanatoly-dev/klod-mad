"""Показать сырые поля комнат из .mm2 живого MUD Mapper: python tools/mm_props.py <зона>"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm2_read as m  # noqa: E402

zone = sys.argv[1]
rooms = m.read_mm2(os.path.join(m.MAPS, zone + ".mm2"))
print(len(rooms))
keys = {}
for r in rooms:
    for k in r:
        keys[k] = keys.get(k, 0) + 1
print(keys)
for r in rooms[:3]:
    print({k: (str(v)[:50]) for k, v in r.items()})
