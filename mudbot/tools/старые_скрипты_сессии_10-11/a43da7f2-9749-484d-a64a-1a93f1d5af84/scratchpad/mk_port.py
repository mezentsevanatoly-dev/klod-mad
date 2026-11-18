import re, json, sqlite3, collections, sys
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\порт", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
SH = {"с": "N", "ю": "S", "в": "E", "з": "W", "вв": "U", "вн": "D", "север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
cur = "100053"
path = []  # (vnum, cmd) для порта
other = []
started = False
for i, l in enumerate(log):
    if i < 1500: continue
    s = l.strip()
    d = SH.get(s)
    if d:
        nxt = R.get(cur, {}).get(d)
        if nxt is None:
            other.append((i, cur, s)); continue
        path.append((cur, RU[d], i)); cur = str(nxt)
    elif re.match(r"^(отпер|откр)", s):
        path.append((cur, "." + s, i))
print("ходов:", len(path), "невозможных:", len(other), other[:8])
print("конец клетка:", cur)
zone = {v for v in R if v.startswith("128")}
seen = {v for v, _, _ in path}
print("зона:", len(zone), "посещено:", len(seen & zone))
json.dump(path, open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\port_path.json", "w", encoding="utf-8"), ensure_ascii=False)
print(path[:6], path[-6:])
