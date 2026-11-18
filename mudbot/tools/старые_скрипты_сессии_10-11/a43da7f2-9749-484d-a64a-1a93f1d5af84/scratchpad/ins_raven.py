import shutil
p = r"C:\Users\User\Desktop\Тадия\areas\аллея.botp"
shutil.copyfile(p, p + ".bak_raven")
L = open(p, "rb").read().decode("cp1251").split("\r\n")
i = next(k for k, l in enumerate(L) if "== 146044}" in l)
assert L[i].endswith("{юг}"), L[i]
L.insert(i, ".триг уби старый")          # старый ворон прилетает на помощь вороненку: добить после боя в 146044
open(p, "wb").write("\r\n".join(L).encode("cp1251"))
print("вставлено перед строкой", i, "; всего", len(L))
