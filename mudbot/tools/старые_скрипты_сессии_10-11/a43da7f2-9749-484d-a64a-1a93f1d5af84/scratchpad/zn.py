import sqlite3
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
for r in c.execute("select zone,count(*),min(vnum),max(vnum) from rooms where zone like '%Ел%' or zone like '%очев%' or zone like '%рыбак%' or zone like '%онюш%' or zone like '%Огис%' or zone like '%Болото%' group by zone"): print(r)
import re
s = open(r"C:\Users\User\Desktop\Тадия\scripts\AreaGuard.js", "rb").read().decode("cp1251", "replace")
i = s.index("var AREA_NAMES"); print(s[i:i+700])
