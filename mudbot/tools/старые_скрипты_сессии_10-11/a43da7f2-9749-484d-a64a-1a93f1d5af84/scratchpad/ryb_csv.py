p = r"C:\Users\User\Desktop\Тадия\areas\рыбка_mob.csv"
rows = open(p, "rb").read().decode("cp1251").split("\r\n")
keep_names = ("Степной орел", "Жена рыбака", "Матрос", "Пьяный матрос", "Дюжий охранник", "Служанка")
out = [rows[0]] + [r for r in rows[1:] if r.strip() and r.split(";")[0].strip('"') in keep_names]
open(p + ".bak_chain", "wb").write(("\r\n".join(rows)).encode("cp1251"))
open(p, "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
print(len(out) - 1, "мобов")
