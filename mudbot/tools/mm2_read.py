"""Читалка карт MUD Mapper (.mm2 = поток Delphi TPF0 с объектами TMudRoom2).

python tools/mm2_read.py              -> data/world/<зона>.json + data/world/_index.json
python tools/mm2_read.py Парк         -> печать одной зоны
Поля комнаты (как в файле): Tag, Exits (буквы выходов СЮЗВ^v), Hint (название), Description,
ChN/ChS/ChW/ChE/ChU/ChD (номер соседней комнаты в этой карте, 0 = нет), X, Y, L (уровень),
AutoMaps.Strings (переход в другую зону: «зона|направление|номер комнаты там|»), Color/BColor.
"""
import json
import os
import struct
import sys

MAPS = os.path.join(os.path.expanduser("~"), "Desktop", "мад", "JMC", "маппер", "MUDMapper2023", "MUDMapper",
                    "Maps", "Сфера Миров")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "world")
ENC = "cp1251"


class Reader:
    def __init__(self, b):
        self.b, self.i = b, 0

    def u8(self):
        v = self.b[self.i]
        self.i += 1
        return v

    def take(self, n):
        v = self.b[self.i:self.i + n]
        self.i += n
        return v

    def sstr(self):
        return self.take(self.u8()).decode(ENC, errors="replace")

    def value(self):
        t = self.u8()
        if t == 0:
            return None
        if t == 1:                       # список
            items = []
            while self.b[self.i] != 0:
                items.append(self.value())
            self.i += 1
            return items
        if t == 2:
            return struct.unpack("<b", self.take(1))[0]
        if t == 3:
            return struct.unpack("<h", self.take(2))[0]
        if t == 4:
            return struct.unpack("<i", self.take(4))[0]
        if t == 5:
            return self.take(10)         # extended
        if t in (6, 7):
            return self.sstr()
        if t == 8:
            return False
        if t == 9:
            return True
        if t == 10:
            n = struct.unpack("<i", self.take(4))[0]
            return self.take(n)
        if t == 11:                      # множество
            items = []
            while True:
                s = self.sstr()
                if not s:
                    break
                items.append(s)
            return items
        if t == 12:
            n = struct.unpack("<i", self.take(4))[0]
            return self.take(n).decode(ENC, errors="replace")
        if t == 13:
            return None
        if t == 18:
            n = struct.unpack("<i", self.take(4))[0]
            return self.take(n * 2).decode("utf-16-le", errors="replace")
        if t == 19:
            return struct.unpack("<q", self.take(8))[0]
        if t == 20:
            n = struct.unpack("<i", self.take(4))[0]
            return self.take(n).decode("utf-8", errors="replace")
        raise ValueError(f"тип {t} на {self.i}")

    def component(self):
        cls = self.sstr()
        name = self.sstr()
        props = {}
        while self.b[self.i] != 0:
            key = self.sstr()
            props[key] = self.value()
        self.i += 1
        while self.b[self.i] != 0:       # дочерние компоненты (у комнат их нет)
            self.component()
        self.i += 1
        return cls, name, props


def read_mm2(path):
    b = open(path, "rb").read()
    rooms, i = [], 0
    while True:
        j = b.find(b"TPF0", i)
        if j < 0:
            break
        r = Reader(b)
        r.i = j + 4
        try:
            cls, name, props = r.component()
        except Exception:
            i = j + 4
            continue
        if cls == "TMudRoom2":
            rooms.append(props)
        i = r.i
    return rooms


def to_json(zone, rooms):
    out = []
    for n, p in enumerate(rooms, 1):          # ChN и т.п. ссылаются на номер комнаты в файле (с 1)
        auto = p.get("AutoMaps.Strings") or []
        out.append({
            "id": n, "name": p.get("Hint", ""), "exits": p.get("Exits", ""),
            "desc": (p.get("Description") or "").strip(),
            "x": p.get("X", 0), "y": p.get("Y", 0), "level": p.get("L", 0),
            "links": {d: p.get("Ch" + d, 0) for d in "NSWEUD" if p.get("Ch" + d, 0)},
            "to_zone": [s for s in auto if s],
            "tag": p.get("Tag", 0),
        })
    return {"zone": zone, "rooms": out}


def main():
    os.makedirs(OUT, exist_ok=True)
    one = sys.argv[1] if len(sys.argv) > 1 else None
    index = {}
    for f in sorted(os.listdir(MAPS)):
        if not f.endswith(".mm2"):
            continue
        zone = f[:-4]
        if one and zone != one:
            continue
        data = to_json(zone, read_mm2(os.path.join(MAPS, f)))
        json.dump(data, open(os.path.join(OUT, zone + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        links = sorted({s.split("|")[0] for r in data["rooms"] for s in r["to_zone"]})
        index[zone] = {"rooms": len(data["rooms"]), "neighbours": links}
        if one:
            for r in data["rooms"]:
                print(r["id"], r["name"], r["exits"], r["links"], (r["x"], r["y"], r["level"]), r["to_zone"])
    if not one:
        json.dump(index, open(os.path.join(OUT, "_index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"зон: {len(index)}, комнат: {sum(v['rooms'] for v in index.values())}")


if __name__ == "__main__":
    main()
