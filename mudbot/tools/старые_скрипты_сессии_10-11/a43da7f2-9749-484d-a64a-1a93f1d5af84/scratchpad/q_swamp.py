import sqlite3, re, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
print(c.execute("select zone,count(*),min(vnum),max(vnum) from rooms where zone like '%олот%' group by zone").fetchall())
print(c.execute("select count(*) from mapper_rooms where zone like '%олот%'").fetchall())
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\болото_часть", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
for i, l in enumerate(log):
    if re.match(r"^(область создать|обл с|обл соз)", l.strip()):
        print(i, l.strip())
        print([x.strip() for x in log[max(0, i - 20):i] if x.strip() and not re.match(r"^\d+H", x.strip()) and not x.startswith(("+", "|", ":"))][-8:])
        print([x.strip() for x in log[i:i + 30] if x.strip() and not x.startswith(("+", "|", ":"))][:14])
        break
kills = {}
for l in log:
    m = re.match(r"^(.+?) мертв[аоы]?\. R\.I\.P\.", l)
    if m: kills[m.group(1)] = kills.get(m.group(1), 0) + 1
print(kills)
