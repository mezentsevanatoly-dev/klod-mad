import re
t = open(r"C:\Users\User\Desktop\Клод мад\JMC\бесы", "rb").read().decode("cp1251", errors="replace").replace("\r", "").split("\n")
idx = [i for i, l in enumerate(t) if l.strip() == "Зал обучения"][0]
seg = t[idx - 6: idx + 160]
for l in seg:
    s = l.rstrip()
    if s.strip() and not re.match(r"^[\s+|:\-~^@%$_\]\[RmGO\"vV<>=#*.!]+$", s):
        print(s[:150])
