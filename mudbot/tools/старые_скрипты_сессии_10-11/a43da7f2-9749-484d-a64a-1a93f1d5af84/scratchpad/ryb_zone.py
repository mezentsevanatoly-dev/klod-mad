import re, collections
log = open(r"C:\Users\User\Desktop\Клод мад\JMC\рыбка", "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
st = next(i for i, l in enumerate(log) if l.strip().startswith("область создать"))
# конец зоны: последнее упоминание зоны/города после старта
end = len(log)
for i in range(len(log) - 1, st, -1):
    if re.match(r"^\[Зона, на .*(Болото|Окрестные|Элендор)", log[i]): end = i; break
print("зона: строки %d..%d (область создана на %d)" % (st, end, st))
kills = collections.defaultdict(lambda: [0, []])
last_exp = None
for i in range(st, end):
    m = re.match(r"^(.+?) (мертв|мертва|мертвы)\. R\.I\.P\.", log[i].strip())
    if m:
        nm = m.group(1).strip(); j = i + 1; exp = None
        while j < i + 6 and j < len(log):
            e = re.match(r"^Вы получили (\d+) единиц", log[j].strip())
            if e: exp = int(e.group(1)); break
            j += 1
        kills[nm][0] += 1
        if exp: kills[nm][1].append(exp)
print("\nУБИТО В ЗОНЕ (по логу, имя из строки «… мертв. R.I.P.»):")
for nm, (n, ex) in sorted(kills.items(), key=lambda x: -x[1][0]):
    print("  %-34s x%-3d опыт %s" % (nm, n, (sum(ex) // len(ex)) if ex else "?"))
# строки комнат в зоне: сразу после [ Exits ...] до приглашения
rooms = collections.Counter()
for i in range(st, end):
    if log[i].startswith("[ Exits"):
        j = i + 1
        while j < len(log) and log[j].strip() and not re.match(r"^\d+H \d+M", log[j].strip()) and j < i + 14:
            t = log[j].strip()
            if t and not t.startswith(("Труп", "[", "Кучка монет")) and re.search(r"[.!]$", t) and len(t) > 12: rooms[t] += 1
            j += 1
print("\nСТРОКИ МОБОВ В КОМНАТАХ ЗОНЫ (встречались >=2 раз):")
for t, n in rooms.most_common(80):
    if n >= 2: print("  x%-3d %s" % (n, t[:90]))
