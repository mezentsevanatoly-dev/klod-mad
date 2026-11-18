import re
p = r"C:\Users\User\Desktop\Клод мад\JMC\claude.set"
L = open(p, "rb").read().decode("cp1251").split("\r\n")
names = ["-сет1", "-сет2", "+сет0", "+колб0", "+колб1", "гир2", "гир20"]
keep = [x for x in L if not any(x.startswith("#alias {%s}" % n) for n in names)]
while keep and keep[-1] == "": keep.pop()
new = [
    "#alias {-сет1} {сня все;кс :следак1 все15;кс :колбы все.восст все.насы все.мы все.охр} {claude}",
    "#alias {-сет2} {сня все;#2 кс :следак4 палиц;кс :следак2 все15} {claude}",
    "#alias {+сет0} {#2 кз :следак4 битв;од все2} {claude}",
    "#alias {+колб0} {#2 кз :колбы насыщ} {claude}",
    "#alias {+колб1} {#2 кз :колбы восс;#2 кз :колбы охр;#2 кз :колбы мыши;кз :колбы насыщ} {claude}",
    "#alias {гир2} {путь варвар;уч доп 20;уч атак 20;уч дуб 20;путь склад} {claude}",
    "#alias {гир20} {уч рукоп 20;уч доп 20;уч атак 20;уч ярость 20} {claude}",
]
open(p, "wb").write(("\r\n".join(keep + new) + "\r\n").encode("cp1251"))
for x in keep + new:
    if re.match(r"^#alias \{(\+|-)?(сет|колб|гир)", x) or x.startswith("#alias {гир"): print(x)
