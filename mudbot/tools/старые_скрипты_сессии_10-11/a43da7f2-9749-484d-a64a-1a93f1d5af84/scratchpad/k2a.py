import re, json, sqlite3, collections
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {str(v): json.loads(e or "{}") for v, e in c.execute("select vnum,exits from rooms")}
NM = {str(v): n for v, n in c.execute("select vnum,name from rooms")}
Z = {str(v): z for v, z in c.execute("select vnum,zone from rooms")}
print(c.execute("select zone,count(*),min(vnum),max(vnum) from rooms where zone like '%атакомб%' group by zone").fetchall())
for v, n in NM.items():
    if n == "Спуск вниз": print(v, Z[v], R[v])
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\геокаты2", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
for i in range(0, 120):
    if log[i].startswith("[ Exits"): print(i, log[i-1].strip(), log[i].strip())
rec = open(r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\геокаты2\геокаты2.md", encoding="utf-8").read()
print(rec[:900])
