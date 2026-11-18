import sqlite3, re
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
print(c.execute("select zone,count(*),min(vnum),max(vnum) from rooms where zone like '%анализ%' group by zone").fetchall())
print(c.execute("select vnum,zone,name,exits from rooms where vnum='100121'").fetchall())
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\канал", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
for i, l in enumerate(log):
    if re.match(r"^(область создать|обл с|обл соз)", l.strip()):
        print(i, l.strip());
        print([x.strip() for x in log[max(0, i - 25):i] if x.strip() and not re.match(r"^\d+H", x.strip())][-14:])
        break
