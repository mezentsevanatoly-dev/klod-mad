import shutil
p = r"C:\Users\User\Desktop\Тадия\areas\притон.botp"
shutil.copyfile(p, p + ".bak_hatch")
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
i = 36
assert L[i] == "вниз", (L[i], L[i-2:i+2])
L[i:i] = [".триг отпер люк", ".триг откр люк"]
open(p, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
print("ok", len(L))
