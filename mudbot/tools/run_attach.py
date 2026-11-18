import sys,os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inc_supervisor as S
z = sys.argv[1]
r = S.run_zone(z, attach=True)
S.say("зона", z, "завершена:", r)
if r != "end": sys.exit(1)
