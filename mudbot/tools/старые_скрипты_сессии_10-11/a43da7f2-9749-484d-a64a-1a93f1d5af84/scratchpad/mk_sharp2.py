import re
D = {"n": "север", "s": "юг", "e": "восток", "w": "запад", "u": "вверх", "d": "вниз"}
def ex(sw):
    out = []
    for n, c in re.findall(r"(\d*)([nsewud])", sw):
        out += [D[c]] * (int(n) if n else 1)
    return out
def build(gloves=False, rage=False):
    L = [".триг #scr botCore.BotInZone = false"]
    L += ex("s2ese") + [".триг клан снять 250000"] + ex("w") + ex("nwnn")[0:0]
    # банк -> склад: обратный к s2ese = w n w n n
    L = [L[0]] + ex("s2ese") + [".триг клан снять 250000"] + ex("wnwwn")
    L += ex("s2en4e2s4e") + [".триг войт", ".пауза 50", ".триг куп 1", ".пауза 50"]
    L += ex("3wn3wsws2wsws3wnw2n") + [".триг войт", ".пауза 80"]
    L += ex("n2d4nu4n3w3nwn")
    if rage:
        pass
    if gloves:
        L += [".триг заточить маст перчатка.правую", ".пауза 30", ".триг заточить маст перчатка.левую", ".пауза 30"]
    else:
        L += [".триг заточить маст палица", ".пауза 30", ".триг заточить маст легкая", ".пауза 30"]
    L += ex("se3s3e4sd4s2us") + [".триг войт", ".пауза 80", ".триг куп 1", ".пауза 50"]
    L += ex("3nwnwn3wsw") + [".триг войт", ".пауза 80"]
    L += ex("4w2n4ws2wn")
    return L
import sys
for name, gl in (("заточка", False), ("заточка20", True)):
    L = build(gl)
    open(r"C:\Users\User\Desktop\Тадия\areas\%s.botp" % name, "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
    open(r"C:\Users\User\Desktop\Тадия\areas\%s_mob.csv" % name, "wb").write(('"Имя моба";"Описание в комнате";"Hp";"MaxHp";"Mp";"MaxMp";"Опыт";"Деньги";"Уровень";"Агрессивность";"Ассистит?";"Умения";"Профессия";"Раса";"Флаги NPC"\r\n').encode("cp1251"))
    print(name, len(L))

L = [".триг #scr botCore.BotInZone = false"] + ex("se3s3e4sd4s2us") + [".триг войт", ".пауза 80", ".триг куп 1", ".пауза 50"] + ex("3nwnwn3wsw") + [".триг войт", ".пауза 80"] + ex("4w2n4ws2wn")
open(r"C:\Users\User\Desktop\Тадия\areas\заточка_назад.botp", "wb").write(("\r\n".join(L) + "\r\n").encode("cp1251"))
open(r"C:\Users\User\Desktop\Тадия\areas\заточка_назад_mob.csv", "wb").write(open(r"C:\Users\User\Desktop\Тадия\areas\заточка_mob.csv", "rb").read())
print(len(L))
