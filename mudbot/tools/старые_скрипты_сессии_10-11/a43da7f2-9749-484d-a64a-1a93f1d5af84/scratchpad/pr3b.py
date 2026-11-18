import sqlite3, json, collections, shutil, sys
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
def bfs(a, b):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R: p[t] = (v, d); q.append(t)
    out = []; v = b
    assert v in p
    while p.get(v): pv, d = p[v]; out.append((pv, RU[d])); v = pv
    return out[::-1]
zone, home, first = sys.argv[1:4]
p = r"C:\Users\User\Desktop\Тадия\areas\%s.botp" % zone
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
i = next(k for k, x in enumerate(L) if x.startswith("#if") or x.startswith(".триг обл") or "BotInZone = true" in x)
# i = первая строка не-плоского подхода; плоский подход = L[1:i]
if L[i].startswith("#if"): j = i
else: j = i
path = bfs(home, first)
shutil.copyfile(p, p + ".bak_pr3")
new = [L[0]] + [V.format(v=v, c=m) for v, m in path] + L[j:]
open(p, "wb").write(("\r\n".join(new) + "\r\n").encode("cp1251"))
print("подход", len(path), "строк", len(new), "первая строка зоны:", L[j][:40])
