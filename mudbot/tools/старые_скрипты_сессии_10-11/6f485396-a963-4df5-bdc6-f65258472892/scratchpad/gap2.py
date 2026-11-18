import re, sqlite3
from collections import Counter
db = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
rows = db.execute("select ts,name from mob_kills order by rowid desc limit 80").fetchall()
print(rows[0], rows[-1])
# лог пользователя по этажам
t = open(r"C:\Users\User\Desktop\Клод мад\JMC\бесы", "rb").read().decode("cp1251", errors="replace").replace("\r", "").split("\n")
i0 = next(i for i, l in enumerate(t) if l.strip().startswith("область создать"))
floor, want = 1, {1: Counter(), 2: Counter(), 3: Counter()}
for l in t[i0:]:
    s = l.strip()
    if "Вы переместились в пространстве" in s:
        floor += 1
        if floor > 3:
            break
    m = re.match(r"^(.+?) мертв[аоы]?\. R\.I\.P\.", s)
    if m and floor <= 3:
        want[floor][m.group(1)] += 1
# мои убийства этого прогона: последние 11+11+23 = 45 записей
mine = Counter(n for _, n in rows[:45])
allw = Counter()
for f in want:
    allw += want[f]
print("убито мной (последние 45):", dict(mine))
print("по логу (всего):", dict(allw))
print("не хватает:", {n: c - mine.get(n, 0) for n, c in allw.items() if c > mine.get(n, 0)})
