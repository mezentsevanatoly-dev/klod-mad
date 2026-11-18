import json, re, sqlite3, collections
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
INV = {v: k for k, v in RU.items()}
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
def bfs(a, b, pref=None):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R and (pref is None or t.startswith(pref) or t == b): p[t] = (v, d); q.append(t)
    out = []; v = b
    assert v in p, (a, b)
    while p.get(v): pv, d = p[v]; out.append((pv, RU[d])); v = pv
    return out[::-1]
sim = json.load(open(S + r"\sim_геокаты2.json", encoding="utf-8"))
# обрезаем по первому 'вверх' после двери 99/100 (индекс 101 в items)
items = json.load(open(S + r"\items_геокаты2.json", encoding="utf-8"))
cut = 101  # items[101] = вверх -> этаж 1
path = sim[: cut + 1]
last_c, last_m = path[-1]
nxt = str(R[last_c][INV[last_m]]) if last_m in INV else last_c
print("после 'вверх':", nxt)
back = bfs(nxt, "226001", "226")
appr = bfs("115092", "115042")
zone = [V.format(v=v, c=m) if not m.startswith(".") else ".триг " + V.format(v=v, c=m[1:]) for v, m in path]
lines = [".триг #scr botCore.BotInZone = false"] + [V.format(v=v, c=m) for v, m in appr] + [".триг обл с вн"] + zone
lines += [V.format(v=v, c=m) for v, m in back] + [V.format(v="226001", c="вверх")]
home = bfs("115042", "115092")
lines += [".триг #scr botCore.BotInZone = false"] + [V.format(v=v, c=m) for v, m in home]
open(r"C:\Users\User\Desktop\Тадия\areas\каты2.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("строк", len(lines), "подход", len(appr), "зона", len(zone), "назад на 226001:", len(back), "домой", len(home), "| индекс обл", 1 + len(appr))
# csv
rec = {}
for r in open(r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\геокаты2\геокаты2_mob.csv", "rb").read().decode("cp1251").split("\r\n")[1:]:
    p = r.split(";")
    if len(p) > 3: rec.setdefault(p[0].strip('"'), p)
want = {"Слепень": "Огромный слепень летает в поисках выхода на поверхность. ", "Скорпион": "Гигантский скорпион ищет местечко посуше. ", "Овод": "Гигантский овод кружит над вами. ",
        "Толстая личинка": None, "Пурпурная слизь": None, "Охристая слизь": None, "Навозный жук": None, "Киноварная слизь": None, "Изумрудная слизь": None, "Карминовая слизь": None,
        "Сколопендра": "Длинная сколопендра забавно перебирает лапками. ", "Маленькая змейка": "Маленькая вёрткая змейка ползает в грязи. "}
mob = open(S + r"\k2_mob.csv", "rb").read().decode("cp1251").split("\r\n")
head = mob[0]; by = {r.split(";")[0].strip('"'): r for r in mob[1:] if r.strip()}
out = [head]
for nm, d in want.items():
    b = list(rec.get(nm) or by.get(nm, "").split(";") or [])
    if not b or b == [""]: b = ['"%s"' % nm] + ['""'] * 14
    b[0] = '"%s"' % nm
    if d: b[1] = '"%s"' % d
    elif nm in by: b[1] = by[nm].split(";")[1]
    out.append(";".join(b))
open(r"C:\Users\User\Desktop\Тадия\areas\каты2_mob.csv", "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
print("csv", len(out) - 1)
