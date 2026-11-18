"""Отладка: какие строки мобов из out.log hunt_luga считает целями (python tools/dbg_targets.py 17 23)."""
import collections
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hunt_luga  # noqa: E402

h = hunt_luga.BarbHunter(99, 1, False)
h.level = 21
h.min_lv, h.max_lv = int(sys.argv[1]), int(sys.argv[2])
hunt_luga.load_map(h)
lines = open(os.path.join(HERE, "..", "out.log"), encoding="utf-8", errors="replace").read().splitlines()[-9000:]
seen = collections.Counter()
hit = collections.Counter()
i = 0
while i < len(lines):
    if "[ Exits:" in lines[i]:
        j = i + 1
        while j < len(lines) and lines[j].strip() and not re.match(r"^\d+H ", lines[j]) and not lines[j].startswith("["):
            seen[lines[j].strip()[:70]] += 1
            t = h.target(lines[j])
            if t:
                hit[(lines[j].strip()[:60], t.get("level"))] += 1
            j += 1
        i = j
    i += 1
print("строк мобов:", sum(seen.values()), "уникальных:", len(seen))
print("ЦЕЛИ:", dict(hit))
print("не цели (топ):", seen.most_common(25))
