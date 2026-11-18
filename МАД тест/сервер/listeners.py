# -*- coding: utf-8 -*-
"""Список слушающих TCP-портов с PID через GetExtendedTcpTable.

Get-NetTCPConnection в песочнице возвращает пусто, netstat тоже, поэтому
таблицу соединений читаем напрямую через iphlpapi.
"""
import ctypes
import ctypes.wintypes as wt
import sys

ip = ctypes.WinDLL("iphlpapi", use_last_error=True)

AF_INET = 2
TCP_TABLE_OWNER_PID_LISTENER = 3
ERROR_INSUFFICIENT_BUFFER = 122


class MIB_TCPROW_OWNER_PID(ctypes.Structure):
    _fields_ = [("dwState", wt.DWORD), ("dwLocalAddr", wt.DWORD),
                ("dwLocalPort", wt.DWORD), ("dwRemoteAddr", wt.DWORD),
                ("dwRemotePort", wt.DWORD), ("dwOwningPid", wt.DWORD)]


def listeners():
    size = wt.DWORD(0)
    ip.GetExtendedTcpTable(None, ctypes.byref(size), False, AF_INET,
                           TCP_TABLE_OWNER_PID_LISTENER, 0)
    buf = ctypes.create_string_buffer(size.value)
    r = ip.GetExtendedTcpTable(buf, ctypes.byref(size), False, AF_INET,
                               TCP_TABLE_OWNER_PID_LISTENER, 0)
    if r != 0:
        raise OSError("GetExtendedTcpTable: %d" % r)
    count = wt.DWORD.from_buffer(buf).value
    off = ctypes.sizeof(wt.DWORD)
    row = ctypes.sizeof(MIB_TCPROW_OWNER_PID)
    out = []
    for i in range(count):
        r2 = MIB_TCPROW_OWNER_PID.from_buffer_copy(buf[off + i * row:])
        port = ((r2.dwLocalPort & 0xFF) << 8) | (r2.dwLocalPort >> 8)
        addr = r2.dwLocalAddr.to_bytes(4, "little")
        out.append(("%d.%d.%d.%d" % tuple(addr), port, r2.dwOwningPid))
    return sorted(out, key=lambda x: x[1])


def main():
    rows = listeners()
    want = int(sys.argv[1]) if len(sys.argv) > 1 else None
    if want:
        rows = [r for r in rows if r[2] == want]
        print("PID %d слушает:" % want, rows if rows else "ничего")
    else:
        for addr, port, pid in rows:
            print("%-16s %6d  PID %d" % (addr, port, pid))
    return 0


if __name__ == "__main__":
    sys.exit(main())
