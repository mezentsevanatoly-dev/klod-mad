import sqlite3
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
kw = ("фибул", "каск", "шахтер", "фонар", "ламп", "факел", "светоч", "свеч", "светл", "кристалл", "огонь", "огонек")
def show(title, rows):
    print("==", title, len(rows))
    for r in rows[:30]:
        print("  ", tuple(str(x)[:60] for x in r))
q = " or ".join(f"lower(name) like '%{k}%'" for k in kw)
show("ksk_items по флагу СВЕТ", c.execute("select dept,name,slot,minlvl,timer,flags,mods from ksk_items where flags like '%СВЕТ%' or mods like '%свет%' or mods like '%Свет%'").fetchall())
show("ksk_items по названию", c.execute(f"select dept,name,slot,minlvl,timer,flags from ksk_items where {q}").fetchall())
show("ex_items по флагу СВЕТ", c.execute("select name,slot,minlvl,timer,flags,mods from ex_items where flags like '%СВЕТ%' or mods like '%свет%'").fetchall())
show("ex_items по названию", c.execute(f"select name,slot,minlvl,timer,flags,mods from ex_items where {q}").fetchall())
show("weapons СВЕТ", c.execute("select src,name,minlvl,flags,aff from weapons where flags like '%СВЕТ%'").fetchall())
show("items (логи) СВЕТ/название", c.execute(f"select name,slot,min_lvl,flags,source from items where flags like '%СВЕТ%' or {q}").fetchall())
show("item_cards", c.execute(f"select name,slot,flags,affects from item_cards where flags like '%СВЕТ%' or affects like '%свет%' or {q}").fetchall())
lots = c.execute(f"select l.lot,l.name,l.price,l.lvl from exch_lots l where {q.replace('name','l.name')}").fetchall()
show("биржа лоты по названию", lots)
