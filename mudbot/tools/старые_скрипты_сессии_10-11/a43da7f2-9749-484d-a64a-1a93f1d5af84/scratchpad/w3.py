import shutil
p = r"C:\Users\User\Desktop\Тадия\areas\притон.botp"
shutil.copyfile(p, p + ".bak_w3")
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
assert L[50:53] == ["запад", "запад", "запад"], L[48:56]
del L[52]
open(p, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
print("ok", len(L))
