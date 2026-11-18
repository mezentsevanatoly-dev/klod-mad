import json, collections, sqlite3
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
def bfs(a, b):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R: p[t] = (v, d); q.append(t)
    out = []; v = b
    while p.get(v): pv, d = p[v]; out.append(RU[d]); v = pv
    return out[::-1]
items = json.load(open(S + r"\items_геокаты2.json", encoding="utf-8"))
cmds = [it[0] for it in items[:102]]
lines = [".триг #scr botCore.BotInZone = false"] + bfs("115092", "115042") + [".триг обл с вн", ".триг #scr botCore.BotInZone = false"] + [(".триг " + x) if x.startswith(("отпер", "откр")) else x for x in cmds]
open(r"C:\Users\User\Desktop\Тадия\areas\каты2p.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("строк", len(lines), "старт зоны (индекс первого хода)", 1 + 10 + 2)
