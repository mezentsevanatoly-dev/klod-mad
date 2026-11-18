import json, sqlite3, os, shutil
base = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon"
P = json.load(open(base + r"\болото_часть\raw_path.json", encoding="utf-8"))
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
N = {v: n for v, n in c.execute("select vnum,name from rooms")}
Z = {v for v, z in c.execute("select vnum,zone from rooms") if z == "Болото"}
ends = [i for i, (v, m) in enumerate(P) if v == "111093" and m == "север"]
print("выходов на север из 111093:", ends[:10])
last = ends[-1] if ends else len(P) - 1
Q = P[: last + 1]
seen = {v for v, _ in Q}
print("ходов:", len(Q), "| клеток болота в БД:", len(Z), "| не тронуто:", [(v, N[v]) for v in sorted(Z - seen, key=int)])
print("первые:", Q[:6], "последние:", Q[-4:])
json.dump(Q, open(base + r"\болото_часть\raw_path_cut.json", "w", encoding="utf-8"), ensure_ascii=False)
