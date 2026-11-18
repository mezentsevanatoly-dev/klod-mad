"""Пересобрать V-маршруты по накопленным клеткам боя (без игры): python -X utf8 tools/recon_rebuild.py [лог ...]"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recon_all as R  # noqa: E402

for name, kind, sw, entry, expect in R.QUEUE:
    if len(sys.argv) > 1 and name not in sys.argv[1:]:
        continue
    area_cmd = None
    if expect is not None:
        route = json.load(open(os.path.join(R.RECON, name, name + "_route.json"), encoding="utf-8"))["steps"]
        k = next((i for i, s in enumerate(route) if s.get("cmd", "").startswith("область создать")), None)
        if k is not None:
            c = route[k]["cmd"].split()
            d = c[2] if len(c) > 2 and "<" not in c[2] else next((s["move"] for s in route[k + 1:] if "move" in s), "с")
            area_cmd = {"север": "с", "юг": "ю", "восток": "в", "запад": "з", "вверх": "вв", "вниз": "вн", "вни": "вн"}.get(d, d)
    print(name, R.build_tour(name, kind, sw, entry, area_cmd, None))
