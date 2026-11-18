"""Спидволк склад р1 (Элендор, 100076) <-> склад р2 (Геолант, 115092): запись в speedwalks.txt и таблицу speedwalks game.db.
Составной: склад -> площадь Элендора 100009 (граф) + дорога 22es7e3s22e (проверена ботом) -> площадь Геоланта 115039 + граф до склада 115092.
python -X utf8 tools/mk_sw_r1_r2.py
"""
import collections, json, os, re, sqlite3

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
c = sqlite3.connect(os.path.join(ROOT, "data", "game.db"))
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
N = {str(v): n for v, n in c.execute("select vnum,name from rooms")}
D = {"N": "n", "S": "s", "E": "e", "W": "w", "U": "u", "D": "d"}

def bfs(a, b):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R: p[t] = (v, d); q.append(t)
    if b not in p: raise SystemExit("нет пути %s -> %s в БД" % (a, b))
    out = []; v = b
    while p[v]: pv, d = p[v]; out.append(D[d]); v = pv
    return out[::-1]

def comp(ms):
    out, i = "", 0
    while i < len(ms):
        j = i
        while j < len(ms) and ms[j] == ms[i]: j += 1
        out += (str(j - i) if j - i > 1 else "") + ms[i]; i = j
    return out

def expand(s):
    return [d for n, d in re.findall(r"(\d*)([nsewud])", s) for _ in range(int(n) if n else 1)]

STOR1, HUB1, HUB2, STOR2 = "100076", "100009", "115039", "115092"
print("склад р2:", N.get(STOR2), "| площадь р2:", N.get(HUB2))
fwd = bfs(STOR1, HUB1) + expand("22es7e3s22e") + bfs(HUB2, STOR2)
rev_g = bfs(STOR2, HUB2) + expand("22w3n7wn22w") + bfs(HUB1, STOR1)
a, b = comp(fwd), comp(rev_g)
print("р1->р2:", a, "(%d ходов)" % len(fwd)); print("р2->р1:", b, "(%d ходов)" % len(rev_g))
sw = os.path.join(ROOT, "speedwalks.txt")
old = open(sw, encoding="utf-8").read().splitlines() if os.path.exists(sw) else []
keep = [l for l in old if not l.startswith(("р1_склад-р2_склад", "р2_склад-р1_склад"))]
keep += ["# от склада р1 (Элендор 100076) до склада р2 (Геолант 115092), 10.11.2026", "р1_склад-р2_склад = %s @ %s" % (a, STOR2),
         "# обратно", "р2_склад-р1_склад = %s @ %s" % (b, STOR1)]
open(sw, "w", encoding="utf-8").write("\n".join(keep) + "\n")
cols = [r[1] for r in c.execute("pragma table_info(speedwalks)")]
print("колонки speedwalks:", cols)
for name, path, end in (("р1_склад-р2_склад", a, STOR2), ("р2_склад-р1_склад", b, STOR1)):
    c.execute("delete from speedwalks where name=?", (name,))
    vals = {"name": name, "path": path, "end_vnum": end, "to_vnum": end, "note": "склад р1<->р2"}
    ks = [k for k in vals if k in cols]
    c.execute("insert into speedwalks(%s) values (%s)" % (",".join(ks), ",".join("?" * len(ks))), [vals[k] for k in ks])
c.commit()
json.dump({"fwd": fwd, "rev": rev_g}, open(os.path.join(ROOT, "data", "recon", "sw_r1_r2.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("записано в speedwalks.txt и БД")
