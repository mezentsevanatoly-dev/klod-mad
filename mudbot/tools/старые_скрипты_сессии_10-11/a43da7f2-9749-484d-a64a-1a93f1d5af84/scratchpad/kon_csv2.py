p = r"C:\Users\User\Desktop\Тадия\areas\конюшни_mob.csv"
rows = open(p, "rb").read().decode("cp1251").split("\r\n")
drop = ("Неопытный наездник", "Помощник конюха", "Младший конюх", "Старший конюх", "Старый кузнец", "Хромой старик", "Зеленоглазая девчушка", "Высокая девушка")
keep = [r for r in rows if r.strip() and r.split(";")[0].strip('"') not in drop]
open(p + ".bak_people", "wb").write("\r\n".join(rows).encode("cp1251"))
open(p, "wb").write(("\r\n".join(keep) + "\r\n").encode("cp1251"))
print(len(keep) - 1, "мобов осталось; убрано", len(rows) - 1 - (len(keep) - 1))
