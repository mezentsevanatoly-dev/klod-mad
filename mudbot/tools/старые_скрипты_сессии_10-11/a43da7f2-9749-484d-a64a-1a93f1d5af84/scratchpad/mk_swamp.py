import json, collections, sqlite3
c = sqlite3.connect(r"C:\Users\User\Desktop\Клод мад\mudbot\data\game.db")
R = {r[0]: json.loads(r[1] or "{}") for r in c.execute("select vnum,exits from rooms")}
RU = {"N": "север", "S": "юг", "E": "восток", "W": "запад", "U": "вверх", "D": "вниз"}

def bfs(a, b):
    q = collections.deque([a]); p = {a: None}
    while q:
        v = q.popleft()
        if v == b: break
        for d, t in R.get(v, {}).items():
            t = str(t)
            if t not in p and t in R:
                p[t] = (v, d); q.append(t)
    out = []; v = b
    while p.get(v):
        pv, d = p[v]; out.append(RU[d]); v = pv
    assert v == a, (a, b)
    return out[::-1]

REC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon"
T = r"C:\Users\User\Desktop\Тадия\areas"
Q = json.load(open(REC + r"\болото_часть\raw_path_cut.json", encoding="utf-8"))
V = "#if {{$MsdpRoomVnum != {v}}} {{#scr botCore.wait(25);#scr seekstep = seekstep -2;очистить}};#if {{$MsdpRoomVnum == {v}}} {{{c}}}"
go, back = bfs("100076", "104043"), bfs("104043", "100076")
lines = [".триг #scr botCore.BotInZone = false"] + go + [".триг #scr botCore.BotInZone = true"] + [V.format(v=v, c=m) for v, m in Q] + back
open(T + r"\болото.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("botp строк:", len(lines), "| туда", len(go), "| обратно", len(back))

D = {
    "Комар": ["Комар жужжит над ухом."],
    "Комарик": ["Маленький комарик летает здесь."],
    "Кукушка": ["Кукушка сидит тут на ветке."],
    "Пиявка": ["Скользкая пиявка ползает по вашим ногам."],
    "Жаба": ["Зелёная жаба ловит насекомых."],
    "Лягушка": ["Лягушка сидит тут на кочке.", "Небольшая лягушка сидит на кочке."],
    "Цапля": ["Длинноногая цапля ловит лягушек."],
    "Москит": ["Огромный москит пытается укусить вас."],
    "Крупная рыбина": ["Крупная рыбина плавает в воде."],
    "Маленькая рыбешка": ["Маленькая рыбешка прячется под кочкой."],
    "Гадюка": ["Скользкая гадюка шевелится в камышах."],
    "Головастик": ["Хвостатый головастик носится по мелководью."],
    "Утенок": ["Облезший утёнок сидит в гнезде."],
    "Жук-плавунец": ["Жук-плавунец плавает здесь."],
    "Водомерка": ["Маленькая водомерка плавает здесь."],
    "Личинка майского жука": ["Личинка майского жука шевелится на полу."],
    "Жук-навозник": ["Жук-навозник ползёт куда-то."],
    "Летучая мышь": ["Большая летучая мышь висит под потолком."],
    "Мотылек": ["Мотылёк порхает над головой."],
    "Скользкий слизень": ["Скользкий слизень извивается на полу."],
    "Прозрачный паучок": ["Прозрачный паучок плетёт паутину."],
    "Многоножка": ["Многоножка ползёт к вам."],
}
rows = open(REC + r"\болото\болото_часть_mob.csv", "rb").read().decode("cp1251").split("\r\n")
orig = {}
for r in rows[1:]:
    if r.strip():
        orig.setdefault(r.split(";")[0].strip('"'), r.split(";"))
out = [rows[0]]
miss = []
for nm, ds in D.items():
    f = orig.get(nm)
    if not f:
        miss.append(nm); continue
    for d in ds:
        g = list(f); g[1] = '"%s "' % d
        out.append(";".join(g))
open(T + r"\болото_mob.csv", "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
print("csv строк:", len(out) - 1, "| нет в исходном csv:", miss)
