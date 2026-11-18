import re
L = open(r"C:\Users\User\Desktop\Тадия\areas\рыбка.botp", "rb").read().decode("cp1251").split("\r\n")
L = [x for x in L if x != ""]
print("строк", len(L))
idx = [i for i, x in enumerate(L) if "== 117" in x]
print("строки с клетками 117:", idx[0], "..", idx[-1], "всего", len(idx))
for i in range(max(0, idx[0] - 3), idx[0] + 2): print(i, L[i][:150])
print("...")
for i in range(idx[-1] - 1, min(len(L), idx[-1] + 4)): print(i, L[i][:150])
print([ (i, x[:40]) for i, x in enumerate(L) if x.startswith(".триг") ][:8])
