import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
for r in c.execute("select vnum,zone,name,exits from rooms where vnum between '135000' and '135013' or vnum between '122000' and '122012' order by vnum"):
    print(r)
