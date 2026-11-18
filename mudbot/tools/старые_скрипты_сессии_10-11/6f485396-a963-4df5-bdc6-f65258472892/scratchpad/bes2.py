import json
R = r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\бесы"
st = json.load(open(R + r"\бесы_route.json", encoding="utf-8"))["steps"]
k = next(i for i, s in enumerate(st) if s.get("cmd", "").startswith("область создать"))
print(" | ".join(f"{s['move'][:2]}>{s['room'][:16]}" if "move" in s else ("K:" + ",".join(s["kill"]) if "kill" in s else "C:" + s["cmd"]) for s in st[:k + 1]))
print("--- cmds head")
print(open(R + r"\бесы_cmds.txt", encoding="utf-8").read().splitlines()[:6])
