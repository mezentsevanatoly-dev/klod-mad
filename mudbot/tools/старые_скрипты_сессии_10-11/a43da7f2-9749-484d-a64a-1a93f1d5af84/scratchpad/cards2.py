import sqlite3
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
for z in ("Деревня рыбаков", "Лагерь кочевников", "Конюшни"):
    rows = c.execute("select name, level, prof, kind, desc, room from mob_cards where zone like ?", ("%" + z[:7] + "%",)).fetchall()
    print("\n==", z, len(rows))
    for r in rows: print("  %-28s ур.%-3s %-10s | desc: %-60s | комната: %s" % (r[0], r[1], r[2], (r[4] or "")[:60], (r[5] or "")[:30]))
print(c.execute("select distinct zone from mob_cards").fetchall()[:60])
