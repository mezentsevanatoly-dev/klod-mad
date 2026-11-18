import json, collections, shutil, sqlite3
exec(open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\mk_alley.py", encoding="utf-8").read().split("SRC =")[0])   # bfs, R, RU
SRC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\аллея"
T = r"C:\Users\User\Desktop\Тадия\areas"
V = [x for x in open(SRC + r"\рр_аллеяV.botp", "rb").read().decode("cp1251").splitlines() if x.strip()]
assert V[5] == ".триг обл с с" and "100069" in V[6] and "146001" in V[7]
# ходы погреба по сырому логу пользователя (log_prep терял часть «восток»)
cellar = "вниз запад север север юг запад запад восток восток юг север юг юг юг север запад запад восток восток север север юг восток вверх".split()
D = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
cur, seen = "146001", {"146001"}
for m in cellar:
    nxt = R[cur].get(D[m]); assert nxt, (cur, m)
    cur = str(nxt); seen.add(cur)
assert cur == "146001", cur
cellar_rooms = {v for v in R if "146011" <= v <= "146021" or v == "146037"}
print("погреб: ходов", len(cellar), "не посещены:", sorted(cellar_rooms - seen))
lines = [".триг #scr botCore.BotInZone = false"] + bfs("100076", "100009") + V[:7] + cellar + V[7:] + bfs("100009", "100076")
open(T + r"\аллея.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
i_cellar = 1 + len(bfs("100076", "100009")) + 7
print("строк", len(lines), "; первый ход погреба — индекс", i_cellar, "; 9-й ход погреба (следующий после 8) — индекс", i_cellar + 8)
