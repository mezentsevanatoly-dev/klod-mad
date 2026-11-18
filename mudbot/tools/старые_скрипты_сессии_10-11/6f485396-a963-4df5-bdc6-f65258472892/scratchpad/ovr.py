import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
for v, z, n, e in c.execute("select vnum,zone,name,exits from rooms where name like '%овраг%' or name like '%Овраг%'"):
    print(v, z, n, e)
print(c.execute("select zone,tag,name,exits from mapper_rooms where name like '%овраг%' limit 8").fetchall())
print(c.execute("select vnum,zone,name from rooms where vnum=149001").fetchall())
print(c.execute("select name,path,end_vnum from speedwalks where name like '%Лиса%'").fetchall())
