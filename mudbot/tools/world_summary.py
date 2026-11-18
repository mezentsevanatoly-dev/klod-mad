"""Сводка по картам маппера: data/world/_index.json."""
import json
import os

W = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "world")
d = json.load(open(os.path.join(W, "_index.json"), encoding="utf-8"))
big = sorted(d.items(), key=lambda kv: -kv[1]["rooms"])
print("зон:", len(d), "комнат:", sum(v["rooms"] for v in d.values()))
print("крупные:", ", ".join(f"{k}({v['rooms']})" for k, v in big[:15]))
print("пустые:", [k for k, v in d.items() if v["rooms"] == 0])
for z in ("Город Элендор", "Парк", "Канализация", "Аллея", "Болото"):
    if z in d:
        print(f"{z}: {d[z]['rooms']} комнат, переходы в: {d[z]['neighbours']}")
