p = r"C:\Users\User\Desktop\Клод мад\JMC\claude.set"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
out = []
for x in L:
    if x.startswith("#alias {-сет1}"):
        x = "#alias {-сет1} {сня все;#2 кс :следак4 битв;кс :следак1 все15} {claude}"
    out.append(x)
open(p, "wb").write(("\r\n".join(out)).encode("cp1251"))
print([x for x in out if x.startswith("#alias {-сет")])
