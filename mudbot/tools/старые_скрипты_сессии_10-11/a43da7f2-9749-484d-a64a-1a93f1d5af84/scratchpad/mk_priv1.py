import re, json, collections, sqlite3, shutil
exec(open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\mk_alley.py", encoding="utf-8").read().split("SRC =")[0])   # R, RU, bfs
REC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon"
T = r"C:\Users\User\Desktop\Тадия\areas"
RUN = {"n": "север", "s": "юг", "e": "восток", "w": "запад", "u": "вверх", "d": "вниз"}
OPP = {"север": "юг", "юг": "север", "восток": "запад", "запад": "восток", "вверх": "вниз", "вниз": "вверх"}
def sw(s): return [RUN[d] for n, d in re.findall(r"(\d*)([nsewud])", s) for _ in range(int(n) if n else 1)]
go = bfs("115092", "115039")
appr = sw("9ne2ne2ne")
zone = [l.strip() for l in open(REC + r"\привы1\raw_moves.txt", encoding="utf-8") if l.strip()]
back_appr = [OPP[m] for m in reversed(appr)]
back = bfs("115039", "115092")
lines = [".триг #scr botCore.BotInZone = false"] + go + appr + [".триг обл с в"] + zone + back_appr + back
open(T + r"\привы1.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("botp строк:", len(lines), "| к складу->площадь:", go, "| подход:", len(appr), "| зона:", len(zone), "| индекс обл:", 1 + len(go) + len(appr))
rows = open(REC + r"\привы1\привы1_mob_fixed.csv", "rb").read().decode("cp1251").split("\r\n")
orig = {r.split(";")[0].strip('"'): r.split(";") for r in open(REC + r"\привы1\рр_привы1V_mob.csv", "rb").read().decode("cp1251").split("\r\n")[1:] if r.strip()}
out = [r for r in rows if r.strip()]
t = list(orig["Любопытная трясогузка"]); t[1] = '"Необычайно любопытная трясогузка рассматривает вас. "'
out.append(";".join(t))
open(T + r"\привы1_mob.csv", "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
for r in out[1:]: print("  ", r.split(";")[0], "|", r.split(";")[1])
# словарь ПнП + AreaGuard
q = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
s = open(q, "rb").read().decode("cp1251")
a = "/Громилы/, "
assert s.count(a) == 1
s = s.replace(a, a + "/Хрупкий шпиль/, /малейшей опасности\\./, /Вдова разрыдалась\\./, ")
open(q, "wb").write(s.encode("cp1251"))
g = r"C:\Users\User\Desktop\Тадия\scripts\AreaGuard.js"
t2 = open(g, "rb").read().decode("cp1251")
if '"привы1"' not in t2:
    t2 = t2.replace('"склад1": "Склад в Геоланте"}', '"склад1": "Склад в Геоланте", "привы1": "Дом с привидениями"}').replace('"склад1": 1}', '"склад1": 1, "привы1": 1}')
    open(g, "wb").write(t2.encode("cp1251"))
print("ok")
