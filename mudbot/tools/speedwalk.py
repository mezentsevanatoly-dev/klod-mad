"""Спидволк между двумя клетками по картам эксплора (ЗОНЫ\\*\\клетки.csv + переходы.csv), через любые зоны.
python -X utf8 tools/speedwalk.py <откуда_vnum> <куда_vnum>      -> печатает путь
Закрытые выходы (запертые двери) в путь не берутся."""
import os, sys, collections, glob

Z = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ЗОНЫ")


def graph():
    G, names = collections.defaultdict(dict), {}
    for f in glob.glob(os.path.join(Z, "*", "клетки.csv")):
        zone = os.path.basename(os.path.dirname(f))
        for l in open(f, encoding="cp1251").read().splitlines()[1:]:
            p = l.split(";")
            closed = p[3] if len(p) > 3 else ""
            names[p[0]] = (zone, p[1])
            for e in p[2].split(","):
                if "=" in e:
                    d, v = e.split("=")
                    if (d + ": заперто") not in closed and (d + ": не прошла") not in closed and (d + ": нет прохода") not in closed:
                        G[p[0]][d] = v
    return G, names


def path(a, b, G):
    q, prev = collections.deque([a]), {a: None}
    while q:
        v = q.popleft()
        if v == b:
            break
        for d, w in G.get(v, {}).items():
            if w not in prev and (w in G or w == b):
                prev[w] = (v, d); q.append(w)
    if b not in prev:
        return None
    out, x = [], b
    while prev[x]:
        out.insert(0, prev[x][1]); x = prev[x][0]
    return out


if __name__ == "__main__":
    G, names = graph()
    p = path(sys.argv[1], sys.argv[2], G)
    if p is None:
        sys.exit("нет пути")
    print(";".join(p))
    print("шагов", len(p), "|", names.get(sys.argv[1]), "->", names.get(sys.argv[2]))
