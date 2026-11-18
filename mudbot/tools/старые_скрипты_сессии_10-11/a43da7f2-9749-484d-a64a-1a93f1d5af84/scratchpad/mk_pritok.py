import json, collections, sqlite3, re
exec(open(r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad\mk_alley.py", encoding="utf-8").read().split("SRC =")[0])   # R, RU, bfs
REC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon"
T = r"C:\Users\User\Desktop\Тадия\areas"
mv = [l.strip() for l in open(REC + r"\притон\raw_moves.txt", encoding="utf-8") if l.strip()]
go, back = bfs("100076", "100011"), bfs("100011", "100076")
lines = [".триг #scr botCore.BotInZone = false"] + go + [".триг обл с с"] + mv + back
open(T + r"\притон.botp", "wb").write(("\r\n".join(lines) + "\r\n").encode("cp1251"))
print("botp строк", len(lines), "| туда", go, "| обратно", back)

log = open(r"C:\Users\User\Desktop\Клод мад\JMC\притон", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
room = collections.Counter()
for i, l in enumerate(log):
    if l.startswith("[ Exits"):
        j = i + 1
        while j < len(log) and not re.match(r"^\d+H \d+M", log[j]) and j < i + 14:
            s = log[j].rstrip()
            if s and not s.startswith(("Труп", " ", "[")) and s.endswith(".") and " вас" not in s and len(s) < 95:
                room[re.sub(r"\s*\.\.\..*$", "", s).strip()] += 1
            j += 1
rows = open(REC + r"\притон\рр_притонV_mob.csv", "rb").read().decode("cp1251").split("\r\n")
head = rows[0]
orig = {}
for r in rows[1:]:
    if r.strip(): orig.setdefault(r.split(";")[0].strip('"'), r.split(";"))
kills = "Громила Путник Крупье Официантка Авантюрист Воровка Нищий Продавец_фруктов Паренек Брат_хозяина_таверны Бродяга Официант Бард Старый_вор".replace("_", " ").split(" ")
names = ["Громила", "Путник", "Крупье", "Официантка", "Авантюрист", "Воровка", "Нищий", "Продавец фруктов", "Паренек", "Брат хозяина таверны", "Бродяга", "Официант", "Бард", "Старый вор"]
out = [head]
for nm in names:
    key = nm.lower().split()[0][:5]
    cand = [s for s in room if key in s.lower() and re.match(r"^[А-ЯЁ]", s)]
    base = orig.get(nm)
    if not cand:
        print("нет строки комнаты:", nm); continue
    if not base:
        base = ['"%s"' % nm, '""', '""', '""', '""', '""', '""', '""', '""', '"false"', '"false"', '""', '"Воин"', '"человека"', '""']
        print("нет в исходном csv, создаю пустую строку:", nm)
    for s in sorted(cand):
        g = list(base); g[1] = '"%s "' % s
        out.append(";".join(g)); print("  ", nm, "<-", s)
open(T + r"\притон_mob.csv", "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
print("csv строк:", len(out) - 1)
