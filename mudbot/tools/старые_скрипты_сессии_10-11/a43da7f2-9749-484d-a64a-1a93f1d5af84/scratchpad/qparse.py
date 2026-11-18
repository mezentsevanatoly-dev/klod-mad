"""Точный разбор хода по логу: очередь команд сопоставляется с результатами (комната/ошибка).
qparse.py <лог> [от] [до] -> scratchpad\q_<лог>.json = [(cmd, name, exits)] только удавшиеся ходы + двери"""
import re, sys, json, collections
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
name = sys.argv[1]
a = int(sys.argv[2]) if len(sys.argv) > 2 else 0
b = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
log = open(r"C:\Users\User\Desktop\Клод мад\JMC" + "\\" + name, "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
SH = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вв": "вверх", "вн": "вниз", "север": "север", "юг": "юг", "восток": "восток", "запад": "запад", "вверх": "вверх", "вниз": "вниз"}
LOOK = {"см", "смотреть", "look", "l", "смотр", "осм"}
q = collections.deque(); out = []
for i in range(a, min(b, len(log))):
    t = log[i].strip()
    if t in SH: q.append(("mv", SH[t], i)); continue
    if t in LOOK: q.append(("look", t, i)); continue
    if re.match(r"^(отпер|откр) \S+( \S+)?$", t): out.append((t, None, None, i)); continue
    if t.startswith("[ Exits"):
        if q:
            k = q.popleft()
            if k[0] == "mv":
                z = i - 1
                while z > i - 6 and log[z].strip().startswith("*"): z -= 1
                out.append((k[1], log[z].strip(), sorted(set(re.findall(r"\b[NSEWUD]\b", t))), k[2]))
        continue
    if re.match(r"^(Вы не можете идти|Попробуйте сначала|Вам нужно|Дверь закрыта|Вы слишком|Вы не в состоянии)", t):
        if q:
            while q and q[0][0] == "look": q.popleft()
            if q: q.popleft()
print("успешных ходов+команд:", len(out), "осталось в очереди:", len(q))
json.dump(out, open(S + r"\q_" + name + ".json", "w", encoding="utf-8"), ensure_ascii=False)
