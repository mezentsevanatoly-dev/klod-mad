p = r"C:\Users\User\Desktop\Тадия\areas\склад2_mob.csv"
rows = open(p, "rb").read().decode("cp1251").split("\r\n")
out = [r for r in rows if not r.startswith('"Охранник склада";') and "Управляющ" not in r]
open(p, "wb").write("\r\n".join(out).encode("cp1251"))
print(len(rows), "->", len(out))
