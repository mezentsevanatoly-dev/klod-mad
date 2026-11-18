p = r"C:\Users\User\Desktop\Клод мад\mudbot\tools\zone_exp.py"
s = open(p, encoding="utf-8").read()
a = '''lines = ["# Опыт за проход зоны «%s» (%s .. %s)" % (zone, seg[0][:8], seg[-1][:8]), "",
         "убийств: %d, опыта: %d, уровень игрока: %s" % (len(kills), tot, kills[0][3] if kills else level), "",
         "| моб | убито | опыт за моба (мин-макс) | всего |", "|---|---|---|---|"]
for name, v in by.items():
    es = [e for e, _ in v if e is not None]
    lines.append("| %s | %d | %s | %d |" % (name, len(v), ("%d-%d" % (min(es), max(es))) if es else "?", sum(es)))'''
b = '''ZN = {"аллея": "Аллея", "парк": "Парк", "школа": "Мад школа", "канал": "Канализация"}.get(zone, zone)
_c = sqlite3.connect(DB)
def card(name):
    r = _c.execute("select level, prof from mob_cards where name=? order by (zone=?) desc limit 1", (name, ZN)).fetchone()
    return r if r else ("?", "?")
lines = ["# Опыт за проход зоны «%s» (%s .. %s)" % (zone, seg[0][:8], seg[-1][:8]), "",
         "убийств: %d, опыта: %d, уровень игрока: %s" % (len(kills), tot, kills[0][3] if kills else level), "",
         "| моб | ур. моба | профа | убито | опыт за моба (мин-макс) | всего |", "|---|---|---|---|---|---|"]
for name, v in sorted(by.items(), key=lambda kv: -sum(e or 0 for e, _ in kv[1])):
    es = [e for e, _ in v if e is not None]
    lv, pf = card(name)
    lines.append("| %s | %s | %s | %d | %s | %d |" % (name, lv, pf, len(v), ("%d-%d" % (min(es), max(es))) if es else "?", sum(es)))'''
assert s.count(a) == 1
s = s.replace(a, b)
s = s.replace('zname = {"аллея": "Аллея", "парк": "Парк", "школа": "Мад школа"}.get(zone, zone)', 'zname = ZN')
open(p, "w", encoding="utf-8").write(s)
print("ok")
