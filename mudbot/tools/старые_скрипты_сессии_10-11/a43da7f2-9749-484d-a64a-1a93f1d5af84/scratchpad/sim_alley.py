import sqlite3, json, re
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {r[0]: json.loads(r[1] or "{}") for r in c.execute("select vnum,exits from rooms")}
D = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
cmds = [l.split("\t")[0].strip() for l in open(r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\аллея\аллея_cmds.txt", encoding="utf-8").read().splitlines() if l.strip()]
# старт: после «область создать с» стоим в 100069
i0 = next(i for i, x in enumerate(cmds) if x.startswith("область создать"))
cur = "100069"
path = []
bad = []
for x in cmds[i0 + 1:]:
    if x in D:
        nxt = R.get(cur, {}).get(D[x])
        if nxt is None:
            bad.append((len(path), cur, x)); continue
        path.append((cur, x)); cur = str(nxt)
print("ходов:", len(path), "конец:", cur, "невозможных:", bad[:10])
seen = {p[0] for p in path} | {cur}
zone = {v for v in R if v.startswith("146")}
print("клеток зоны 146xxx:", len(zone), "не посещено:", sorted(zone - seen))
json.dump(path, open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\alley_path.json", "w"), ensure_ascii=False)
print(path[:12], "...", path[-6:])
