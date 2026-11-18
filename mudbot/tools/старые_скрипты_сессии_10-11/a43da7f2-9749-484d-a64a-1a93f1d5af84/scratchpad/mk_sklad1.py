import re, json, collections, sqlite3
exec(open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\mk_alley.py", encoding="utf-8").read().split("SRC =")[0])   # R, RU, bfs
REC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon"
T = r"C:\Users\User\Desktop\Тадия\areas"
RUN = {"n": "север", "s": "юг", "e": "восток", "w": "запад", "u": "вверх", "d": "вниз"}

def sw(s):
    out = []
    for n, d in re.findall(r"(\d*)([nsewud])", s):
        out += [RUN[d]] * (int(n) if n else 1)
    return out

to_hub = bfs("100076", "100009")
road = sw("22es7e3s22e")                       # элен_цп-гео_цп, конец 115039
to_door = sw("4e4se")                          # площадь Геоланта -> 115080 «Перед складом»
zone = [l.strip() for l in open(REC + r"\склад1\raw_moves.txt", encoding="utf-8") if l.strip()]
OPP = {"север": "юг", "юг": "север", "восток": "запад", "запад": "восток"}
back_door = [OPP[m] for m in reversed(to_door)]
road_back = sw("22w3n7wn22w")
to_stor = bfs("100009", "100076")
lines = ([".триг #scr botCore.BotInZone = false"] + to_hub + road + to_door + [".триг обл с в"] + zone + back_door + road_back + to_stor)
open(T + r"\склад1.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
idx_area = 1 + len(to_hub) + len(road) + len(to_door)
print("botp строк:", len(lines), "| хаб:", len(to_hub), "| дорога:", len(road), "| к двери:", len(to_door), "| индекс обл:", idx_area, "| зона:", len(zone))
