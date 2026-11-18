import os, re, subprocess, sys
os.chdir(r"C:\Users\User\Desktop\Клод мад\mudbot")
env = dict(os.environ, MUD_VIA="bot")
rows = [l.split("\t") for l in open(r"C:\Users\User\Desktop\Клод мад\mudbot\data\recon\бесы\бесы_cmds.txt", encoding="utf-8").read().splitlines()]
k = next(i for i, r in enumerate(rows) if r[0] == "область создать с")
M = ("север", "юг", "восток", "запад", "вверх", "вниз")
def cmd(c):
    r = subprocess.run([sys.executable, "-X", "utf8", "tools/cmd.py", c], env=env, capture_output=True, encoding="utf-8", errors="replace", timeout=300)
    return r.stdout
def cur(out):
    m = re.findall(r"^\[cur\] .*?'vnum': '(\d+)'.*?'name': '([^']*)'", out, re.M)
    return m[-1] if m else ("?", "?")
cmd("!go 115050")
bad = 0
for i in range(k):
    c, _ = rows[i][0], rows[i][1]
    if c not in M:
        continue
    out = cmd(c)
    v, n = cur(out)
    exp = rows[i + 1][1][2:] if i + 1 < len(rows) else "?"
    fail = "Вы не можете идти" in out
    flag = "" if (n == exp or exp.startswith("*") or fail) else f"  <-- ждали «{exp}»"
    print(i, c, "→", v, n, "НЕУДАЧА" if fail else "", flag, flush=True)
    if flag:
        bad += 1
        if bad > 3:
            break
