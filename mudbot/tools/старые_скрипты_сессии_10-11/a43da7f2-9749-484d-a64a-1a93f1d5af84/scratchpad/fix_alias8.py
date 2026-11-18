p = r"C:\Users\User\Desktop\Клод мад\JMC\claude.set"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
new = "#alias {сдай} {кс :колбы все.насыщ все.восст все.мыш все.охр все.леч все.прозр;сдать все} {claude}"
L = [(new if x.startswith("#alias {сдай}") else x) for x in L]
open(p, "wb").write(("\r\n".join(L)).encode("cp1251"))
print([x for x in L if x.startswith("#alias {сдай}")])
