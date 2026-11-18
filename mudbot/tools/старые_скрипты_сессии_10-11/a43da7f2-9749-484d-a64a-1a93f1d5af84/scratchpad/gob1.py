import re, json, sqlite3, collections
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
print(c.execute("select zone,count(*),min(vnum),max(vnum) from rooms where zone like '%гоблин%' group by zone").fetchall())
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
NM = {str(v): n for v, n in c.execute("select vnum,name from rooms")}
Z = {str(v) for (v,) in c.execute("select vnum from rooms where zone like '%гоблин%'")}
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\гоблины", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
SH = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вв": "вверх", "вн": "вниз"}
MV = {"север", "юг", "восток", "запад", "вверх", "вниз"}
INV = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
cmds = []
for i in range(0, 4650):
    s = log[i].strip(); k = SH.get(s, s)
    if k in MV or re.match(r"^(отпер|откр) \S+( \S+)?$", s):
        j = i + 1
        while j < len(log) and not log[j].strip(): j += 1
        if re.match(r"^Вы не можете", log[j].strip()) and k in MV: continue
        cmds.append((k, i))
print("команд", len(cmds), "первые:", [x[0] for x in cmds[:12]])
cur = "115092"; path = []; bad = []
for k, i in cmds:
    if k in MV:
        t = R.get(cur, {}).get(INV[k])
        if t is None: bad.append((i, cur, k)); continue
        path.append((cur, k, i)); cur = str(t)
    else: path.append((cur, "." + k, i))
print("промахов:", len(bad), bad[:8]); print("конец:", cur, NM.get(cur))
inz = [n for n, (v, m, i) in enumerate(path) if v in Z]
print("в зоне гоблинов шаги:", inz[0] if inz else None, inz[-1] if inz else None, "из", len(path), "| клеток зоны:", len(Z), "посещено:", len({v for v, _, _ in path} & Z))
json.dump(path, open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\gob_path.json", "w", encoding="utf-8"), ensure_ascii=False)
