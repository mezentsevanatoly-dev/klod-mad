import re, sys, collections
src = open(r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js", "rb").read().decode("cp1251")
body = src[src.index("var InspectionWords = [") : src.index("];", src.index("var InspectionWords = ["))]
pats = []
for m in re.finditer(r"(?<![\w)])/((?:\\.|[^/\\\n])+)/", body):
    try:
        pats.append(re.compile(m.group(1)))
    except re.error:
        pass
print("шаблонов:", len(pats))
files = sys.argv[1:]
cnt = collections.Counter()
for f in files:
    for l in open(f, "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n"):
        l = re.sub(r"^\d\d:\d\d:\d\d ", "", l).rstrip()
        if not l.strip() or l.startswith(("## ", ">> ")):
            continue
        if re.match(r"^\d+H \d+M", l) or l.startswith("[ Exits") or "[Союзники]" in l or "Союзники" in l:
            continue
        if not any(p.search(l) for p in pats):
            cnt[l.strip()] += 1
print("не в словаре:", len(cnt))
for s, n in [(s, n) for s, n in cnt.most_common() if re.search(r"[а-яА-Я]{3}", s) and len(s) > 3 and not re.match(r"^(очистить|вст|од все|заб |смотреть|убить|у \d)", s)]:
    print(n, "|", s[:100])


