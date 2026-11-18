"""Универсальная сим-сборка маршрута по логу: simgen.py <лог> <старт_vnum> <префикс_зоны> [<строка_от> <строка_до>]"""
import re, json, sqlite3, collections, sys
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
NM = {str(v): n for v, n in c.execute("select vnum,name from rooms")}
byname = collections.defaultdict(list)
for v, n in NM.items(): byname[n].append(v)
name, start, pref = sys.argv[1:4]
a = int(sys.argv[4]) if len(sys.argv) > 4 else 0
b = int(sys.argv[5]) if len(sys.argv) > 5 else 10**9
log = open(r"C:\Users\User\Desktop\Клод мад\JMC" + "\\" + name, "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
SH = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вв": "вверх", "вн": "вниз"}
MV = {"север", "юг", "восток", "запад", "вверх", "вниз"}
INV = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
OPP = {"N": "S", "S": "N", "E": "W", "W": "E", "U": "D", "D": "U"}
items = []
for i in range(a, min(b, len(log))):
    s = log[i].strip(); k = SH.get(s, s)
    isd = re.match(r"^(отпер|откр) \S+( \S+)?$", s)
    if not (k in MV or isd): continue
    j = i + 1
    while j < len(log) and not log[j].strip(): j += 1
    if k in MV and re.match(r"^Вы не можете|^Попробуйте сначала|^Вам нужно", log[j].strip()): continue
    nm = ex = None
    if k in MV:
        for q in range(i + 1, min(i + 40, len(log))):
            t = log[q].strip()
            if t.startswith("[ Exits"):
                ex = set(re.findall(r"\b[NSEWUD]\b", t)); z = q - 1
                while z > q - 6 and log[z].strip().startswith("*"): z -= 1
                nm = log[z].strip(); break
    items.append((k, nm, ex, i))
cur = start; out = []; amb = []
for n, (cmd, nm, ex, li) in enumerate(items):
    if cmd not in MV: out.append((cur, "." + cmd)); continue
    d = INV[cmd]; t = R.get(cur, {}).get(d)
    if t is not None and (nm is None or NM.get(str(t)) == nm or ex is None):
        out.append((cur, cmd)); cur = str(t); continue
    cands = [v for v in byname.get(nm, []) if v.startswith(pref) and (ex is None or set(R[v].keys()) == ex or True)]
    cands2 = [v for v in cands if R[v].get(OPP[d]) == cur]
    if cands2: cands = cands2
    out.append((cur, cmd))
    if len(cands) >= 1:
        if len(cands) > 1: amb.append((n, out[-1][0], cmd, nm, cands[:4]))
        R.setdefault(out[-1][0], {})[d] = int(cands[0]); cur = cands[0]
    else:
        amb.append((n, out[-1][0], cmd, nm, "НЕТ"))
print("команд", len(items), "неясных", len(amb), "конец", cur, NM.get(cur))
for x in amb[:15]: print(x)
seen = {v for v, _ in out}
Zs = [v for v in R if v.startswith(pref)]
print("клеток префикса", len(Zs), "посещено", len(seen & set(Zs)))
json.dump(out, open(S + r"\sim_" + name + ".json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump([(k, nm, sorted(ex) if ex else None, li) for k, nm, ex, li in items], open(S + r"\items_" + name + ".json", "w", encoding="utf-8"), ensure_ascii=False)
