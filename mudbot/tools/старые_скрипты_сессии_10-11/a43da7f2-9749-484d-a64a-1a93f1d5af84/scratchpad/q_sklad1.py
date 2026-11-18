import re, sqlite3, collections
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\склад1", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
kills = collections.Counter()
for l in log:
    m = re.match(r"^(.+?) мертв[аоы]?\. R\.I\.P\.", l)
    if m: kills[m.group(1)] += 1
print("убийства в логе:", len(kills))
for n, k in kills.most_common():
    r = c.execute("select zone,level,prof,kind from mob_cards where name=? order by (zone like '%клад%') desc limit 1", (n,)).fetchone()
    print("  ", n, k, r)
for i, l in enumerate(log):
    if re.match(r"^(область создать|обл с|обл соз)", l.strip()):
        print("create line", i, l.strip()); break
