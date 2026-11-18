import sqlite3
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
for (n,) in c.execute("select name from sqlite_master where type='table'"):
    cols = [r[1] for r in c.execute(f"pragma table_info({n})")]
    cnt = c.execute(f"select count(*) from {n}").fetchone()[0]
    if any(k in n for k in ("item", "equip", "kit", "gear", "ksk", "cloth")):
        print(n, cnt, cols)
print([n for (n,) in c.execute("select name from sqlite_master where type='table'")])
