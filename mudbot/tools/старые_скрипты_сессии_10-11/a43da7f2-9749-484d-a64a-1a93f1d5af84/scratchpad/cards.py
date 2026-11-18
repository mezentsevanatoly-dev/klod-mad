import sqlite3
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
cols = [r[1] for r in c.execute("pragma table_info(mob_cards)")]
print(cols, c.execute("select count(*) from mob_cards").fetchone())
lines = ["Мужик средних лет с крючками", "Старый рыбак со снастями", "Седой старик, помогающий", "Молодой парнишка идет к морю", "Жирный котяра", "Речной сом", "Сильный рыбак плетется", "Веселый матрос", "Жена рыбака хлопочет", "Дюжий мужик", "Служанка бегает", "облезлая крыса пытается", "Красивая рыбешка", "Большая паучиха", "Складской смотритель", "разъяренный энт", "по имени Контар", "капитан эльфийского", "эльфийский воин стоит", "Мертвецки пьяный матрос", "облако молочного", "облако черного"]
for l in lines:
    rows = c.execute("select * from mob_cards where line like ? or room_line like ? limit 3", ("%" + l + "%", "%" + l + "%")).fetchall() if "line" in cols or "room_line" in cols else []
    print(l, "->", rows[:2])
