import json
d = json.load(open(r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\sw_r1_r2.json", encoding="utf-8"))
RUN = {"n": "север", "s": "юг", "e": "восток", "w": "запад", "u": "вверх", "d": "вниз"}
T = r"C:\Users\User\Desktop\Тадия\areas"
hdr = '"Имя моба";"Описание в комнате";"Hp";"MaxHp";"Mp";"MaxMp";"Опыт";"Деньги";"Уровень";"Агрессивность";"Ассистит?";"Умения";"Профессия";"Раса";"Флаги NPC"\r\n'
for name, key in (("переход_р2", "fwd"), ("переход_р1", "rev")):
    ms = [".триг #scr botCore.BotInZone = false"] + [{"n":"север","s":"юг","e":"восток","w":"запад","u":"вверх","d":"вниз"}.get(m, m) for m in d[key]]
    ms = [m if m.startswith(".") else {"n":"север","s":"юг","e":"восток","w":"запад","u":"вверх","d":"вниз"}.get(m, m) for m in ms]
    open(T + "\\" + name + ".botp", "wb").write(("\r\n".join(ms) + "\r\n").encode("cp1251"))
    open(T + "\\" + name + "_mob.csv", "wb").write(hdr.encode("cp1251"))
    print(name, len(ms))
