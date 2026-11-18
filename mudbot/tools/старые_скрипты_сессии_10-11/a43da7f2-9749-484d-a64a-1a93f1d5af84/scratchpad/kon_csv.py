S = r"C:\Users\User\AppData\Local\Temp\claude\c875d00ec83f8f7f\a43da7f2-9749-484d-a64a-1a93f1d5af84\scratchpad"
rows = open(S + r"\kon_mob.csv", "rb").read().decode("cp1251").split("\r\n")
keep = [r for r in rows if r.strip() and not r.startswith('"Кто-то"') and not r.startswith('"Учитель верховой езды"')]
open(r"C:\Users\User\Desktop\Тадия\areas\конюшни_mob.csv", "wb").write(("\r\n".join(keep) + "\r\n").encode("cp1251"))
print(len(keep) - 1, "мобов")
