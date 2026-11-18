import re, json, sqlite3, collections
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
N = {str(v): n for v, n in c.execute("select vnum,name from rooms")}
Z = {str(v) for v, z in c.execute("select vnum,zone from rooms") if z == "Дом с привидениями"}
L = open(r"C:\Users\User\Desktop\Тадия\claude_game.log", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
b = max(i for i, l in enumerate(L) if "## BOT_START zone=привы1" in l)
S = []
for l in L[b:]:
    m = re.match(r"^\d\d:\d\d:\d\d ## STEP (\d+) vn=(\S*) cmd=(.*)$", l)
    if m: S.append((int(m.group(1)), m.group(2), m.group(3)))
seen = {v for _, v, _ in S}
print("комнат зоны в БД:", len(Z), "| посещено ботом:", len(seen & Z), "| не посещено:", [(v, N[v]) for v in sorted(Z - seen, key=int)][:25])
cur = "122004"
D = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
q = collections.deque([cur]); p = {cur: None}
while q:
    v = q.popleft()
    if v == "122011": break
    for d, t in R.get(v, {}).items():
        t = str(t)
        if t not in p and t in R: p[t] = (v, d); q.append(t)
if "122011" in p:
    out = []; v = "122011"
    while p[v]: pv, d = p[v]; out.append(D[d]); v = pv
    print("выход из", cur, "->115080:", out[::-1])
else:
    print("нет пути в БД из", cur)
print("последние шаги:", S[-6:])

