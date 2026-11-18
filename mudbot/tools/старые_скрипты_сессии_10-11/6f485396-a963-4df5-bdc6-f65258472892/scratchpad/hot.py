import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
for n in ("В прихожей", "Перед гостиницей", "Опасный перекресток", "Перед аркой", "Западный путь"):
    print(n, [(v, z, e) for v, z, e in c.execute("select vnum,zone,exits from rooms where name=?", (n,)) if "Геолант" in z or "Элендор" in z])
