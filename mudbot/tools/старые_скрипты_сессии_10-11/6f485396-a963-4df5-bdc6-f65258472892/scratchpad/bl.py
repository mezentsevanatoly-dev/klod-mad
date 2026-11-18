import re, sys
t = open(r"C:\Users\User\Desktop\Клод мад\JMC\бесы", "rb").read().decode("cp1251", errors="replace").replace("\r", "").split("\n")
i0 = next(i for i, l in enumerate(t) if l.strip().startswith("область создать"))
print("строк", len(t), "область на", i0)
# собрать: команды (строка после промпта, начинается со строчной), названия комнат (строка перед [ Exits ), особые строки
PROMPT = re.compile(r"^\d+H \d+M \d+V .*>\s*$")
out, room, after, prev = [], "?", False, "?"
special = re.compile(r"переме|телепорт|портал|внезапно|ослепит|вспышк|Вы оказались|падаете|проваливаетесь|рычаг|нажали|скрыт|потайн|Тоннель бесов|уровень|этаж|поднялись|спустились|затягивает|уносит|уноси", re.I)
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
            out.append(("CMD", i, s))
            continue
    m = re.match(r"^\[ Exits: ?(.*)\]", s)
    if m:
        out.append(("ROOM", i, prev, m.group(1)))
    if special.search(s) and not s.startswith("[Союзники") and "R.I.P" not in s:
        out.append(("SP", i, s[:140]))
    prev = s
for r in out[:int(sys.argv[1]) if len(sys.argv) > 1 else 200]:
    print(r)
