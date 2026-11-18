p = r"C:\Users\User\Desktop\Клод мад\JMC\claude.set"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
L = [("#alias {сдай} {сдать все} {claude}" if x.startswith("#alias {сдай}") else x) for x in L]
open(p, "wb").write(("\r\n".join(L)).encode("cp1251"))
print([x for x in L if x.startswith("#alias {сдай}")])
