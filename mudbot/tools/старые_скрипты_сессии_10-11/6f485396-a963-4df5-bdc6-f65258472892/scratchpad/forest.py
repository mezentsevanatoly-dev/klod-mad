import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
for n in ("Зеленый коридор", "Большие дубы", "Спуск в овраг", "Рощица", "Тропинка в лесу", "Изгиб дороги", "В воде", "Развилка"):
    print(n, c.execute("select vnum,zone,exits from rooms where name=?", (n,)).fetchall()[:4], c.execute("select zone,tag,x,y,l from mapper_rooms where name=? limit 4", (n,)).fetchall())
print(c.execute("select distinct zone from mapper_rooms where zone like '%лес%' or zone like '%равнин%' or zone like '%дуб%' or zone like '%Бес%' or zone like '%бес%'").fetchall())
