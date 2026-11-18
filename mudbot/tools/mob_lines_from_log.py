"""Строки комнаты мобов из сырого лога пользователя -> _mob.csv для JMC-бота (в recon-csv описания часто перепутаны).

  python -X utf8 tools/mob_lines_from_log.py <лог> <csv_in> <csv_out>
Для каждого моба из csv_in (имя в 1-м столбце) ищет в логе строки комнаты (после «[ Exits…», без «Труп…»), начинающиеся с имени
(без учёта регистра). Каждая найденная строка -> отдельная строка csv (описание = строка + пробел). Мобов без строки печатает.
Дополнительно печатает строки комнат, похожих на мобов (заканчиваются точкой, 1-я буква заглавная), которых нет в csv: кандидаты.
"""
import collections, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JMC = os.path.join(os.path.dirname(ROOT), "JMC")
name, cin, cout = sys.argv[1:4]
log = open(os.path.join(JMC, name), "rb").read().decode("cp1251", "replace").replace("\r", "").split("\n")
lines = collections.Counter()
for i, l in enumerate(log):
    if l.startswith("[ Exits"):
        j = i + 1
        while j < len(log) and not re.match(r"^\d+H \d+M", log[j]) and j < i + 14:
            s = log[j].rstrip()
            if s and not s.startswith(("Труп", " ", "[")) and s.endswith((".", ")", "...")):
                lines[re.sub(r"\s*\.\.\..*$", "", s).strip()] += 1
            j += 1
rows = open(cin, "rb").read().decode("cp1251").split("\r\n")
out = [rows[0]]
have = set()
for r in rows[1:]:
    if not r.strip():
        continue
    f = r.split(";")
    nm = f[0].strip('"')
    cand = [s for s in lines if s.lower().startswith(nm.lower() + " ") or s.lower().startswith(nm.lower() + ",")]
    if not cand:
        print("нет строки комнаты в логе:", nm)
        continue
    for s in sorted(cand):
        g = list(f); g[1] = '"%s "' % re.sub(r"\(.*$", "", s).rstrip()
        out.append(";".join(g)); have.add(s)
open(cout, "wb").write("\r\n".join(out).encode("cp1251"))
print("строк в csv:", len(out) - 1)
extra = [(s, n) for s, n in lines.most_common() if s not in have and re.match(r"^[А-ЯЁ]", s) and n >= 2 and len(s) < 90][:25]
print("кандидаты (не в csv):")
for s, n in extra:
    print("  ", n, s)
