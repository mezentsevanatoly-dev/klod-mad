p = r"C:\Users\User\Desktop\Тадия\areas\притон_mob.csv"
rows = open(p, "rb").read().decode("cp1251").split("\r\n")
base = next(r for r in rows if r.startswith('"Громила";')).split(";")
base[1] = '"Громила лежит тут без сознания. "'
if not any("без сознания" in r for r in rows):
    rows.insert(len(rows) - 1 if rows[-1] == "" else len(rows), ";".join(base))
open(p, "wb").write("\r\n".join(rows).encode("cp1251"))
print("ok")
