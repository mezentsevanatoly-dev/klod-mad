import sys, os
sys.path.insert(0, "tools")
import mapfight as m
h = m.MapHunter(4, 3, m.allowed(["start2"]))
h.skip_below = 0
h.sync_level()
h.last_msdp_from_log()
h.look()
r = h.last_room
print("level", h.level, "room", r.name if r else None, "cur", h.cur["name"], h.cur["vnum"])
print("mobs", r.mobs if r else None)
for l in (r.mobs if r else []):
    print("target:", l, "->", h.target(l))
print("pick:", h.pick(r) if r else None)
print("minimap rows", len(getattr(h, "minimap", []) or []))
