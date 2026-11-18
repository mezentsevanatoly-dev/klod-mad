p = r"C:\Users\User\Desktop\Клод мад\JMC\claude.set"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
out = []
for x in L:
    if x.startswith("#alias {гир20}"):
        x = "#alias {гир20} {путь варвар;уч рукоп 20;уч доп 20;уч атак 20;уч ярость 20;путь склад} {claude}"
    out.append(x)
open(p, "wb").write(("\r\n".join(out)).encode("cp1251"))
print([x for x in out if x.startswith("#alias {гир")])
