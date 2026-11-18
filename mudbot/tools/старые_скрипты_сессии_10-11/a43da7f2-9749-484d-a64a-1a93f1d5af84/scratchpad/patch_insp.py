import shutil
p = r"C:\Users\User\Desktop\Клод мад\JMC БОТ ИНКА\scripts\Inspection.js"
shutil.copyfile(p, p + ".bak_school")
s = open(p, "rb").read().decode("cp1251")
new = ["/(О|о)синое гнездо/", "/желобе\\./", "/сквознячок\\./", "/оружием\\./"]
add = [w for w in new if w not in s]
anchor = "/ловушке собратья./, "
assert s.count(anchor) == 1
nl = "\r\n" if "\r\n" in s else "\n"
s = s.replace(anchor, anchor + nl + "\t" + ", ".join(w for w in add) + ", ")
open(p, "wb").write(s.encode("cp1251"))
print("добавлено:", add)
