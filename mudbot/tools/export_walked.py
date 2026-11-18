"""Разложить areas/msdp/_walked.json (все клетки, увиденные по MSDP) по зонам: areas/walked_by_zone/<зона>.json.

python tools/export_walked.py
Реальные vnum -> клетка (название, выходы): по ним сверять карты MUD Mapper, где vnum нет (только Tag).
"""
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
src = json.load(open(os.path.join(ROOT, "areas", "msdp", "_walked.json"), encoding="utf-8"))
out = os.path.join(ROOT, "areas", "walked_by_zone")
os.makedirs(out, exist_ok=True)
by = {}
for vnum, r in src.items():
    by.setdefault(r.get("area", "?"), {})[vnum] = r
n = 0
for area, rooms in by.items():
    name = "".join(c if c.isalnum() or c in " _-" else "_" for c in area).strip().replace(" ", "_")
    json.dump(dict(sorted(rooms.items())), open(os.path.join(out, name + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    n += 1
print(f"зон: {n}, комнат: {len(src)}")
for area, rooms in sorted(by.items(), key=lambda x: -len(x[1]))[:12]:
    print(len(rooms), area)
