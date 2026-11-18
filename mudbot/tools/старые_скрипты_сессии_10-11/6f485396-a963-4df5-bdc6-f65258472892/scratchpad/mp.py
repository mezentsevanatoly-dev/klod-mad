import sqlite3, re
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
print(c.execute("select count(*) from mapper_rooms where zone='Тоннель бесов'").fetchone())
rx = re.compile(r"^\[msdp\] комната (\d+) \| ([^|]*) \|")
cells, kills = set(), {}
cur = None
for l in open(r"C:\Users\User\Desktop\Клод мад\mudbot\out.log", encoding="utf-8", errors="replace"):
    m = rx.match(l)
    if m:
        cur = (m.group(1), m.group(2).strip())
        if cur[1] == "Тоннель бесов":
            cells.add(cur[0])
    elif "R.I.P." in l and cur and cur[1] == "Тоннель бесов":
        kills[cur[0]] = kills.get(cur[0], 0) + 1
print(len(cells), len(kills), sorted(cells)[:5], sorted(cells)[-5:])
