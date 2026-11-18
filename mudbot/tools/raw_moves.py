"""Успешные ходы из СЫРОГО лога пользователя (без графа БД; для зон, где граф неполный) -> plain-маршрут для JMC-бота.

  python -X utf8 tools/raw_moves.py <лог> "<строка создания в логе>" "<название клетки создания (старта)>" [--out файл.txt]
Ход = строка-команда север/юг/…; неудачным считается, если до следующей комнаты есть «Вы не можете идти», «Не получится»,
«закрыт», «Вы уже…». Обрезка: после последнего прихода в комнату с названием клетки создания.
Печатает число ходов и список; --out пишет по ходу на строку.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JMC = os.path.join(os.path.dirname(ROOT), "JMC")
name, create, startroom = sys.argv[1:4]
out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
SH = {"с": "север", "ю": "юг", "в": "восток", "з": "запад", "вв": "вверх", "вн": "вниз"}
MV = {"север", "юг", "восток", "запад", "вверх", "вниз"}
FAIL = re.compile(r"Вы не можете идти|Не получится|закрыт|заперт|не пускает|сначала открыть|Сначала откройте")
log = open(os.path.join(JMC, name), "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
i0 = next(i for i, l in enumerate(log) if l.strip().startswith(create))

def room_above(j, lo):
    for k in range(j - 1, max(lo, j - 14), -1):
        s = log[k].strip()
        if s and not log[k].startswith(" ") and not s.endswith((".", "!", "?", ",", ":")) and not re.match(r"^\d+H", s):
            return s
    return "?"

moves = []   # (ход, комната прибытия); команды дверей (отпер/откр) идут как (".триг <текст>", "")
i = i0 + 1
while i < len(log):
    s = SH.get(log[i].strip(), log[i].strip())
    if re.match(r"^(отпер|откр) \S+( \S+)?$", s):
        moves.append((".триг " + s, ""))
    if s in MV:
        ok, arr = True, None
        for j in range(i + 1, min(i + 30, len(log))):
            t = log[j].strip()
            if SH.get(t, t) in MV:
                break                                  # следующая команда: ответа-комнаты не было
            if FAIL.search(t):
                ok = False; break
            if log[j].startswith("[ Exits"):
                arr = room_above(j, i); break
        if ok:
            moves.append((s, arr or "?"))
    i += 1
ends = [k for k, (m, r) in enumerate(moves) if r == startroom and k > 0]
cut = moves[: ends[-1] + 1] if ends else moves
print("успешных ходов:", len(moves), "| до возврата в «%s»: %d" % (startroom, len(cut)))
print(" ".join(m for m, _ in cut))
if out:
    open(out, "w", encoding="utf-8").write("\n".join(m for m, _ in cut) + "\n")
    print("записано:", out)




