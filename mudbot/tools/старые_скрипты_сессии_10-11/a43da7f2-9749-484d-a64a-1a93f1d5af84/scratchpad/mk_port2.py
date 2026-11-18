import re, json, sqlite3, collections
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\порт", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
SH = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вв": "вверх", "вн": "вниз", "север": "север", "юг": "юг", "восток": "восток", "запад": "запад", "вверх": "вверх", "вниз": "вниз"}
MV = set(SH.values())
cmds = []
for i in range(1514 - 1, 6830):
    s = log[i].strip()
    k = SH.get(s)
    isd = re.match(r"^(отпер|откр) \S+( \S+)?$", s)
    if not (k or isd): continue
    # следующая непустая строка не про промах
    j = i + 1
    nxt = ""
    while j < len(log) and not log[j].strip(): j += 1
    nxt = log[j].strip() if j < len(log) else ""
    if re.match(r"^(Вы не можете идти|Закрыто|Дверь закрыта|Вы слишком|Вы не можете)", nxt) and not isd:
        continue
    cmds.append(k or s)
print("команд:", len(cmds), "ходов:", sum(1 for x in cmds if x in MV))
open(S + r"\port_cmds.txt", "w", encoding="utf-8").write("\n".join(cmds))
# проверка по графу
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
INV = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
cur = "100053"; bad = []
for n, x in enumerate(cmds):
    if x in MV:
        t = R.get(cur, {}).get(INV[x])
        if t is None: bad.append((n, cur, x))
        else: cur = str(t)
print("конец:", cur, "промахов по графу:", bad[:10])
