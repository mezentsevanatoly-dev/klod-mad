import sqlite3, json
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
for r in c.execute("select vnum,name,exits from rooms where name='Южная улица' and vnum between 180000 and 180999"): print(r)
for r in c.execute("select vnum,name,exits from rooms where vnum between 181001 and 181012"): print(r)
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\огис_конюшни", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
last = None
for i in range(12664, len(log)):
    if log[i].startswith("[Зона, на") and "Конюшни" not in log[i]: last = i
print("последняя не-конюшни зона строка:", last, "всего", len(log))
# где пользователь покидает конюшни: последний раз 'Зона' с Огис
for i in range(len(log) - 1, 12664, -1):
    if re.match(r"^\[Зона", log[i]) if False else log[i].startswith("[Зона, на") and "Огис" in log[i]: print("посл. упоминание Огис", i, log[i]); break
