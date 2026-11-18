import shutil, os
A = r"C:\Users\User\Desktop\Тадия\areas"
# вернуть конюшни как было
b = os.path.join(A, "конюшни_mob.csv.bak_people")
if os.path.exists(b):
    shutil.copyfile(b, os.path.join(A, "конюшни_mob.csv")); print("конюшни_mob.csv восстановлен из бэкапа")
def show(path, title):
    rows = open(path, "rb").read().decode("cp1251").split("\r\n")
    print("\n== %s (%d)" % (title, len([r for r in rows[1:] if r.strip()])))
    for r in rows[1:]:
        p = r.split(";")
        if len(p) > 8: print("%-30s ур.%-3s | %s" % (p[0].strip('"'), p[8].strip('"'), p[1].strip('" ')[:70]))
show(os.path.join(A, "рыбка_mob.csv.bak_chain"), "РЫБКА (как в recon, 31 строка)")
show(os.path.join(A, "кочи_mob.csv"), "КОЧИ (сейчас в списке)")
show(os.path.join(A, "конюшни_mob.csv"), "КОНЮШНИ")
