import shutil
p = r"C:\Users\User\Desktop\Тадия\areas\привы1.botp"
shutil.copyfile(p, p + ".bak_enter")
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
assert L[24] == ".триг обл с в" and "122001" in L[25]
L.insert(25, "восток")
open(p, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
print("ok", len(L))
