import re
rx = re.compile(r"^\[msdp\] комната (\d+) \| ([^|]*) \| ([^|]*) \| (\{.*\})\s*$")
lines = open(r"C:\Users\User\Desktop\Клод мад\mudbot\out.log", encoding="utf-8", errors="replace").read().splitlines()
hist = []
for i, l in enumerate(lines):
    m = rx.match(l)
    if m:
        hist.append((i, m.group(1), m.group(3).strip(), m.group(4)))
    if "переместились в пространстве" in l:
        prev = hist[-1] if hist else None
        # следующая комната
        nxt = next((rx.match(x) for x in lines[i:i + 40] if rx.match(x)), None)
        print("ТЕЛЕПОРТ на строке", i, "из", prev[1:3] if prev else None, "→", (nxt.group(1), nxt.group(3)) if nxt else None, "exits_prev", prev[3] if prev else None)
