import re, sys, sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
NM = {}
name = sys.argv[1]
log = open(r"C:\Users\User\Desktop\Клод мад\JMC" + "\\" + name, "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
print(name, "строк", len(log))
SH = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вв": "вверх", "вн": "вниз"}
MV = {"север", "юг", "восток", "запад", "вверх", "вниз"}
n = 0
zones = []
for i, l in enumerate(log):
    s = l.strip()
    if re.match(r"^(область|обл |путь|ехать|огис|гео|стэ|элен|фело|рекол|зач)", s): print(i, s[:70])
    if s.startswith("[Зона") and (not zones or zones[-1][1] != s): zones.append((i, s[:70]))
print("зоны:", zones[:12])
mv = []
for i, l in enumerate(log):
    k = SH.get(l.strip(), l.strip())
    if k in MV: mv.append((i, k))
print("ходов:", len(mv), "первые:", " ".join(k[:2] for i, k in mv[:50]))
# первая комната
for i, l in enumerate(log[:200]):
    if l.startswith("[ Exits"): print("1-я комната:", log[i - 1].strip(), "|", l.strip()); break
