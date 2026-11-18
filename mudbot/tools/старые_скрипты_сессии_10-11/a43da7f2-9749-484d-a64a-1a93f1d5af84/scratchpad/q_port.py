import re, sqlite3, json
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\порт", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
for v in ("100053",):
    print(c.execute("select vnum,zone,name,exits from rooms where vnum=?", (v,)).fetchone())
print(c.execute("select zone,count(*),min(vnum),max(vnum) from rooms where zone like '%Порт%' group by zone").fetchall())
n = 0
for i, l in enumerate(log):
    if re.match(r"^\[Зона, на .*Порт", l.strip()):
        print(i, l.strip(), "| выше:", [x.strip() for x in log[max(0, i - 6):i] if x.strip() and not re.match(r"^\d+H", x.strip())][-3:])
        n += 1
        if n >= 3: break
print("команды-ходы до первой зоны порта:", [l.strip() for l in log[:400] if l.strip() in ("север", "юг", "восток", "запад", "вверх", "вниз")][:40])
