import shutil
src = r"C:\Users\User\Desktop\Клод мад\Мад\Копия Мад\jmc\areas"
dst = r"C:\Users\User\Desktop\Тадия\areas"
L = [x.strip() for x in open(src + r"\рр1_Школа.botp", "rb").read().decode("cp1251").splitlines() if x.strip()]
assert L[0] == "север" and L[-1] == "юг", (L[0], L[-1])
# рр1: старт «Комната отдыха» (р1) -> наш старт «Склад» 100076: юг(Холл) вместо первого «север», конец: север (в склад) вместо «юг» (в комнату отдыха)
out = [".триг #scr botCore.BotInZone = true", "юг"] + L[1:-1] + ["север"]
open(dst + r"\школа.botp", "wb").write(("\r\n".join(out) + "\r\n").encode("cp1251"))
shutil.copyfile(src + r"\рр1_Школа_mob.csv", dst + r"\школа_mob.csv")
print(len(out), "строк")
