import sqlite3, json, collections, sys, subprocess, time
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
a, b = sys.argv[1:3]
q = collections.deque([a]); p = {a: None}
while q:
    v = q.popleft()
    if v == b: break
    for d, t in R.get(v, {}).items():
        t = str(t)
        if t not in p and t in R: p[t] = (v, d); q.append(t)
out = []; v = b
assert v in p, "нет пути"
while p.get(v): pv, d = p[v]; out.append(RU[d]); v = pv
out = out[::-1]
print(len(out), out)
J = [sys.executable, "-X", "utf8", r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc.py", "type", "--force"]
for m in out:
    subprocess.run([J[0], J[1], J[2], J[3], "type", m, "--force"], stdout=subprocess.DEVNULL); time.sleep(0.9)
