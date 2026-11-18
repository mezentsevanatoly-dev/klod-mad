import sqlite3, json, collections
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
NM = {str(v): n for v, n in c.execute("select vnum,name from rooms")}
Z = sorted(v for v in R if v.startswith("117"))
print("клеток 117:", len(Z))
# достижимо от входа 117094 без прохода из 117008 на юг (D/S)
start = "117094"
seen = {start}; q = collections.deque([start])
while q:
    v = q.popleft()
    for d, t in R.get(v, {}).items():
        t = str(t)
        if not t.startswith("117"): continue
        if v == "117008" and d == "S": continue
        if t not in seen: seen.add(t); q.append(t)
print("доступно без отшельника:", len(seen))
rest = [v for v in Z if v not in seen]
print("за отшельником/недоступно:", len(rest))
for v in Z:
    mark = " " if v in seen else "X"
    print(mark, v, NM[v], R[v])
