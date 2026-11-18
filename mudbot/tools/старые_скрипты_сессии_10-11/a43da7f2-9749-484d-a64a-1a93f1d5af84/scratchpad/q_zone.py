import re, sqlite3, collections, sys
name = sys.argv[1]
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\%s" % name, "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
kills = collections.Counter()
for l in log:
    m = re.match(r"^(.+?) мертв[аоы]?\. R\.I\.P\.", l)
    if m: kills[m.group(1)] += 1
print("лог строк:", len(log), "| убийств видов:", len(kills))
for n, k in kills.most_common():
    r = c.execute("select zone,level,prof,kind from mob_cards where name=? order by (zone like ?) desc limit 1", (n, "%" + (sys.argv[2] if len(sys.argv) > 2 else "") + "%")).fetchone()
    print("  ", n, k, r)
for i, l in enumerate(log):
    if re.match(r"^(область создать|обл с|обл соз)", l.strip()):
        print("create line", i, l.strip())
        print("комната создания (выше):", [x.strip() for x in log[max(0, i - 14):i] if x.strip() and not re.match(r"^\d+H", x.strip()) and not x.startswith(("+", "|", ":"))][-6:])
        break
