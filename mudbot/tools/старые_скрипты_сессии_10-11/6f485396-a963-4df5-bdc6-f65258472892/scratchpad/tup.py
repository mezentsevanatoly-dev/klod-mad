import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
for n in ("Тупик", "Широкая дорога", "На дне оврага", "Зеленая улица"):
    for v, z, e in c.execute("select vnum,zone,exits from rooms where name=?", (n,)):
        ex = json.loads(e) if e.startswith("{") else {}
        if n != "Тупик" or "D" in ex:
            print(n, v, z, ex)
print(c.execute("select zone,count(*) from rooms where zone like '%гобл%' or zone like '%Яр%' or zone like '%Лечебн%' or zone like '%Конюш%' group by zone").fetchall())
print(c.execute("select zone,count(*) from mapper_rooms where name='Тупик' and l<0 group by zone").fetchall())
