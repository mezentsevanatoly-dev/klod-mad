import json, sqlite3
P = json.load(open(r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\канал\raw_path.json", encoding="utf-8"))
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {v: e for v, e in c.execute("select vnum,exits from rooms")}
N = {v: n for v, n in c.execute("select vnum,name from rooms")}
last = max(i for i, (v, m) in enumerate(P) if v == "102002" and m == "вверх")
Q = P[: last + 1]
print("ходов до выхода:", len(Q), "| хвост (город) отброшен:", len(P) - len(Q))
seen = {v for v, _ in Q} | {"102002"}
zone = {v for v in N if "102002" <= v <= "102032"}
print("клеток зоны:", len(zone), "не тронуто:", [(v, N[v]) for v in sorted(zone - seen)])
print("первые 12:", Q[:12])
print("последние 6:", Q[-6:])
json.dump(Q, open(r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\канал\raw_path_cut.json", "w", encoding="utf-8"), ensure_ascii=False)
