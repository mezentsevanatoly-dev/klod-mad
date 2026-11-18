import json, sqlite3, collections, shutil
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
    assert v == a; return out[::-1]
items = json.load(open(S + r"\gob_items.json", encoding="utf-8")) if False else None
exec(open(S + r"\gob2.py", encoding="utf-8").read().split('print("команд"')[0])
cmds = [it[0] for it in items[32:124]]; appr = bfs("115092", "122047")
back = bfs("122047", "115092")
lines = [".триг #scr botCore.BotInZone = false"] + appr + [".триг #scr botCore.BotInZone = true"] + [(".триг " + x) if x.startswith(("отпер", "откр")) else x for x in cmds] + [".триг #scr botCore.BotInZone = false"] + back
open(r"C:\Users\User\Desktop\Тадия\areas\гоблины.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("строк", len(lines), "подход", len(appr), "назад", len(back))
# csv
rec = {}
for r in open(r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\гоблины\рр_гоблиныV_mob.csv", "rb").read().decode("cp1251").split("\r\n")[1:]:
    p = r.split(";")
    if len(p) > 3: rec.setdefault(p[0].strip('"'), p)
rows = open(S + r"\gob_mob.csv", "rb").read().decode("cp1251").split("\r\n")
out = [rows[0]] + [r for r in rows[1:] if r.strip()]
extra = {"Шаман": "Боевой гоблинский шаман стоит здесь. ", "Тролль-вышибала": "Здоровенный тролль-вышибала стоит тут. ", "Маленький гоблин": "Маленький и весь покрытый бородавками гоблин стоит тут. ", "Посетитель": "Посетитель таверны методично напивается тут. ", "Разбойник": "Разбойник, вышедший на промысел стоит тут. "}
for nm, d in extra.items():
    b = list(rec.get(nm) or ['"%s"' % nm] + ['""'] * 14); b[0] = '"%s"' % nm; b[1] = '"%s"' % d; out.append(";".join(b))
open(r"C:\Users\User\Desktop\Тадия\areas\гоблины_mob.csv", "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
print("csv", len(out) - 1, [o.split(";")[0] for o in out[1:]])
