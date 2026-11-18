"""conv.py <бот_имя> <recon_V_botp> <home_vnum> [--csv файл] [--drop имя1,имя2] [--pre cmd1,cmd2] [--post cmd1,cmd2]
Собирает areas/<бот_имя>.botp = [BotInZone=false] + (pre | BFS home->первая клетка) + V-строки + (post | BFS последняя->home) + [BotInZone=false]"""
import sys, re, json, sqlite3, collections, shutil
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}
INV = {v: k for k, v in RU.items()}
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
def bfs(a, b):
    if a == b: return []
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R: p[t] = (v, d); q.append(t)
    out = []; v = b
    assert v in p, ("нет пути", a, b)
    while p.get(v): pv, d = p[v]; out.append((pv, RU[d])); v = pv
    return out[::-1]
name, src, home = sys.argv[1:4]
opt = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
L = open(src, "rb").read().decode("cp1251").split("\r\n")
L = [x for x in L if x.strip()]
def parse(x):
    m = re.search(r"== (\d+)\} \{([^}]*)\}$", x); return (m.group(1), m.group(2)) if m else (None, None)
first = next(parse(x)[0] for x in L if parse(x)[0])
last = [parse(x) for x in L if parse(x)[0]][-1]
lastnext = R[last[0]].get(INV[last[1]]) if last[1] in INV else None
lastnext = str(lastnext) if lastnext else last[0]
pre = opt("--pre"); post = opt("--post")
pre_l = [x for x in pre.split(",")] if pre else [V.format(v=v, c=m) for v, m in bfs(home, first)]
post_l = [x for x in post.split(",")] if post else [V.format(v=v, c=m) for v, m in bfs(lastnext, home)]
lines = [".триг #scr botCore.BotInZone = false"] + pre_l + L + post_l + [".триг #scr botCore.BotInZone = false"]
out = r"C:\Users\User\Desktop\Тадия\areas\%s.botp" % name
open(out, "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print(name, "строк", len(lines), "| первая клетка", first, "| после последней", lastnext, "| префикс", len(pre_l), "суффикс", len(post_l))
csv = opt("--csv")
if csv:
    drop = (opt("--drop") or "").split(",")
    rows = open(csv, "rb").read().decode("cp1251").split("\r\n")
    keep = [r for r in rows if r.strip() and not any(r.startswith('"%s"' % d) for d in drop if d)]
    open(r"C:\Users\User\Desktop\Тадия\areas\%s_mob.csv" % name, "wb").write(("\r\n".join(keep) + "\r\n").encode("cp1251"))
    print("csv строк", len(keep) - 1, "убрано", len(rows) - 1 - (len(keep) - 1) - sum(1 for r in rows if not r.strip()))
