import re, sqlite3, sys, json
zone = sys.argv[1]
src = open(r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js", "rb").read().decode("cp1251")
body = src[src.index("var InspectionWords = [") : src.index("];", src.index("var InspectionWords = ["))]
pats = []
for m in re.finditer(r"(?<![\w)])/((?:\\.|[^/\\\n])+)/", body):
    try:
        pats.append(re.compile(m.group(1)))
    except re.error:
        pass
print("шаблонов:", len(pats))
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
names = sorted({r[0] for r in c.execute("select name from rooms where zone=?", (zone,))})
print("комнат (имён):", len(names))
bad = [n for n in names if not any(p.search(n) for p in pats)]
print("не в словаре:", bad)
