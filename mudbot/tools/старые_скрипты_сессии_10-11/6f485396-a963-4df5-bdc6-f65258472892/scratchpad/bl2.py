import re, sys
t = open(r"C:\Users\User\Desktop\Клод мад\JMC\бесы", "rb").read().decode("cp1251", errors="replace").replace("\r", "").split("\n")
i0 = next(i for i, l in enumerate(t) if l.strip().startswith("область создать"))
PROMPT = re.compile(r"^\d+H \d+M \d+V .*>\s*$")
MV = {"север", "юг", "восток", "запад", "вверх", "вниз"}
seq, after, prev, kills, lastmove = [], False, "?", 0, None
for i, l in enumerate(t[i0:], start=i0):
    s = l.strip()
    if PROMPT.match(s):
        after = True
        continue
    if not s:
        continue
    if after:
        after = False
        if (s[0].islower() or s[0].isdigit()) and len(s) < 50:
            if s in MV:
                if kills:
                    seq.append(f"[K{kills}]")
                    kills = 0
                lastmove = s
                seq.append(s[:2])
            elif s not in ("убить 2.", "яр и", "яр к", "очистить", "у 3", "у 1", "смотреть"):
                seq.append(f"<{s}>")
            continue
    m = re.match(r"^\[ Exits: ?(.*)\]", s)
    if m:
        seq.append(f"@{prev}[{m.group(1).strip()}]")
    if "R.I.P." in s:
        kills += 1
    if re.search(r"переместились|Вы оказались|Вы попали", s):
        seq.append("!!!" + s)
    prev = s
print(" ".join(seq))
