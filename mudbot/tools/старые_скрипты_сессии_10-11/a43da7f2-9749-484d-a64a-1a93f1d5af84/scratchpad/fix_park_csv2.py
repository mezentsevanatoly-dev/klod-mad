p = r"C:\Users\User\Desktop\Тадия\areas\парк_mob.csv"
bak = open(p + ".bak", "rb").read().decode("cp1251").split("\r\n")
cur = open(p, "rb").read().decode("cp1251").split("\r\n")
row = next(r for r in bak if r.startswith('"Ворон";'))
if not any(r.startswith('"Ворон";') for r in cur):
    i = max(i for i, r in enumerate(cur) if r.startswith('"'))
    cur.insert(i + 1, row)
open(p, "wb").write("\r\n".join(cur).encode("cp1251"))
print(row[:90])
