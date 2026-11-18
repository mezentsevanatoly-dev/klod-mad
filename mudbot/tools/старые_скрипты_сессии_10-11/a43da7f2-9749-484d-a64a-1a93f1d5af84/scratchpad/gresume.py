import sys, json, sqlite3, collections, subprocess, time
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
def bfs(a, b):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R: p[t] = (v, d); q.append(t)
    cells = [b]; v = b
    while p.get(v): v = p[v][0]; cells.append(v)
    return cells[::-1]
cell = sys.argv[1]
cells = bfs("115092", "122047")
step = 1 + cells.index(cell)
print("шаг", step)
J = ["python", "-X", "utf8", r"C:\Users\User\Desktop\Клод мад\mudbot\tools\jmc.py", "do", "--force"]
for x in ["#scr botCore.enableBot=false", "#scr botCore.loadZone('гоблины')", "#scr seekstep=%d" % step, "#scr botCore.BotInZone=false", "#scr botCore.enableBot=true", "look краткий"]:
    subprocess.run(J + [x], stdout=subprocess.DEVNULL); time.sleep(2)
