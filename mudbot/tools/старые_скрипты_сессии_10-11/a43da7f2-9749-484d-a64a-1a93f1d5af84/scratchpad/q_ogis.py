import sqlite3, json, collections, re
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
N = {str(v): (z, n) for v, z, n in c.execute("select vnum,zone,name from rooms")}
for v in ("115061", "115092", "180154", "180085", "180048", "180025", "12172", "12163", "115039"):
    print(v, N.get(v), R.get(v))
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
def comp(s):
    return re.sub(r"(.)\1+", lambda m: str(len(m.group(0))) + m.group(1), s)
for a, b in (("115092", "115061"), ("115061", "115092"), ("180154", "180048"), ("180085", "180048"), ("180048", "180154"), ("12172", "12163"), ("12163", "12172")):
    r = bfs(a, b)
    print(a, "->", b, comp(r) if r else None)
# заданный спидволк огис_лечеб_вход: пройти от 180154 / 180085
def walk(start, sw):
    cur = start
    for n, d in re.findall(r"(\d*)([nsewud])", sw):
        for _ in range(int(n) if n else 1):
            nxt = R.get(cur, {}).get(d.upper())
            if nxt is None: return ("обрыв", cur, d)
            cur = str(nxt)
    return ("конец", cur, N.get(cur))
for s in ("180154", "180085", "180025"):
    print("огис_лечеб_вход от", s, ":", walk(s, "wd2n3e5s6wswn4e3nwuw2n"))
