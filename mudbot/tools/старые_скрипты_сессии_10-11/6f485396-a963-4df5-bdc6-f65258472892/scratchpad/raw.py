import re
ab = {"север": "n", "юг": "s", "восток": "e", "запад": "w", "вверх": "u", "вниз": "d"}
L = [l.split("\t")[0] for l in open(r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\бесы\бесы_cmds.txt", encoding="utf-8").read().splitlines()]
k = L.index("область создать с")
print(L[:k])
seq = [ab[c] for c in L[:k] if c in ab]
p = "".join(seq)
print(len(p), re.sub(r"(.)\1+", lambda m: f"{len(m.group(0))}{m.group(1)}", p))
