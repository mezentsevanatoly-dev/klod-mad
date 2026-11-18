import re, sys
sys.path.insert(0, r"C:\Users\User\Desktop\Клод мад\mudbot\tools")
import resolve_entries as RE
from collections import deque
a, b = sys.argv[1], sys.argv[2]
prev, q = {a: None}, deque([a])
while q:
    v = q.popleft()
    for d, t in RE.R.get(v, ("", "", {}))[2].items():
        if t in RE.R and t not in prev:
            prev[t] = (v, d)
            q.append(t)
if b not in prev:
    print("нет пути"); sys.exit()
p, v = [], b
while prev[v]:
    v, d = prev[v]; p.append(d.lower())
p = "".join(p[::-1])
print(re.sub(r"(.)\1+", lambda m: f"{len(m.group(0))}{m.group(1)}", p), len(p))
