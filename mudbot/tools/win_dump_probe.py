import sys, os, ctypes
from ctypes import wintypes
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools"))
import jmc as J
u = J.u32
main = J.find_window()
WM_GETTEXT, WM_GETTEXTLENGTH = 0x000D, 0x000E
res = []
def cb(h, _):
    cls = ctypes.create_unicode_buffer(64); u.GetClassNameW(h, cls, 64)
    n = u.SendMessageW(h, WM_GETTEXTLENGTH, 0, 0)
    res.append((h, cls.value, n))
    return True
u.EnumChildWindows(main, J.WNDENUM(cb), 0)
for h, c, n in res:
    print(h, c, n)

