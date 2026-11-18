import ast, re
rx = re.compile(r"^\[msdp\] комната (\d+) \| ([^|]*) \| ([^|]*) \| (\{.*\})\s*$")
seq = []
for l in open(r"C:\Users\User\Desktop\Клод мад\mudbot\out.log", encoding="utf-8", errors="replace"):
    m = rx.match(l)
    if m and m.group(2).strip() == "Тоннель бесов":
        seq.append((m.group(1), m.group(3).strip(), ast.literal_eval(m.group(4))))
# последние ~120 переходов: найти прыжки (следующая клетка не среди соседей предыдущей)
tail = seq[-160:]
for a, b in zip(tail, tail[1:]):
    if b[0] not in {str(x) for x in a[2].values()} and a[0] != b[0]:
        print("ПРЫЖОК", a[0], a[1], a[2], "->", b[0], b[1], b[2])
