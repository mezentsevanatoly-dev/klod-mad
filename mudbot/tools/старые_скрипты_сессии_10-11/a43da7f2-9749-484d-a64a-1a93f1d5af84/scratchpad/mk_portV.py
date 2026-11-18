import re, json, sqlite3, collections
S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
INV = {"север": "N", "юг": "S", "восток": "E", "запад": "W", "вверх": "U", "вниз": "D"}
L = open(r"C:\Users\User\Desktop\Тадия\claude_game.log", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
b = max(i for i, l in enumerate(L) if "BOT_START zone=порт" in l and "20:" in l[:3] or "19:51:50 ## BOT_START zone=порт" in l)
b = next(i for i, l in enumerate(L) if "## BOT_START zone=порт" in l)
cand = collections.defaultdict(collections.Counter)
for l in L[b:]:
    m = re.match(r"^\d\d:\d\d:\d\d ## STEP (\d+) vn=(\d+) cmd=(.*)$", l)
    if m: cand[int(m.group(1))][(m.group(2), m.group(3))] += 1
plain = open(S + r"\port_cmds.txt", encoding="utf-8").read().split("\n")
# plain индекс k -> шаг 16+k (шаг 0 = маркер BotInZone=false, 1..15 подход, 16 = маркер true -> k=0 это 17)
off = None
for st in sorted(cand):
    for (vn, cmd), n in cand[st].items():
        pass
# найдём смещение по первой команде зоны
first = {st: cand[st] for st in sorted(cand) if 15 <= st <= 20}
print({st: dict(v) for st, v in first.items()})
json.dump({str(k): {f"{v}|{c2}": n for (v, c2), n in d.items()} for k, d in cand.items()}, open(S + r"\steps.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(cand), min(cand), max(cand))
