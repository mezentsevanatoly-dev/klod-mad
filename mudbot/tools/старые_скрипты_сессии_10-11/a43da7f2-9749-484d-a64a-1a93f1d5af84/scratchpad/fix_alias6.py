p = r"C:\Users\User\Desktop\Клод мад\JMC\claude.set"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
L = [x for x in L if not x.startswith("#alias {сдай}")]
while L and L[-1] == "": L.pop()
L.append("#alias {сдай} {кс :колбы все.насыщ все.восст все.мыш все.охр все.леч все.прозр;кс :общий все} {claude}")
open(p, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
print(L[-1])
