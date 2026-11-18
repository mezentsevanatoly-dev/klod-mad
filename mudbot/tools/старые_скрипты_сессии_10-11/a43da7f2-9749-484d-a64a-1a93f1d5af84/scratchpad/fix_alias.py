import re
p = r"C:\Users\User\Desktop\Клод мад\JMC\claude.set"
raw = open(p, "rb").read().decode("cp1251")
L = raw.split("\r\n")
keep = [x for x in L if not re.match(r"^#alias \{-сет[123]\}", x)]
new = [
    "#alias {-сет1} {сня все;кс :следак1 все17;кс :колбы все.восст все.насы все.мы все.охр} {claude}",
    "#alias {-сет2} {сня все;#2 кс :следак1 палиц;кс :следак2 все17} {claude}",
    "#alias {-сет3} {сня все;кс :следак3 все17} {claude}",
]
while keep and keep[-1] == "": keep.pop()
out = "\r\n".join(keep + new) + "\r\n"
open(p, "wb").write(out.encode("cp1251"))
for x in out.split("\r\n"):
    if re.match(r"^#alias \{[+-]сет", x): print(x)
