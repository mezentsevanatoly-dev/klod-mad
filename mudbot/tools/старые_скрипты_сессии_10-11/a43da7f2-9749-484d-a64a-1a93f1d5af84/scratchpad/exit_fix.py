import shutil
p = r"C:\Users\User\Desktop\Тадия\areas\притон.botp"
shutil.copyfile(p, p + ".bak_exit")
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
print([ (i, L[i]) for i in range(50, 60)])
assert L[53:57] == ["юг", "запад", "юг", "юг"], L[53:57]
L[53:57] = ["запад", "юг", "юг"]       # из «Полутемного коридора»: запад (Стойка), юг (Внутри притона), юг (Перед притоном)
open(p, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
print("ok", len(L))
