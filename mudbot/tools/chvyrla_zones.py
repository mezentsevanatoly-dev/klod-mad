"""Сводка зон JMC-бота Чвырла (areas/*.botp + _mob.csv, cp1251): мобы, уровни, комнаты, квестовые строки.

python tools/chvyrla_zones.py [папка_areas]  -> areas/chvyrla_zones.md
"""
import csv
import glob
import os
import re
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\User\Desktop\мад\БОТ ЧВЫРЛА\areas"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "areas", "chvyrla_zones.md")
SKIP = re.compile(r"^(ждать|гг|бгр|прыг|пну|#|look|подкр|ПоискКлетки|БотОдеться|заряжай|од все|войт$)")


def zone(botp):
    lines = open(botp, encoding="cp1251").read().splitlines()
    vnums = re.findall(r"\$MsdpRoomVnum ==\s*(\d+)\}", "\n".join(lines))
    acts = []
    for l in lines:
        if l.startswith(".триг") or "#if" in l:
            for c in re.sub(r"^\.триг", "", re.sub(r".*\{\$MsdpRoomVnum ==\s*\d+\} \{([^}]*)\}.*", r"\1", l)).split(";"):
                c = c.strip()
                if c and not SKIP.match(c) and not re.fullmatch(r"(подкр )?(север|юг|восток|запад|вверх|вниз)|\d*[nsewud]+.*", c):
                    acts.append(c)
    entry = next((l for l in lines if "область создать" in l or "Создание_области" in l), "")
    return sorted(set(vnums)), list(dict.fromkeys(acts)), entry


def mobs(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="cp1251") as f:
        return [r for r in csv.DictReader(f, delimiter=";")]


def main():
    out = ["# Зоны бота Чвырла (ДК) — сводка", "", "Чвырла — рыцарь смерти: его `пну`, `тр` (тёмный ритуал), `мв` (масс. вред) — "
           "не для друида. Маршрут = последовательность vnum; квестовые действия — ниже.",
           "«рр5» = rest room 5 = Артуанель: маршруты рр5_* начинаются оттуда (спидволк до зоны — от Артуанеля).", ""]
    for botp in sorted(glob.glob(os.path.join(SRC, "рр5_*.botp")) + glob.glob(os.path.join(SRC, "Слава_*.botp"))):
        name = os.path.basename(botp)[:-5]
        vnums, acts, entry = zone(botp)
        ms = mobs(botp[:-5] + "_mob.csv")
        lv = [int(m["Уровень"]) for m in ms if (m.get("Уровень") or "").isdigit()]
        peace = [m["Имя моба"] for m in ms if "Мирный" in (m.get("Флаги NPC") or "")]
        zones = sorted({v[:-3] for v in vnums})
        out.append(f"## {name}")
        out.append(f"- комнат в маршруте: {len(vnums)}, зоны vnum: {', '.join(zones) or '-'}")
        if ms:
            out.append(f"- мобов: {len(ms)}, уровни {min(lv) if lv else '?'}–{max(lv) if lv else '?'}"
                       + (f"; мирные: {', '.join(peace)}" if peace else ""))
        if entry:
            out.append(f"- вход: `{entry.strip()[:120]}`")
        if acts:
            out.append("- действия: " + "; ".join(f"`{a}`" for a in acts[:25]))
        out.append("")
    open(OUT, "w", encoding="utf-8").write("\n".join(out))
    print(OUT)


if __name__ == "__main__":
    main()
