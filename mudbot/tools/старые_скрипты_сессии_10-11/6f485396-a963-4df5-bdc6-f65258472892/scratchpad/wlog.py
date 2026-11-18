import os, re, collections
D = r"C:\Users\User\Desktop\Клод мад\JMC"
out = collections.OrderedDict()
for n in sorted(os.listdir(D), key=lambda x: os.path.getmtime(os.path.join(D, x))):
    p = os.path.join(D, n)
    if not os.path.isfile(p) or os.path.getsize(p) == 0 or n.endswith((".set", ".ini", ".js", ".dll", ".exe")):
        continue
    try:
        t = open(p, "rb").read().decode("cp1251", errors="replace")
    except OSError:
        continue
    lvl = re.findall(r"Варвар (\d+) уровня", t)
    for m in re.finditer(r"<(?:в (?:правой|левой) руке|в обеих руках|вторичное оружие|оружие)[^>]*>\s+(.+)", t):
        out.setdefault(n, collections.OrderedDict())[m.group(0).strip()[:90]] = 1
    if n in out:
        print(f"== {n} (лвл в логе: {lvl[:1]}-{lvl[-1:]})")
        for k in out[n]:
            print("   ", k)
