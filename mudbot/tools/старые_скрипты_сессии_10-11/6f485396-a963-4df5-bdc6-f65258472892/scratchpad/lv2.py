import re, os, collections
D = r"C:\Users\User\Desktop\Клод мад\JMC"
pat = collections.Counter()
for n in ("аллея", "луга", "церковь", "рыбка"):
    t = open(os.path.join(D, n), "rb").read().decode("cp1251", errors="replace")
    for l in t.splitlines():
        if re.search(r"уровень|уровня|повыс", l) and "Вам надо" not in l and "уровня." not in l[:0]:
            pat[(n, l.strip()[:90])] += 1
for (n, l), c in list(pat.items())[:30]:
    print(n, c, l)
