p = r"C:\Users\User\Desktop\Тадия\areas\гильда12.botp"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
if L[-1] == "": L.pop()
out = []
for l in L:
    if l.endswith("{стэ}"): l = l.replace("{стэ}", "{ехать стэдвик}")
    if l.endswith("{гео}"): l = l.replace("{гео}", "{ехать гео}")
    out.append(l)
    if l.endswith("{ехать стэдвик}") or l.endswith("{ехать гео}"):
        out.append(".пауза 80")                 # поездка идёт по остановкам; не посылать следующий шаг сразу (очистить стирает очередь)
open(p, "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
print("строк", len(out))
