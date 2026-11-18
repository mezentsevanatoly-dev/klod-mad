import sqlite3
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
print(c.execute("select count(*) from ksk_items").fetchone())
for r in c.execute("select slot,count(*) from ksk_items group by slot order by 2 desc"):
    print(r)
print("--- без слота")
for r in c.execute("select dept,name,type,minlvl,ac,mods from ksk_items where slot='' limit 20"):
    print(r)
