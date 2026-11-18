import re, shutil
p = r"C:\Users\User\Desktop\Тадия\areas\склад2.botp"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
def vc(x):
    m = re.search(r"== (\d+)\} \{([^}]*)\}$", x); return (m.group(1), m.group(2)) if m else (None, x)
out = []; i = 0; rem = 0
while i < len(L):
    if vc(L[i]) == ("114034", "север") and i + 1 < len(L) and vc(L[i + 1]) == ("114004", "юг"):
        i += 2; rem += 1; continue      # вход в кабинет и выход
    out.append(L[i]); i += 1
print("убрано заходов в кабинет:", rem, "строк:", len(L), "->", len(out))
# и вокруг 114004 команд быть не должно
print([vc(x) for x in out if vc(x)[0] == "114004"])
shutil.copyfile(p, p + ".bak_kab")
open(p, "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
