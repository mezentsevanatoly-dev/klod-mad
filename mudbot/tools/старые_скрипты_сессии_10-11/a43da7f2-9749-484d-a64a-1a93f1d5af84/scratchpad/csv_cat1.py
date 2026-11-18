import re, collections
REC = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\каналгео1"
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\каналгео1", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
room = collections.Counter()
for i, l in enumerate(log):
    if l.startswith("[ Exits"):
        j = i + 1
        while j < len(log) and not re.match(r"^\d+H \d+M", log[j]) and j < i + 14:
            s = log[j].rstrip()
            if s and not s.startswith(("Труп", " ", "[")) and s.endswith(".") and "мертв" not in s and len(s) < 100:
                room[re.sub(r"\s*\.\.\..*$", "", s).strip()] += 1
            j += 1
names = {"Сколопендра": "сколопенд", "Канализационная крыса": "крыса", "Навозная муха": "навоз", "Водомерка": "водомерк", "Огромный слизень": "слизень",
         "Пиявка": "пиявк", "Овод": "овод", "Серый паук": "паук", "Улитка": "улитк", "Ядовитый клоп": "клоп", "Слепень": "слепен"}
EXCL = ("скорпион", "седая", "седой", "седые")
rows = open(REC + r"\рр_каналгео1V_mob.csv", "rb").read().decode("cp1251").split("\r\n")
orig = {r.split(";")[0].strip('"'): r.split(";") for r in rows[1:] if r.strip()}
print("в recon csv:", sorted(orig))
out = [rows[0]]
for nm, key in names.items():
    cand = [s for s in room if key in s.lower() and re.match(r"^[А-ЯЁ]", s) and not any(e in s.lower() for e in EXCL) and "Кладовщ" not in s]
    base = orig.get(nm) or next((v for k, v in orig.items() if key in k.lower()), None)
    if not base:
        base = ['"%s"' % nm, '""', '""', '""', '""', '""', '""', '""', '""', '"false"', '"false"', '""', '"Воин"', '"животное"', '""']
    if not cand:
        print("нет строки:", nm); continue
    for s in sorted(cand):
        g = list(base); g[0] = '"%s"' % nm; g[1] = '"%s "' % s
        out.append(";".join(g)); print("  ", nm, "<-", s)
open(r"C:\Users\User\Desktop\Тадия\areas\каты1_mob.csv", "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
print("csv строк:", len(out) - 1)
