import sys,os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inc_supervisor as S
r = S.run_zone("из_эрдера", attach=True)
S.say("из_эрдера:", r)

