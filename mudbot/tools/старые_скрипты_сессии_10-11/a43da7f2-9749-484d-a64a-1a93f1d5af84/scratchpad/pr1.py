import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
NM = {str(v): n for v, n in c.execute("select vnum,name from rooms")}
INV = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
for v in ("100076", "100077", "100075", "100070"): print(v, NM.get(v), R.get(v))
L = open(r"C:\Users\User\Desktop\Тадия\areas\притон.botp", "rb").read().decode("cp1251").split("\r\n")
mv = []
for x in L[1:]:
    if x in INV: mv.append(x)
    else: break
print("плоский подход:", mv)
for st in R:
    if not st.startswith("100"): continue
    cur = st; ok = True
    for m in mv:
        t = R[cur].get(INV[m])
        if t is None: ok = False; break
        cur = str(t)
    if ok: print("старт", st, NM[st], "-> конец", cur, NM.get(cur))
