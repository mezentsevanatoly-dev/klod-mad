# -*- coding: utf-8 -*-
"""Все реплики пользователя из user_phrases.md + user_phrases_live.md без повторов, по времени -> data/фразы_все_без_повторов.md"""
import os, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
seen = {}
for fn in ("user_phrases.md", "user_phrases_live.md"):
    cur = None
    for s in open(os.path.join(D, fn), encoding="utf-8", errors="replace"):
        m = re.match(r"^- \[(\d{4}-\d\d-\d\dT\d\d:\d\d)(?::\d\d)?\] ?(.*)$", s.rstrip("\n"))
        if m:
            cur = [m.group(1), m.group(2)]
            key = re.sub(r"\W+", "", m.group(2).lower())[:160]
            if key and key not in seen:
                seen[key] = cur
            else:
                cur = None
        elif cur is not None and s.strip() and not s.startswith(("#", "- [")):
            cur[1] += " " + s.strip()
rows = sorted(seen.values())
out = os.path.join(D, "фразы_все_без_повторов.md")
with open(out, "w", encoding="utf-8") as f:
    for t, x in rows:
        f.write("- [%s] %s\n" % (t, x))
print(len(rows), "реплик ->", out, os.path.getsize(out) // 1024, "КБ")
