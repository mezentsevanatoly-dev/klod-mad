import json, os, re, subprocess, sys
os.chdir(r"C:\Users\User\Desktop\Клод мад\mudbot")
env = dict(os.environ, MUD_VIA="bot")
def cmd(x):
    r = subprocess.run([sys.executable, "-X", "utf8", "tools/cmd.py", x], env=env, capture_output=True, encoding="utf-8", errors="replace", timeout=300)
    return r.stdout
def cur(out):
    m = re.findall(r"^\[cur\] .*?'vnum': '(\d+)'.*?'name': '([^']*)'.*?'area': '([^']*)'", out, re.M)
    if not m:
        m2 = re.findall(r"^\[cur\] .*?'vnum': '(\d+)'.*?'area': '([^']*)'.*?'name': '([^']*)'", out, re.M)
        return (m2[-1][0], m2[-1][2], m2[-1][1]) if m2 else ("?", "?", "?")
    return m[-1]
st = json.load(open(r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\бесы\бесы_route.json", encoding="utf-8"))["steps"]
k = next(i for i, s in enumerate(st) if s.get("cmd", "").startswith("область создать"))
j = next(i for i, s in enumerate(st[:k]) if s.get("room") == "Рощица")
seq = [s for s in st[j + 1:k] if "move" in s]
print(cmd("!go 104010").strip().splitlines()[-1], flush=True)
print("шагов от Рощицы:", len(seq), flush=True)
bad = 0
for s in seq:
    out = cmd(s["move"])
    v, n, a = cur(out)
    ok = (n == s["room"]) or s["room"].startswith("*")
    print(s["move"], "→", v, n, f"({a})", "" if ok else f"  <-- ждали «{s['room']}»", flush=True)
    bad += (not ok)
    if bad > 4:
        break
