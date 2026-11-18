import sqlite3, json, collections, shutil
exec(open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\mk_alley.py", encoding="utf-8").read().split("SRC =")[0])   # bfs, R, RU
SRC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\аллея"
T = r"C:\Users\User\Desktop\Тадия\areas"
V = [x for x in open(SRC + r"\рр_аллеяV.botp", "rb").read().decode("cp1251").splitlines() if x.strip()]
assert V[5] == ".триг обл с с" and "100069" in V[6] and "146001" in V[7], (V[5], V[6][:80], V[7][:80])
M = ("север", "юг", "восток", "запад", "вверх", "вниз")
cmds = [l.split("\t")[0].strip() for l in open(SRC + r"\аллея_cmds.txt", encoding="utf-8").read().splitlines() if l.strip()]
i0 = next(i for i, x in enumerate(cmds) if x.startswith("область создать"))
j = next(i for i in range(i0, len(cmds)) if cmds[i] == "вниз")
k = next(i for i in range(j, len(cmds)) if cmds[i] == "вверх")
cellar = [x for x in cmds[j:k + 1] if x in M]
print("погреб:", len(cellar), "ходов:", " ".join(cellar))
lines = [".триг #scr botCore.BotInZone = false"] + bfs("100076", "100009") + V[:7] + cellar + V[7:] + bfs("100009", "100076")
shutil.copyfile(T + r"\аллея.botp", T + r"\аллея.botp.bak_nocellar")
open(T + r"\аллея.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("всего строк", len(lines))
