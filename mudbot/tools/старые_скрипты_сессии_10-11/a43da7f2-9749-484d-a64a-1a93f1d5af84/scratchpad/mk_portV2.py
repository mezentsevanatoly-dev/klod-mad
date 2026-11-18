import json, sqlite3, collections
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
NM = {str(v): n for v, n in c.execute("select vnum,name from rooms")}
INV = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
cand = json.load(open(S + r"\steps.json", encoding="utf-8"))
plain = open(S + r"\port_cmds.txt", encoding="utf-8").read().split("\n")
chain = []  # (k, vn or None)
for k, cmd in enumerate(plain):
    st = str(17 + k); vn = None
    for key in cand.get(st, {}):
        v, cm = key.split("|", 1)
        c2 = cm.split(";")[0] if cm.split(";")[0] in INV else cm
        if cm == cmd or cm.startswith(cmd): vn = v
    chain.append(vn)
bad = []
for k in range(len(plain) - 1):
    a, b2 = chain[k], chain[k + 1]
    if plain[k] in INV and a and b2:
        t = R.get(a, {}).get(INV[plain[k]])
        if str(t) != b2: bad.append((k, a, plain[k], b2, str(t)))
print("известно:", sum(1 for x in chain if x), "из", len(chain))
print("разрывы:", len(bad)); [print(x) for x in bad[:20]]
print("первый неизвестный:", next((k for k, x in enumerate(chain) if x is None), None))
json.dump(chain, open(S + r"\chain.json", "w"))
