import sys, os, struct
sys.path.insert(0, r"C:\Users\User\Desktop\Клод мад\mudbot\tools")
import mm2

_orig = mm2.read_value
def read_value(b, p):
    if b[p] == 1:                      # vaList: значения до нуля
        p += 1; vals = []
        while b[p]:
            v, p = read_value(b, p); vals.append(v)
        return vals, p + 1
    return _orig(b, p)
mm2.read_value = read_value

D = {"С": (-1, 0, 0), "Ю": (1, 0, 0), "З": (0, -1, 0), "В": (0, 1, 0), "^": (0, 0, 1), "v": (0, 0, -1)}
OPP = {"С": "Ю", "Ю": "С", "З": "В", "В": "З", "^": "v", "v": "^"}
WORD = {"С": "север", "Ю": "юг", "З": "запад", "В": "восток", "^": "вверх", "v": "вниз"}

def exits(r):
    return set(c for c in str(r.get("Exits") or "") if c in D)

RED = ("clRed", "clMaroon", 255, 128)    # красные клетки (15.11 пользователь: не ходить): clRed — ловушки, clMaroon — комнаты боссов
out_dt, out_mg, out_red, errs, jmc_dt = [], [], [], [], []
for f in sorted(os.listdir(mm2.MAPS)):
    if not f.endswith(".mm2"):
        continue
    zone = f[:-4]
    try:
        rooms = [r for r in mm2.parse(os.path.join(mm2.MAPS, f)) if r.get("_class") == "TMudRoom2"]
    except Exception as e:
        errs.append("%s: %s" % (zone, e)); continue
    pos = {}
    for r in rooms:
        if all(isinstance(r.get(k), int) for k in ("X", "Y", "L")):
            pos[(r["X"], r["Y"], r["L"])] = r
    for r in rooms:
        kind = None
        if r.get("ImageIndex") == 1: kind = "ДТ"
        elif r.get("BColor") in RED: kind = "красная"
        elif r.get("BColor") == "clWhite": kind = "!магик"
        if not kind:
            continue
        x, y, l = r.get("X"), r.get("Y"), r.get("L")
        ways = []
        if isinstance(x, int):
            for d, (dx, dy, dl) in D.items():
                n = pos.get((x + dx, y + dy, l + dl))
                if n and OPP[d] in exits(n):          # из соседа n идти в сторону клетки
                    if kind in ("ДТ", "красная"):
                        ways.append("из «%s» не ходить на %s" % (n.get("Hint"), WORD[OPP[d]]))
                    else:
                        ways.append("вход: из «%s» на %s" % (n.get("Hint"), WORD[OPP[d]]))
        if kind in ("ДТ", "красная") and isinstance(x, int):
            for d, (dx, dy, dl) in D.items():
                n = pos.get((x + dx, y + dy, l + dl))
                if n and OPP[d] in exits(n) and n.get("BColor") not in RED:   # из соседней красной не считаем — туда и так не ходим
                    jmc_dt.append("%s;%s;%s" % (zone, n.get("Hint"), WORD[OPP[d]]))
        tag = " — %s" % ("ловушка" if r.get("BColor") in ("clRed", 255) else "босс") if kind == "красная" else ""
        line = "- **%s**%s (x%s y%s этаж %s): %s" % (r.get("Hint"), tag, x, y, l, "; ".join(ways) if ways else "вход на карте не найден")
        {"ДТ": out_dt, "красная": out_red}.get(kind, out_mg).append((zone, line))

# ручные запреты по словам пользователя: ЗОНЫ\запрет_выходы.txt (зона;клетка;направление;почему), UTF-8
MANUAL = r"C:\Users\User\Desktop\Клод мад\ЗОНЫ\запрет_выходы.txt"
out_man = []
if os.path.exists(MANUAL):
    for s in open(MANUAL, encoding="utf-8"):
        p = s.rstrip("\n").split(";")
        if len(p) >= 3 and not s.startswith("#"):
            jmc_dt.append("%s;%s;%s;зона" % (p[0], p[1], p[2]))   # «зона»: Эксплор.js сверяет вместе с зоной (MSDP)
            out_man.append((p[0], "- из «%s» не ходить на %s — %s" % (p[1], p[2], p[3] if len(p) > 3 else "")))

def section(title, items):
    res = ["## " + title, ""]
    cur = None
    for z, l in items:
        if z != cur:
            res += ["", "### " + z]; cur = z
        res.append(l)
    return res

txt = ["# ДТ и !магик по картам MUD Mapper", "",
       "Источник: `MUDMapper2023\\MUDMapper\\Maps\\Сфера Миров\\*.mm2`. ДТ = значок 1 (череп), !магик = белый цвет клетки (BColor clWhite).",
       "Направление «из клетки А не ходить на X» посчитано по осям карты (x = строка, y = столбец).", "ДТ с пометкой «вход на карте не найден» — это ДТ, куда падаешь, если нет полёта (аффект «плавная левитация»). Без этого аффекта из ренты не выходить.", ""]
txt += section("ДТ (%d)" % len(out_dt), out_dt) + [""]
txt += section("Красные клетки (%d) — не ходить (clRed — ловушка, clMaroon — босс; слова пользователя 15.11)" % len(out_red), out_red) + [""]
txt += section("Ручные запреты (%d) — `ЗОНЫ\\запрет_выходы.txt`, слова пользователя" % len(out_man), out_man) + [""]
txt += section("!магик (%d) — только для информации, ходить туда можно и нужно" % len(out_mg), out_mg)
if errs:
    txt += ["", "## Не прочитались", ""] + ["- " + e for e in errs]
open(r"C:\Users\User\Desktop\Клод мад\ДТ_И_МАГИК.md", "w", encoding="utf-8").write("\n".join(txt) + "\n")
# для JMC (Эксплор.js): зона;клетка, из которой не ходить;направление — cp1251
os.makedirs(r"C:\Users\User\Desktop\Клод мад\ЗОНЫ", exist_ok=True)
open(r"C:\Users\User\Desktop\Клод мад\ЗОНЫ\дт_выходы.txt", "w", encoding="cp1251", errors="replace").write("\n".join(sorted(set(jmc_dt))) + "\n")
print("ДТ", len(out_dt), "красных", len(out_red), "ручных", len(out_man), "!магик", len(out_mg), "ошибок", len(errs), "выходов в ДТ для JMC", len(set(jmc_dt)))
print(sum(1 for _, l in out_dt if "не найден" in l), "ДТ без входа")
