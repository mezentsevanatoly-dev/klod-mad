import sqlite3, json, collections
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
for r in c.execute("select vnum,zone,name,exits from rooms where (name like '%ильдия%' or name like '%арвар%') and vnum between 115000 and 115200"): print(r)
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
print(R["115092"], R["115089"])
