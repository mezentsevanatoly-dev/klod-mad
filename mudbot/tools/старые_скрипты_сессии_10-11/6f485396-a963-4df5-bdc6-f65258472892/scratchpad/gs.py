import sqlite3
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
print("--- gear_sets")
for r in c.execute("select * from gear_sets order by lvl, slot"):
    print(r)
print("--- items (name,type,slot,min_lvl,ac,timer,flags,source)")
for r in c.execute("select name,slot,min_lvl,ac,timer,mods,flags,source from items order by min_lvl, slot limit 120"):
    print(tuple(str(x)[:40] if x is not None else "" for x in r))
print("--- item_cards")
for r in c.execute("select name,slot,requires,ac,timer,flags,mods,place,rating from item_cards"):
    print(tuple(str(x)[:45] if x is not None else "" for x in r))
