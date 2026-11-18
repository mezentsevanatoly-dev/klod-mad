import re
p = r"C:\Users\User\Desktop\Клод мад\JMC\claude.set"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
L = [x for x in L if not (x.startswith("#alias {айл}") or x.startswith("#alias {жда}"))]
while L and L[-1] == "": L.pop()
L += ["#alias {айл} {постой;3;айлина;1} {claude}", "#alias {жда} {постой;3;ждадиус;1} {claude}"]
open(p, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
print([x for x in L if x.startswith(("#alias {айл}", "#alias {жда}"))])
