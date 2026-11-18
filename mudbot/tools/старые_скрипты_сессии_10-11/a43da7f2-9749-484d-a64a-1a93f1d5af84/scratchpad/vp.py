import shutil
p = r"C:\Users\User\Desktop\Тадия\settings\дкаре.js"
shutil.copyfile(p, p + ".bak_vp")
s = open(p, "rb").read().decode("cp1251")
a = "var countMinVp = 30;"
assert s.count(a) == 1
s = s.replace(a, "var countMinVp = 0; ")
open(p, "wb").write(s.encode("cp1251"))
print("ok")
