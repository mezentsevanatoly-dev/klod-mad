"""Чтение карт MUD Mapper (.mm2, Delphi VCL stream TPF0) -> список клеток {props}. Нужен, чтобы сравнить карту мапера с моей из MSDP.
  python tools/mm2.py "<файл.mm2>"     распечатать клетки (имя, координаты, выходы)
"""
import struct
import sys

MAPS = r"C:\Users\User\Desktop\Клод мад\MUDMapper2023\MUDMapper\Maps\Сфера Миров"


def read_value(b, p):
    t = b[p]
    p += 1
    if t == 2:
        return struct.unpack_from("<b", b, p)[0], p + 1
    if t == 3:
        return struct.unpack_from("<h", b, p)[0], p + 2
    if t == 4:
        return struct.unpack_from("<i", b, p)[0], p + 4
    if t == 5:
        return struct.unpack_from("<d", b[:p + 10] + b"\0" * 2, p)[0] if False else None, p + 10
    if t in (6, 7):
        n = b[p]
        return b[p + 1:p + 1 + n].decode("cp1251", "replace"), p + 1 + n
    if t == 8:
        return False, p
    if t == 9:
        return True, p
    if t == 10:
        n = struct.unpack_from("<i", b, p)[0]
        return b[p + 4:p + 4 + n], p + 4 + n
    if t == 11:
        s = []
        while b[p]:
            n = b[p]
            s.append(b[p + 1:p + 1 + n].decode("cp1251", "replace"))
            p += 1 + n
        return s, p + 1
    if t == 12:
        n = struct.unpack_from("<i", b, p)[0]
        return b[p + 4:p + 4 + n].decode("cp1251", "replace"), p + 4 + n
    if t == 18:
        n = struct.unpack_from("<i", b, p)[0]
        return b[p + 4:p + 4 + n * 2].decode("utf-16le", "replace"), p + 4 + n * 2
    if t == 20:
        return struct.unpack_from("<q", b, p)[0], p + 8
    raise ValueError(f"тип {t} на {p}")


def parse(path):
    b = open(path, "rb").read()
    rooms = []
    i = 0
    while True:
        i = b.find(b"TPF0", i)
        if i < 0:
            break
        p = i + 4
        n = b[p]
        cls = b[p + 1:p + 1 + n].decode("cp1251")
        p += 1 + n
        n = b[p]
        name = b[p + 1:p + 1 + n].decode("cp1251")
        p += 1 + n
        props = {"_class": cls, "_name": name}
        try:
            while b[p]:
                n = b[p]
                key = b[p + 1:p + 1 + n].decode("cp1251")
                v, p = read_value(b, p + 1 + n)
                props[key] = v
        except Exception as e:
            props["_err"] = str(e)
        rooms.append(props)
        i = p
    return rooms


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    rs = parse(sys.argv[1] if len(sys.argv) > 1 else MAPS + r"\Мад школа.mm2")
    print(len(rs), "объектов")
    for r in rs[:6]:
        print({k: (v[:50] if isinstance(v, str) else v) for k, v in r.items()})
