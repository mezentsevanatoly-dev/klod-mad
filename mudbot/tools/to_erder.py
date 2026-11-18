import sys,os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inc_supervisor as S
r = S.run_zone("к_эрдер")
S.say("к_эрдер:", r)
