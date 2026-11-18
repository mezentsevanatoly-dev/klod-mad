p = r"C:\Users\User\Desktop\Тадия\areas\каты1_mob.csv"
rows = open(p, "rb").read().decode("cp1251").split("\r\n")
out = [r for r in rows if "Крыса роется тут" not in r and "Огромная крыса копошится" not in r and "попытался ужалить" not in r]
open(p, "wb").write("\r\n".join(out).encode("cp1251"))
print(len(rows), "->", len(out))
