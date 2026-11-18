import json, re, sys
R = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon"
ab = {"север": "n", "юг": "s", "восток": "e", "запад": "w", "вверх": "u", "вниз": "d"}
for name in sys.argv[1:]:
    st = json.load(open(f"{R}\\{name}\\{name}_route.json", encoding="utf-8"))["steps"]
    k = next(i for i, s in enumerate(st) if s.get("cmd", "").startswith("область создать"))
    pre = st[:k]
    # старт: после первого «вниз» (Верхний зал -> Центральный зал) для Геоланта
    j = next((i for i, s in enumerate(pre) if s.get("move") == "вниз" and s["room"] == "Центральный зал"), None)
    seq = pre[j + 1:] if j is not None else pre
    p = "".join(ab[s["move"]] for s in seq if "move" in s)
    print(name, "старт Геолант-зал" if j is not None else "старт неясен", "| ходов", len(p), "|",
          re.sub(r"(.)\1+", lambda m: f"{len(m.group(0))}{m.group(1)}", p), "| последняя клетка:", seq[-1].get("room") if seq else None,
          "| область:", st[k]["cmd"])
