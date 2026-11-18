import re, json, sqlite3, collections
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\порт", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
NM = {str(v): n for v, n in c.execute("select vnum,name from rooms")}
byname = collections.defaultdict(list)
for v, n in NM.items(): byname[n].append(v)
SH = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вв": "вверх", "вн": "вниз", "север": "север", "юг": "юг", "восток": "восток", "запад": "запад", "вверх": "вверх", "вниз": "вниз"}
INV = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
OPP = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}
EX = {"С": "N", "Ю": "S", "В": "E", "З": "W", "Вв": "U", "Вн": "D"}
items = []  # (cmd, name, exits_set)
for i in range(1513, 6830):
    s = log[i].strip()
    k = SH.get(s); isd = re.match(r"^(отпер|откр) \S+( \S+)?$", s)
    if not (k or isd): continue
    j = i + 1
    while j < len(log) and not log[j].strip(): j += 1
    nxt = log[j].strip()
    if re.match(r"^(Вы не можете)", nxt) and not isd: continue
    if isd: items.append((s, None, None)); continue
    # ищем Exits и имя
    name = None; ex = None
    for q in range(i + 1, min(i + 40, len(log))):
        t = log[q].strip()
        if t.startswith("[ Exits"):
            ex = set(re.findall(r"\b[NSEWUD]\b", t)); break
        if t in byname and name is None: name = t
    items.append((k, name, ex))
print("элементов:", len(items))
cur = "100053"; out = []; amb = []; fixes = 0
for n, (cmd, name, ex) in enumerate(items):
    if cmd.startswith(("отпер", "откр")): out.append((cur, "." + cmd)); continue
    d = INV[cmd]; t = R.get(cur, {}).get(d)
    if t is not None and (name is None or NM.get(str(t)) == name):
        out.append((cur, cmd)); cur = str(t); continue
    cands = [v for v in byname.get(name, []) if (ex is None or set(R[v].keys()) == ex)]
    if len(cands) > 1:
        c2 = [v for v in cands if R[v].get(OPP[d]) == cur]
        if c2: cands = c2
    if len(cands) == 1:
        out.append((cur, cmd)); cur = cands[0]; fixes += 1
        R.setdefault(out[-1][0], {})[d] = int(cur)
        continue
    amb.append((n, cur, cmd, name, ex, cands)); out.append((cur, cmd))
    if cands: cur = cands[0]
print("исправлений:", fixes, "неясных:", len(amb)); [print(a) for a in amb[:10]]
print("конец:", cur)
json.dump(out, open(S + r"\port_v.json", "w", encoding="utf-8"), ensure_ascii=False)


for n in range(76,112): print(n+16, items[n][:2])

print('---')
for n in range(96,112): print(n+16, items[n], out[n][0])

print('===')
for n in range(90,112): print('item',n,'bot',n+17, out[n], items[n][1])

print('###')
LI=[]
for i in range(1513, 6830):
    s=log[i].strip()
    if SH.get(s): LI.append(i)
print(LI[88], LI[93])
