T = r"C:\Users\User\Desktop\Тадия\areas"
p = T + r"\гильда5.botp"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
n = 0
for i, l in enumerate(L):
    if l == ".триг снять 300":
        L[i] = ".триг снять 55555"; n += 1
open(p, "wb").write("\r\n".join(L).encode("cp1251"))
print("гильда5: заменено", n)
q = T + r"\переход_р2.botp"
M = open(q, "rb").read().decode("cp1251").split("\r\n")
if M[-1] == "": M.pop()
if ".триг рерент" not in M:
    M += ["запад", "вниз", ".триг рерент", "вверх", "восток"]     # Центральный зал гостиницы Геоланта 115050: дом = р2 (рекол и вход после рипа)
open(q, "wb").write(("\r\n".join(M) + "\r\n").encode("cp1251"))
print("переход_р2 строк:", len(M))
