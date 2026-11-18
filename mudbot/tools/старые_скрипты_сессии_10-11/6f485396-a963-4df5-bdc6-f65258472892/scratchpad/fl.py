import re, sqlite3
from collections import Counter
t = open(r"C:\Users\User\Desktop\Клод мад\JMC\бесы", "rb").read().decode("cp1251", errors="replace").replace("\r", "").split("\n")
i0 = next(i for i, l in enumerate(t) if l.strip().startswith("область создать"))
floor, kills = 1, {1: Counter(), 2: Counter(), 3: Counter()}
for l in t[i0:]:
    s = l.strip()
    if "Вы переместились в пространстве" in s:
        floor += 1
        print("переход на этаж", floor)
        if floor > 3:
            break
    m = re.match(r"^(.+?) мертв[аоы]?\. R\.I\.P\.", s)
    if m and floor <= 3:
        kills[floor][m.group(1)] += 1
db = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
mine = {n.lower() for n, in db.execute("select distinct name from mob_kills where my_level>=25")}
for f in (1, 2, 3):
    tot = sum(kills[f].values())
    print(f"этаж {f}: убито {tot}, видов {len(kills[f])}")
    print("   ", "; ".join(f"{n} x{c}{'' if n.lower() in mine else ' (я не убивала)'}" for n, c in kills[f].most_common()))
