import ast, re
rx = re.compile(r"^\[msdp\] комната (\d+) \| ([^|]*) \| ([^|]*) \| (\{.*\})\s*$")
g = {}
for l in open(r"C:\Users\User\Desktop\Клод мад\mudbot\out.log", encoding="utf-8", errors="replace"):
    m = rx.match(l)
    if m and m.group(2).strip() == "Тоннель бесов":
        g[m.group(1)] = (m.group(3).strip(), {k: str(v) for k, v in ast.literal_eval(m.group(4)).items()})
for v in sorted(g):
    n, e = g[v]
    out = {d: t for d, t in e.items() if t not in g}
    print(v, n, e, "| ВНЕ:", out if out else "")
