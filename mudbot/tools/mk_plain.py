"""Маршрут Чвырлы без vnum -> .botp с нулевыми vnum для режима plain: python tools/mk_plain.py <botp> <с_строки> <по_строку> <выход>"""
import sys

src = open(sys.argv[1], encoding="cp1251").read().splitlines()
a, b = int(sys.argv[2]), int(sys.argv[3])
out = ["#if {$MsdpRoomVnum ==0} {#var SumReset 0}"]          # маркер начала для load_steps
for l in src[a - 1:b]:
    l = l.strip()
    if l:
        out.append(l if l.startswith(".триг") else "#if {$MsdpRoomVnum ==0} {%s}" % l)
open(sys.argv[4], "w", encoding="cp1251", newline="\r\n").write("\n".join(out) + "\n")
print(len(out), "строк")
