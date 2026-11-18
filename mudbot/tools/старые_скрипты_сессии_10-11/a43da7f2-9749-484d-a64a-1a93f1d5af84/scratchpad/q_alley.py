import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
rows = c.execute("select vnum,zone,name,exits from rooms where vnum between '146000' and '146099' order by vnum").fetchall()
print(len(rows), "комнат в БД 146xxx")
for r in rows:
    print(r[0], r[1], "|", r[2], "|", r[3])
print("mapper_rooms:", [x[1] for x in c.execute("pragma table_info(mapper_rooms)")])
print(c.execute("select count(*) from mapper_rooms where zone like '%Аллея%'").fetchall())
