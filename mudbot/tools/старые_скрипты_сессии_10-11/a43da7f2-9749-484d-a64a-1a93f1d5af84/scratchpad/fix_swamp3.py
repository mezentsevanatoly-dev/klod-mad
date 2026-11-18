import sqlite3, json, collections
p = r"C:\Users\User\Desktop\Тадия\areas\болото.botp"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
fl = max(i for i, l in enumerate(L) if l.startswith(".триг #scr botCore.BotInZone = false"))
back = L[fl + 1:]
assert len(back) == 32, len(back)
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {r[0]: json.loads(r[1] or "{}") for r in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
q = collections.deque(["100009"]); pr = {"100009": None}
while q:
    v = q.popleft()
    if v == "100076": break
    for d, t in R.get(v, {}).items():
        t = str(t)
        if t not in pr and t in R: pr[t] = (v, d); q.append(t)
city = []; v = "100076"
while pr[v]: v, d = pr[v][0], pr[v][1]; city.append(RU[d])
city = city[::-1]
new = L[:fl + 1] + back[:24] + city
open(p, "wb").write(("\r\n".join(new) + "\r\n").encode("cp1251"))
print("зеркало 24 хода + город", city, "| всего строк", len(new))
