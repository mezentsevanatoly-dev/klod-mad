import json, collections, sqlite3, shutil
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
    assert v == a, (a, b)
    return out[::-1]
cmds = open(S + r"\port_cmds.txt", encoding="utf-8").read().split("\n")
appr = bfs("100076", "100053"); back = bfs("100053", "100076")
print("подход", len(appr), "зона", len(cmds), "назад", len(back))
lines = [".триг #scr botCore.BotInZone = false"] + appr + [".триг #scr botCore.BotInZone = true"] + [(".триг " + x) if x.startswith(("отпер", "откр")) else x for x in cmds] + [".триг #scr botCore.BotInZone = false"] + back
open(r"C:\Users\User\Desktop\Тадия\areas\порт.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
shutil.copyfile(S + r"\port_mob.csv", r"C:\Users\User\Desktop\Тадия\areas\порт_mob.csv")
print("строк", len(lines))
