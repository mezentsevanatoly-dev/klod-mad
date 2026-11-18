import sqlite3, json, collections, re, os
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
N = {str(v): (z, n) for v, z, n in c.execute("select vnum,zone,name from rooms")}
banks = [(v, N[v]) for v in N if N[v][1] in ("Банк",) and N[v][0] in ("Город Геолант", "Город Элендор", "Город Стэдвик", "Город Огис")]
print("банки:", banks)
def bfs(a, b):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R: p[t] = (v, d); q.append(t)
    if b not in p: return None
    out = []; v = b
    while p[v]: pv, d = p[v]; out.append(d.lower()); v = pv
    return "".join(out[::-1])
def comp(s): return re.sub(r"(.)\1+", lambda m: str(len(m.group(0))) + m.group(1), s)
for v, _ in banks:
    if v.startswith("115"):
        print("склад р2 ->", v, comp(bfs("115092", v) or ""), "| конюшня 115061 ->", comp(bfs("115061", v) or ""))
# лог гильдии Стэдвика у пользователя
JMC = r"C:\Users\User\Desktop\Клод мад\JMC"
for f in os.listdir(JMC):
    p = os.path.join(JMC, f)
    if os.path.isfile(p) and os.path.getsize(p) > 50000:
        t = open(p, "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
        for i, l in enumerate(t):
            if l.strip() == "Дом яростного бойца":
                seg = [x.strip() for x in t[i:i + 60] if x.strip() and not re.match(r"^\d+H", x.strip())]
                print("==", f, i)
                print("\n".join(seg[:30])); break
        else:
            continue
        break
