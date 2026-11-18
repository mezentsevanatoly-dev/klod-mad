import re, json, sqlite3, collections
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
NM = {str(v): n for v, n in c.execute("select vnum,name from rooms")}
Z = [str(v) for (v,) in c.execute("select vnum from rooms where zone like '%гоблин%' order by vnum")]
print([ (v, NM[v], R[v]) for v in Z if NM[v] in ("Поворот в яру", "Дорожка в яру", "На дне яра")])
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\гоблины", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
SH = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вв": "вверх", "вн": "вниз"}
MV = {"север", "юг", "восток", "запад", "вверх", "вниз"}
INV = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
OPP = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}
items = []
for i in range(0, 4650):
    s = log[i].strip(); k = SH.get(s, s)
    isd = re.match(r"^(отпер|откр) \S+( \S+)?$", s)
    if not (k in MV or isd): continue
    j = i + 1
    while j < len(log) and not log[j].strip(): j += 1
    if k in MV and re.match(r"^Вы не можете", log[j].strip()): continue
    name = ex = None
    if k in MV:
        for q in range(i + 1, min(i + 40, len(log))):
            t = log[q].strip()
            if t.startswith('[ Exits'):
                ex = set(re.findall(r'\b[NSEWUD]\b', t)); name = log[q-1].strip(); break
    items.append((k, name, ex, i))
print("команд", len(items))
