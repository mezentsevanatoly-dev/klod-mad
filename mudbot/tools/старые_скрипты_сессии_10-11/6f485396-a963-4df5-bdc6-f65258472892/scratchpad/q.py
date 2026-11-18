import sqlite3
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
for t in ("rooms", "mapper_rooms"):
    try:
        print(t, c.execute(f"select vnum,area,name from {t} where area like '%Огис%' and (name like '%Склад%' or name like '%Банк%' or name like '%Аватар%' or name like '%Веранда%' or name like '%портал%' or name like '%Храм%')").fetchall())
    except Exception as e:
        print(t, e)
